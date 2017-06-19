#!/NAS/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import argparse
import ConfigParser
from lib.dis_prcs import *

HCConfigPath='/NAS/HC/config/hc.cfg'

SPS_PNR_CONFIG_PATH='/home/brbt/config/PNR/PNR.cfg'
SPS_CDS_CONFIG_PATH='/home/brbt/config/SPS/CDSIF.cfg'
SPS_SMS_CONFIG_PATH='/home/brbt/config/SPS/SMSIF.cfg'
MPS_PNR_CONFIG_PATH='/home/brbt/config/pnr/PNR.cfg'
PNR_CONFIG_PATH='/home/brbt/config/PNR/PNR.cfg'

class bcolors:
    HEADER = '[1;20m'
    BLUE = '[1;36;40m'
    GREEN = '[1;32;40m'
    WARNING = '[1;5;35;40m'
    RED = '[1;5;31;40m'
    PINK = '[1;35;40m'
    ENDC = '[0m'

def main():
	parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool perform a health check.")
	parser.add_argument('-f', '--full', action='store_true')
	parser.add_argument('-l', '--longcmd', action='store_true')
	args = parser.parse_args()

	HOST_INFO = host_info()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],

	SystemNumber = HOST_INFO.system_name
	HostName = HOST_INFO.hostname
	HostClass = HOST_INFO.hostclass
	HaStatus = HOST_INFO.ha_operating_mode
	HaInstalled = HOST_INFO.ha_installed

#	DayOfTheWeek = datetime.datetime.today().weekday()
	# Mon = 0, Tue = 1, Wed = 2, Thu = 3, Fri = 4, Sat = 5, Sun = 6
#	DayOfTheMonth = datetime.datetime.today().strftime("%d")
	CheckDate = datetime.date.today().strftime("%Y. %m. %d")
	CheckTime = time.strftime("%H:%M", time.localtime())

	logger.info("%s :: System Infomation : %s" , GetCurFunc(), HOST_INFO)

	pnr_process = pnr_process_name(HOST_INFO, PNR_CONFIG_PATH)
	omc_process = omc_process_name(HOST_INFO)
	ha_process = ha_process_name(HOST_INFO)

	if HostClass == 'DB':
		etc_process = ['--','DELLOG','altibase']
	elif HostClass == "SIP" :
		etc_process = ['SyncD','--','DELLOG']
	elif HostClass == "RTP":
		etc_process = ['--','DELLOG']
	else :
		etc_process = []

	if HaInstalled:
		ProcessName = pnr_process + omc_process + etc_process + ha_process
	else:
		ProcessName = pnr_process + omc_process + etc_process

##### Display start 
	PrintEqualLine()
	if HaInstalled :
		head_title_templ0 = bcolors.PINK  + '                        SKT SNSU - BRBT Process Check !!' + bcolors.ENDC
		head_title_templ1 = bcolors.HEADER + ' HOST : %s %s ' + bcolors.RED + '( HA : %s )' + bcolors.ENDC
		print head_title_templ0
		PrintDashLine()
		print head_title_templ1 % (SystemNumber, HostName, HaStatus)
	else:
		head_title_templ0 = bcolors.PINK  + '                        SKT SNSU - BRBT Process Check !!' + bcolors.ENDC
		head_title_templ1 = bcolors.HEADER + ' HOST : %s %s' + bcolors.ENDC
		print head_title_templ0
		PrintDashLine()
		print head_title_templ1 % (SystemNumber, HostName)
	PrintDashLine()
	head_title_templ2 = bcolors.BLUE + ' DATE : %s (%s) %s' + bcolors.ENDC
	weekday = korean_weekday()
	print head_title_templ2 % (CheckDate, weekday, CheckTime)

	if args.longcmd:
		DisplayProcess(ProcessName,args.longcmd)
	else:
		DisplayProcess(ProcessName,args.longcmd)

if __name__ == "__main__":
	sys.exit(main())
