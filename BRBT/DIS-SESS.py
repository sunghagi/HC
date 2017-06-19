#!/NAS/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
from __future__ import division
import os
import sys
import sysv_ipc
import struct
import fcntl
from collections import namedtuple
import lib.vms_hc
import time
'''
namespace MPRM
{

enum {
   EMG_MAX_MP_BOARD = 2,
   EMG_MAX_MP_MPA_PER_BOARD = 8,
   EMG_MAX_MP_MPA = EMG_MAX_MP_BOARD * EMG_MAX_MP_MPA_PER_BOARD,
   EMG_MAX_MP_SESSION_PER_MPA = 1000,
   EMG_MAX_MP_SESSION_PER_BOARD = EMG_MAX_MP_MPA_PER_BOARD * EMG_MAX_MP_SESSION_PER_MPA,
   EMG_MAX_MP_GROUP_PER_BOARD = EMG_MAX_MP_SESSION_PER_BOARD*2,
   EMG_MAX_MP_GROUP_PER_MPA = EMG_MAX_MP_SESSION_PER_MPA*2,
   EMG_MAX_MP_RM_SESSION = EMG_MAX_MP_BOARD * EMG_MAX_MP_SESSION_PER_BOARD,
};

enum e_mpa_status{
// e_mpa_status_notusing = 0x00, 
// e_mpa_status_ok       = 0x01,
   e_mpa_status_ok       = 0x00,
   e_mpa_status_block    = 0x02,
   e_mpa_status_ng       = 0x04,
   e_mpa_status_connect_fail = 0x08,
};

enum e_ses_status{
   e_ses_notuse = 0x00,
   e_ses_idle   = 'I',
   e_ses_start  = 'S',
   e_ses_play   = 'P',
   e_ses_relay  = 'R', // not use
   e_ses_relay_tc = 'T', // not use
   e_ses_record = 'E', // not use
   e_ses_fault = 'F',
};

enum e_ip_mode{
   e_ip_unknown = 0, // unknown
   e_ipv4_only = 1, // IPv4 only
   e_ipv6_only = 2, // IPv6 only
   e_ip_both = 3, // IPv4, v6 both
};

struct st_mprm_shm{
   st_mp_bd stBoard[EMG_MAX_MP_BOARD]; // max 2
   st_mp_mpa stMpa[EMG_MAX_MP_BOARD][EMG_MAX_MP_MPA_PER_BOARD]; // max 80
   unsigned char ucSesStatus[EMG_MAX_MP_BOARD][EMG_MAX_MP_MPA_PER_BOARD][EMG_MAX_MP_SESSION_PER_MPA]; // max 1000
};

#define MPRM_SHM_PATH         "../ipc/shm/mprm_wshm"

typedef struct st_mp_base {
   unsigned int uReason;
   unsigned char ucEnabled;
   unsigned char ucValid;
   unsigned char ucID;
   unsigned char ucStatus; // use not useµî  e_status

typedef struct st_mp_bd : public st_mp_base {
   unsigned char ucNumMPA;
   unsigned char ucReserved[7];

typedef struct st_mp_mpa : public st_mp_base {
   unsigned char ucBoardIndex;
   unsigned char ucIP;
   unsigned char ucReserved[2];
   unsigned short usMaxSession;
   unsigned short usMaxGroup;
'''
 
EMG_MAX_MP_BOARD = 2
EMG_MAX_MP_MPA_PER_BOARD = 8
EMG_MAX_MP_MPA = EMG_MAX_MP_BOARD * EMG_MAX_MP_MPA_PER_BOARD
EMG_MAX_MP_SESSION_PER_MPA = 1000
EMG_MAX_MP_SESSION_PER_BOARD = EMG_MAX_MP_MPA_PER_BOARD * EMG_MAX_MP_SESSION_PER_MPA
EMG_MAX_MP_GROUP_PER_BOARD = EMG_MAX_MP_SESSION_PER_BOARD*2
EMG_MAX_MP_GROUP_PER_MPA = EMG_MAX_MP_SESSION_PER_MPA*2
EMG_MAX_MP_RM_SESSION = EMG_MAX_MP_BOARD * EMG_MAX_MP_SESSION_PER_BOARD

e_mpa_status_ok       = 0x00
e_mpa_status_block    = 0x02
e_mpa_status_ng       = 0x04
e_mpa_status_connect_fail = 0x08

e_ses_notuse = 0x00
e_ses_idle   = 'I'
e_ses_start  = 'S'
e_ses_play   = 'P'
e_ses_relay  = 'R'
e_ses_relay_tc = 'T'
e_ses_record = 'E'
e_ses_fault = 'F'

FTOK_ID = 'x'
BRBT_MPRM_SHM_PATH = '/home/brbt/ipc/shm/mprm_wshm'

ATTR_MP_BASE = 'uReason ucEnabled ucValid ucID ucStatus'
ATTR_MP_BOARD = 'uReason ucEnabled ucValid ucID ucStatus ucNumMPA ucReserved'
ATTR_MP_MPA = 'uReason ucEnabled ucValid ucID ucStatus ucBoardIndex ucIP ucReserved usMaxSession usMaxGroup'
ATTR_SES_STATUS = 'ucSesStatus'

class SharedMemory(object):
	def __init__(self):
		self.error = ""

	def _GetShmId(self):
		key = sysv_ipc.ftok(BRBT_MPRM_SHM_PATH, ord(FTOK_ID), True)
		try:
			Shm = sysv_ipc.SharedMemory(key)
		except Exception as e:
			self.error = e
			raise (NameError,"Shared Memory read failed!!")
		else:
			return Shm

class DisMprmShm(object):
	def __init__(self):
		self.mp_mpa_list = []
		self.ses_status_list = []

	def ReadBytes(self, memory, noBytes):
		data = memory.read(noBytes)
		return data

	def RemoveNul(self, StrWithNul):
		StrWithoutNul = StrWithNul.split('\x00', 1)[0]
		return StrWithoutNul

	def get_dashes(self, perc):
		dashes = "|" * int((float(perc) / 10 * 4))
		empty_dashes = " " * (40 - len(dashes))
		return dashes, empty_dashes

	def read_mprm_shm(self):
		read_result = lib.vms_hc.HcResult()
#		key = sysv_ipc.ftok(BRBT_MPRM_SHM_PATH, ord(FTOK_ID), True)
#		try:
#			Shm = sysv_ipc.SharedMemory(key)
#		except sysv_ipc.ExistentialError:
#			print "  MPA Session is available in brbtsip01/02\n"
#			sys.exit(1)
		mprm_shm = SharedMemory()
		try:
			Shm = mprm_shm._GetShmId()
		except Exception as e:
			read_result.result = "NOK"
			read_result.reason = mprm_shm.error
			return read_result

		HEADER_MP_BASE = 'IBBBB'

		HEADER_ST_MP_BD = HEADER_MP_BASE + 'B7s'
		HEADER_ST_MP_MPA = HEADER_MP_BASE + 'BB2sHH'
		HEADER_SES_STATUS = 's'

		unpack_mp_base_str_size = struct.calcsize(HEADER_MP_BASE)

		unpack_st_mp_bd_shm_str_size = struct.calcsize(HEADER_ST_MP_BD)
		unpack_st_mp_mpa_shm_str_size = struct.calcsize(HEADER_ST_MP_MPA)
		unpack_ses_status = struct.calcsize(HEADER_SES_STATUS) 
		total_unpack_size = unpack_st_mp_bd_shm_str_size*EMG_MAX_MP_BOARD + \
								unpack_st_mp_mpa_shm_str_size*EMG_MAX_MP_BOARD*EMG_MAX_MP_MPA_PER_BOARD + \
								unpack_ses_status*EMG_MAX_MP_BOARD*EMG_MAX_MP_MPA_PER_BOARD*EMG_MAX_MP_SESSION_PER_MPA

		shm_value = self.ReadBytes(Shm, total_unpack_size)

		mp_bd_tpl = namedtuple('mp_bd_tpl', ATTR_MP_BOARD)
		mp_mpa_tpl = namedtuple('mp_mpa_tpl', ATTR_MP_MPA)
		ses_status_tpl = namedtuple('ses_status_tpl', ATTR_SES_STATUS)

		for i in range(EMG_MAX_MP_BOARD):
			offset = unpack_st_mp_bd_shm_str_size*i
			st_mp_bd = mp_bd_tpl._make(struct.unpack_from(HEADER_ST_MP_BD, shm_value, offset))
#			print st_mp_bd

		for i in range(EMG_MAX_MP_BOARD*EMG_MAX_MP_MPA_PER_BOARD):
			offset = unpack_st_mp_bd_shm_str_size*EMG_MAX_MP_BOARD + \
						unpack_st_mp_mpa_shm_str_size*i
			st_mp_mpa = mp_mpa_tpl._make(struct.unpack_from(HEADER_ST_MP_MPA, shm_value, offset))
			self.mp_mpa_list.append(st_mp_mpa)
#		print self.mp_mpa_list

		for i in range(EMG_MAX_MP_BOARD*EMG_MAX_MP_MPA_PER_BOARD*EMG_MAX_MP_SESSION_PER_MPA):
			offset = unpack_st_mp_bd_shm_str_size*EMG_MAX_MP_BOARD + \
						unpack_st_mp_mpa_shm_str_size*EMG_MAX_MP_BOARD*EMG_MAX_MP_MPA_PER_BOARD + \
						unpack_ses_status*i
			ses_status = ses_status_tpl._make(struct.unpack_from(HEADER_SES_STATUS, shm_value, offset))
			self.ses_status_list.append(ses_status)
#		print self.ses_status_list

		return read_result

	def print_mpa_line(self):
		for index in range(EMG_MAX_MP_BOARD*EMG_MAX_MP_MPA_PER_BOARD*EMG_MAX_MP_SESSION_PER_MPA):
			mpa_id, session_id = divmod(index, EMG_MAX_MP_SESSION_PER_MPA)
#			mpa_id = mpa_id % EMG_MAX_MP_MPA_PER_BOARD + 1
			bd_id, mpa_id = divmod(mpa_id, EMG_MAX_MP_MPA_PER_BOARD)
			mpa_id += 1
			bd_id += 1
			ses_status = self.ses_status_list[index]

			if session_id == 0:
				avail_channel_count = 0
				used_channel_count = 0
				notused_channel_count = 0

			if ses_status.ucSesStatus == "\x00":
				notused_channel_count += 1
			else:
				if ses_status.ucSesStatus != e_ses_idle:
					used_channel_count += 1
				avail_channel_count += 1

			if session_id == 999:
				if mpa_id == 1:
					print " RTP%-2s" % bd_id
				try:
					channel_usage_perc = round(used_channel_count/avail_channel_count*100, 2)
#					channel_usage_perc = used_channel_count/avail_channel_count*100
				except ZeroDivisionError:
					channel_usage_perc = 'NOT_USE_MPA'
				else:	
#					print session_id
#					print used_channel_count
#					print avail_channel_count
#					print channel_usage_perc
					mp_mpa_info = self.mp_mpa_list[mpa_id]
					mpa_status = mp_mpa_info.ucStatus
					if mp_mpa_info.ucStatus == 0:
						mpa_status = 'OK'
					elif mp_mpa_info.ucStatus == 2:
						mpa_status = 'BLOCK'
					else:
						mpa_status = 'ETC'
					dashes, empty_dashes = self.get_dashes(channel_usage_perc)
					if mp_mpa_info.ucStatus == 2:
						dashes, empty_dashes = 'X'*40, ""*0
					mpa_line_fmt = "  MPA%-2s [%5s] [%s%s] %5s%% %3s/%s" 
					print mpa_line_fmt % (mpa_id,mpa_status,dashes,empty_dashes,channel_usage_perc,used_channel_count,avail_channel_count)
				continue
#		print ""

def dis_session():
	cmd_result = lib.vms_hc.HcResult()
	column_name = ' BIZ RING SESSION STATUS '
	column_width = 74
	cmd_result_table = lib.vms_hc.HcCmdResultTalbe(column_name, column_width)

	print cmd_result_table.output,

	st_mp = DisMprmShm()
	result = st_mp.read_mprm_shm()

	result_templ = "   %-10s %3s %-30s "
	if result.result == "OK":
		st_mp.print_mpa_line()
	print "=" * column_width + '\n'
	print result_templ % ("RESULT", "=", result.result)
	if result.result == "NOK":
		print result_templ % ("REASON", "=", result.reason)
		print result_templ % ("HELP","=","session status is available in SIP01/02")
	print ""

def main():
	dis_session()

if __name__ == '__main__':
	sys.exit(main())
