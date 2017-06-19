#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import psutil
import datetime
import argparse
import socket
import re
from lib.cmd import *
from lib.odbc_conn import odbcConn
#from lib.mysql_odbc import MysqlConn

BONDING_NIC_NAME=['bond0:1','bond1:1']
#LOCAL_IP_ADDR_NIC='bond0'
LOCAL_IP_ADDR_NIC='eth0'

# 'SYSTEM_NUMBER','HOSTNAME','HOSTTYPE','HOSTIP'
HostConf = [
['IVMS01','SPS01', 'SPS', '121.134.202.163'],
['IVMS01','SPS01', 'SPS', '192.168.41.198'],
['IVMS01','SPS02', 'SPS', '192.168.41.199'],
['IVMS01','MPS01', 'MPS', '192.168.41.201'],
['IVMS01','MPS02', 'MPS', '192.168.41.202'],
['IVMS01','OMP', 'OMP', '192.168.41.205'],
['IVMS01','SS701', 'SS7', '192.168.41.208'],
['IVMS01','SS702', 'SS7', '192.168.41.209'],
['IVMS02','SPS01', 'SPS', '192.168.41.228'],
['IVMS02','SPS02', 'SPS', '192.168.41.229'],
['IVMS02','MPS01', 'MPS', '192.168.41.231'],
['IVMS02','MPS02', 'MPS', '192.168.41.232'],
['IVMS02','OMP', 'OMP', '192.168.41.235'],
['IVMS02','SS701', 'SS7', '192.168.41.238'],
['IVMS02','SS702', 'SS7', '192.168.41.239'],
['IVMS03','MPS01', 'MPS', '150.31.13.51'],
['IVMS03','MPS02', 'MPS', '150.31.13.52'],
['IVMS03','OMP', 'OMP', '150.31.13.53'],
['IVMS03','SPS01', 'SPS', '150.31.13.55'],
['IVMS03','SPS02', 'SPS', '150.31.13.56'],
['IVMS03','SS701', 'SS7', '150.31.13.57'],
['IVMS03','SS702', 'SS7', '150.31.13.58'],
['IVMS04','MPS01', 'MPS', '150.31.13.61'],
['IVMS04','MPS02', 'MPS', '150.31.13.62'],
['IVMS04','OMP', 'OMP', '150.31.13.63'],
['IVMS04','SPS01', 'SPS', '150.31.13.65'],
['IVMS04','SPS02', 'SPS', '150.31.13.66'],
['IVMS04','SS701', 'SS7', '150.31.13.67'],
['IVMS04','SS702', 'SS7', '150.31.13.68'],
]

class VmsDisPrefix(HealthCheckCommand):
	def __init__(self):
		pass

	def GetHostClass(self,IP_ADDR):
		LocalIpAddress = self.GetIP(IP_ADDR)
		for host in HostConf:
			if LocalIpAddress in host:
				HostClass = host[2]
		return HostClass	# SPS, MPS, SS7, OMP

	def DisPrefix(self, DSN, args):
		HostClass = self.GetHostClass(LOCAL_IP_ADDR_NIC)

		if HostClass == "SPS" :
			db_query = """
			select netid,prefix,spsnumber 
			from allprefixlist 
			where netid = ? and PREFIX = ? 
			"""
			db_param = args
			column_name=['NETID','PREFIX','VMS NUMBER']
			column_width=['-25','-25','-30']

			self.print_column_name(column_name,column_width)
			self.odbc_query_execute_fetchone(DSN, db_query, db_param, column_width)
		else:
			print " This system is " + HostClass
			print " PFX check is available in SPS "


def main():
	parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
	parser.add_argument('-n', '--netid', action='store', type=int, default='010', help="NETID, ex) 010, 011")
	parser.add_argument('-p', '--prefix', action='store', help="PREFIX, ex) 010-2099-1234, 2099")
	args = parser.parse_args()

	cmd = VmsDisPrefix()

	DbParameter = []
	DbParameter.append(args.netid)
	DbParameter.append(args.prefix)

#	print DbParameter

	cmd.DisPrefix("DSN=odbc_local", DbParameter)

if __name__ == "__main__":
	sys.exit(main())
