#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import sysv_ipc
import struct
import fcntl
import socket
from collections import namedtuple
'''
typedef struct {
190    char   szName[32];      // 연동 장비 명
	191    char   szProcName[32];  // 연동 프로세스 명 (추가됨)
	192    int    nValid;          // 사용 여부 (0 : 미사용, 1:사용)
	193    int    nStatus;         // 상태 (0 : Inactive, 1 : Active)
	194    int    nPort;           // nport (for the future use)
	195    int    nCnt;            // 세션 개수 (for the future use)
	196    char   szIp[32];        // ip
	197    char   szDesc[128];     // (for the future use)
	198 } EXT_SERVER_STATUS, *PEXT_SERVER_STATUS;
	199 
	200 typedef struct {
		201    int                nExtServerCount;      // 외부 연동 상태 정보 개수
		202    EXT_SERVER_STATUS  ExtServerStatus[MAX_EXT_SERVER];
		203    char               Reserved[10*1024];    // for the future use 
		204 } EXT_SHM, *PEXT_SHM;
'''
MAX_EXT_SERVER          = 32

FTOK_ID = 'x'
SHM_PATH = '/home/vms/ipc/shm/ExtTop'

ATTR_EXT_STATUS = 'szName szProcName nValid nStatus nPort nCnt szIp szDesc'

def ReadBytes(memory, noBytes):
	data = memory.read(noBytes)
	return data

def RemoveNul(StrWithNul):
	StrWithoutNul = StrWithNul.split('\x00', 1)[0]
	return StrWithoutNul

def main():
	HEADER_SHM = 'i'
	HEADER_PROCESS_STATUS = '32s32siiii32s128s'

	key = sysv_ipc.ftok(SHM_PATH, ord(FTOK_ID), True)
	Shm = sysv_ipc.SharedMemory(key)

	UnpackShmStrSize = struct.calcsize(HEADER_SHM)
	UnpackProcStrSize = struct.calcsize(HEADER_PROCESS_STATUS)
	TotalUnpackSize = UnpackShmStrSize + UnpackProcStrSize*MAX_EXT_SERVER

	ShmValue = ReadBytes(Shm, TotalUnpackSize)

	ProcessStatusTpl = namedtuple('ProcessStatusTpl', ATTR_EXT_STATUS)
	print '====== Process List ===================================================='
	print ' idx | vld | pid    | ppid   | name             | alias                |'
	print '------------------------------------------------------------------------'
	offset = 0
	for i in range(MAX_EXT_SERVER):
		offset = UnpackShmStrSize + UnpackProcStrSize*i
		ProcessStatus = ProcessStatusTpl._make(struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, offset))
		ShmProcStatusDisplayFmt = ' %s | %s' % ( RemoveNul(ProcessStatus.szName), RemoveNul(ProcessStatus.szProcName))
		print ShmProcStatusDisplayFmt
#		print ProcessStatus
	print '------------------------------------------------------------------------'

#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize)
#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize+UnpackProcStrSize)
#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize+UnpackProcStrSize+UnpackProcStrSize)


if __name__ == "__main__":
	sys.exit(main())
