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
#define MAX_PROCESSES          32
#define MAX_PROCESS_NAME_LEN   16 // including the NULL character!!
#define MAX_NUM_OF_ARGVS       8
#define MAX_ARGV_LEN           16
#define MAX_ALARM_COUNT        64
#define MAX_IVR_BOARDS         8

typedef struct {
   int   size;                           // sizeof(PROCESS_STATUS)
   int   valid;                          // valid flag(0: invalid)
   int  pid;                            // process ID
   int  ppid;                           // parent process ID
   pid_t  szName[MAX_PROCESS_NAME_LEN];   // process name
   pid_t  szAlias[MAX_PROCESS_NAME_LEN];  // process name(alias)
   int   argc;                           // same as argc of main()
   char  argv[MAX_NUM_OF_ARGVS * MAX_ARGV_LEN + MAX_NUM_OF_ARGVS * sizeof(int)];  // same as argv of main()
   int   alarm[MAX_ALARM_COUNT];         // alarm type
} PROCESS_STATUS, *PPROCESS_STATUS;  //DBSVRALARMCOMM//

typedef struct {
	unsigned int   dwMagicCode; // it must be 0xa5a55a5a
	short          major;       // major version number(must be 1)
	short          minor;       // minor version number(must be 0)
	unsigned int   dwSysId;     //system id
	PROCESS_STATUS procs[MAX_PROCESSES];
	CHSTS          ChStatus[MAX_IVR_BOARDS];      //mps ==> 1
	CIRCUIT_STS    CircuitStatus[MAX_IVR_BOARDS]; //mps ==> 3
	int            nMasterSps;                    //mps (W: SPSIF Process added) ==> 4
	char           Reserved[10 * 1024 - sizeof(int)]; ==> 10240 - 4 = 10236
} SHM, *PSHM;  //DBSVRALARMSHM//
'''
MAX_PROCESSES          = 32
MAX_PROCESS_NAME_LEN   = 16
MAX_NUM_OF_ARGVS       = 8
MAX_ARGV_LEN           = 16
MAX_ALARM_COUNT        = 64
MAX_IVR_BOARDS         = 8

FTOK_ID = 'x'
SHM_PATH = '/home/vms/ipc/shm/top'

ATTR_PROCESS_STATUS = 'size valid pid ppid szName szAlias argc argv alarm'

def ReadBytes(memory, noBytes):
	data = memory.read(noBytes)
	return data

def RemoveNul(StrWithNul):
	StrWithoutNul = StrWithNul.split('\x00', 1)[0]
	return StrWithoutNul

def main():
	HEADER_SHM = 'IhhI'
	HEADER_PROCESS_STATUS = 'iiii%ds%dsi%ds%ds' % ( MAX_PROCESS_NAME_LEN, MAX_PROCESS_NAME_LEN, (MAX_NUM_OF_ARGVS*MAX_ARGV_LEN + MAX_NUM_OF_ARGVS*4), 4*MAX_ALARM_COUNT)

	key = sysv_ipc.ftok(SHM_PATH, ord(FTOK_ID), True)
	Shm = sysv_ipc.SharedMemory(key)

	UnpackShmStrSize = struct.calcsize(HEADER_SHM)
	UnpackProcStrSize = struct.calcsize(HEADER_PROCESS_STATUS)
	TotalUnpackSize = UnpackShmStrSize + UnpackProcStrSize*MAX_PROCESSES

	ShmValue = ReadBytes(Shm, TotalUnpackSize)

	ProcessStatusTpl = namedtuple('ProcessStatusTpl', ATTR_PROCESS_STATUS)
	print '====== Process List ===================================================='
	print ' idx | vld | pid    | ppid   | name             | alias                |'
	print '------------------------------------------------------------------------'
	offset = 0
	for i in range(MAX_PROCESSES):
		offset = UnpackShmStrSize + UnpackProcStrSize*i
		ProcessStatus = ProcessStatusTpl._make(struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, offset))
		ShmProcStatusDisplayFmt = ' %3s | %3s | %6s | %6s | %-16s | %-20s |' % ( i, ProcessStatus.valid, ProcessStatus.pid, ProcessStatus.ppid, RemoveNul(ProcessStatus.szName), RemoveNul(ProcessStatus.szAlias) )
		print ShmProcStatusDisplayFmt
	print '------------------------------------------------------------------------'

#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize)
#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize+UnpackProcStrSize)
#	print struct.unpack_from(HEADER_PROCESS_STATUS, ShmValue, UnpackShmStrSize+UnpackProcStrSize+UnpackProcStrSize)


if __name__ == "__main__":
	sys.exit(main())
