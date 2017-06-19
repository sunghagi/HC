#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import sysv_ipc
import struct
import fcntl
from collections import namedtuple
'''
#define MAX_EXT_SERVER   32  //연동 서버 최대 개수

typedef struct {
   char   szName[32];      // 연동 장비 명
   char   szProcName[32];  // 연동 프로세스 명 (추가됨)
   int    nValid;          // 사용 여부 (0 : 미사용, 1:사용)
   int    nStatus;         // 상태 (0 : Inactive, 1 : Active)
   int    nPort;           // nport (for the future use)
   int    nCnt;            // 세션 개수 (for the future use)
   char   szIp[32];        // ip
   char   szDesc[128];     // (for the future use)
} EXT_SERVER_STATUS, *PEXT_SERVER_STATUS;

typedef struct {
   int                nExtServerCount;      // 외부 연동 상태 정보 개수
   EXT_SERVER_STATUS  ExtServerStatus[MAX_EXT_SERVER];
   char               Reserved[10*1024];    // for the future use 
} EXT_SHM, *PEXT_SHM;

'''
MAX_EXT_SERVER   = 32

FTOK_ID = 'x'
VMS_SHM_FTOK_PATH_EXT = '/home/vms/ipc/shm/ExtTop'

ATTR_EXT_SERVER_STATUS = 'szName szProcName nValid nStatus nPort nCnt szIp szDesc'

class DisExtShm():
	def __init__(self):
		self.result = 'OK'

	def ReadBytes(self, memory, noBytes):
		data = memory.read(noBytes)
		return data

	def RemoveNul(self, StrWithNul):
		StrWithoutNul = StrWithNul.split('\x00', 1)[0]
		return StrWithoutNul

	def ReadExtShm(self, HaStatus):
		if HaStatus == 'STANDBY':
			print " This system is Standby side "
			print " Remote connection Information is available in SPS active side "
			return 'OK'

		HEADER_EXT_SHM = 'i'
		HEADER_EXT_SERVER_STATUS = '32s32siiii32s128s'

		key = sysv_ipc.ftok(VMS_SHM_FTOK_PATH_EXT, ord(FTOK_ID), True)
		Shm = sysv_ipc.SharedMemory(key)

		UnpackExtShmStrSize = struct.calcsize(HEADER_EXT_SHM)
		UnpackExtServerStrSize = struct.calcsize(HEADER_EXT_SERVER_STATUS)
		TotalUnpackSize = UnpackExtShmStrSize + UnpackExtServerStrSize*MAX_EXT_SERVER

		ShmValue = self.ReadBytes(Shm, TotalUnpackSize)

		ExtServerStatusTpl = namedtuple('ExtServerStatusTpl', ATTR_EXT_SERVER_STATUS)
		print '====== External Server List ============================================'
		print ' name         | procname        | ip              | port  | ExtStatus'
		print '------------------------------------------------------------------------'
		offset = 0
		for i in range(MAX_EXT_SERVER):
			offset = UnpackExtShmStrSize + UnpackExtServerStrSize*i
			ExtServerStatus = ExtServerStatusTpl._make(struct.unpack_from(HEADER_EXT_SERVER_STATUS, ShmValue, offset))
			if ExtServerStatus.nValid :
#				print '====' + ExtServerStatus.szName
				if self.RemoveNul(ExtServerStatus.szName) == 'VVMG':
					continue

				if ExtServerStatus.nStatus :
					ExtStatus = 'Connected'
				else :
					ExtStatus = 'DisConnected'
					self.result = 'NOK'

				ShmExtServerStatusDisplayFmt = ' %-12s | %-15s | %-15s | %5s | %12s' % ( self.RemoveNul(ExtServerStatus.szName), self.RemoveNul(ExtServerStatus.szProcName), self.RemoveNul(ExtServerStatus.szIp), ExtServerStatus.nPort, ExtStatus )

				print ShmExtServerStatusDisplayFmt
		print '------------------------------------------------------------------------'

		return self.result

#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize)
#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize+UnpackProcStrSize)
#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize+UnpackProcStrSize+UnpackProcStrSize)

