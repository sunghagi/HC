#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import psutil
import datetime
import argparse
import socket
import re
import csv
import ConfigParser
from lib.hclib import *
from StringIO import StringIO
from lib.cmd import *
from lib.dis_extshm import *

HCConfigPath='/nas/HC/config/hc.cfg'

SPS_PNR_CONFIG_PATH='/home/vms/config/DBSVRPM.cfg'
SPS_CDS_CONFIG_PATH='/home/vms/config/CDSIF.cfg'
SPS_SMS_CONFIG_PATH='/home/vms/config/GIPSMS.cfg'
MPS_PNR_CONFIG_PATH='/home/vms/config/pnr/PNR.cfg'
CORE_BIN_PATH='/home/vms/bin'

AppendResultList = []

class VmsHealthCheck(HealthCheckCommand):
	def vms_subscribers(self, HOST_INFO, DSN):
		RESULT = "OK"

		SystemNumber = HOST_INFO.system_name
		HostName = HOST_INFO.hostname
		HostClass = HOST_INFO.hostclass
		HaStatus = HOST_INFO.ha_operating_mode


		if HostClass == "SPS" and HaStatus == 'STANDBY':
			db_query = """
			select count(*) from subscribers
			"""
			db_param = ''

			column_name=['소리샘 총가입자']
			column_width=['25']

			self.print_column_name(column_name,column_width)
			self.odbc_query_execute_fetchone(DSN, db_query, db_param, column_width)

		else:
			print " This system is " + HostClass + " ACTIVE Side"
			print " Subscribers Count is available in STANDBY Side "
			return RESULT

		return RESULT

	def tmemo_subscribers(self, HOST_INFO, DSN):
		RESULT = "OK"

		SystemNumber = HOST_INFO.system_name
		HostName = HOST_INFO.hostname
		HostClass = HOST_INFO.hostclass
		HaStatus = HOST_INFO.ha_operating_mode

		if SystemNumber == "IVMS03" and HostClass == "SPS" and HaStatus == 'STANDBY':
			db_query = """
			select count(*) from subscribers
			"""
			db_param = ''
			column_name=['T메모링 총가입자']
			column_width=['20']

			self.print_column_name(column_name,column_width)
			self.odbc_query_execute_fetchone(DSN, db_query, db_param, column_width)

		else:
			print " This system is " + SystemNumber + ", " + HostClass + " ACTIVE Side "
			print " T-Memoring Subscribers Count is available in iVMS#3 STANDBY Side "
			return RESULT

		return RESULT

	def ConfigFileCheck(self,ConfigPath):
		import os.path
		if not os.path.isfile(ConfigPath):
			print "Filed to open config file !!"
			print "Check Server type !!"
			sys.exit()

#	def CommentRemove(self,ConfigValueWithComment):
#		ConfigValue=ConfigValueWithComment.split('#', 1)[0].strip()
#		return ConfigValue

	def CheckPasswdExpire(self, THRESHOLD):
		RESULT = "OK"

		import getpass
		UserName = getpass.getuser()

		CurrentTime = time.mktime(time.localtime())
		CurrentDate = int(CurrentTime) / 60 / 60 / 24
		logger.info('%s :: CurrentDate : %s', self.GetCurFunc(), CurrentDate)

#		LastPasswdChangeDate = self.os_execute("sudo getent shadow vms|cut -f3 -d:")
		CMD = 'sudo getent shadow ' + UserName + ' |cut -f3 -d:'
		logger.debug('%s :: CMD : %s', self.GetCurFunc(), CMD)
		LastPasswdChangeDate = self.os_execute(CMD)
		logger.debug('%s :: LastPasswdChangeDate : %s', self.GetCurFunc(), LastPasswdChangeDate)
		CMD = 'sudo getent shadow ' + UserName + ' |cut -f5 -d:'
		PassMaxDays = self.os_execute(CMD)
		logger.debug('%s :: PassMaxDays : %s', self.GetCurFunc(), PassMaxDays)

		UserExpireInDate = int(LastPasswdChangeDate) + int(PassMaxDays)
		logger.debug('%s :: UserExpireInDate : %s', self.GetCurFunc(), UserExpireInDate)

		RemainExpireInDate = UserExpireInDate - CurrentDate
		logger.debug('%s :: RemainExpireInDate : %s', self.GetCurFunc(), RemainExpireInDate)

		if RemainExpireInDate < THRESHOLD :
			RESULT = "NOK"
		print "-" * 87
		print " 패스워드 만료 %2s 일 남음 " %  ( RemainExpireInDate )
		print "-" * 87

		return RESULT

	def GetSpsProcessName(self,PnrConfigPath,CdsConfigPath):
		self.ConfigFileCheck(PnrConfigPath)

		PnrConfig = ConfigParser.RawConfigParser()
		PnrConfig.read(PnrConfigPath)
		PnrSectionNameList = PnrConfig.sections()

		CdsConfig = ConfigParser.RawConfigParser()
		CdsConfig.read(CdsConfigPath)
		CdsSectionNameList = CdsConfig.sections()

		AppendProcessNameList = ['HA','MONITOR','OMA','DBSVRPM']
		# DBSVRPM fork process list
		for SectionName in PnrSectionNameList:
			ProcessName=PnrConfig.get(SectionName,'PROCESS_NAME')
			if ProcessName == 'CDSIF':
				AppendProcessNameList.append(ProcessName)
				# CDSIF fork process list
				for SectionName in CdsSectionNameList:
					RunningMode=CdsConfig.get(SectionName,'RUNNING_MODE')
					RunningMode=comment_remove(RunningMode)
					if RunningMode == '1':
						AppendProcessNameList.append(CdsConfig.get(SectionName,'PROCESS_NAME'))
			elif ProcessName == 'vMPSIF':
				# vMPSIF fork process list
				ProcessName = ['vMPSIF_P','vMPSIF_C 1','vMPSIF_C 2']
				AppendProcessNameList = AppendProcessNameList + ProcessName
			else:
				RespawnCondition=PnrConfig.get(SectionName,'RESPAWN_CONDITION')
				RespawnCondition=comment_remove(RespawnCondition)
				if RespawnCondition != '0':
					AppendProcessNameList.append(ProcessName)
		logger.info('%s :: Process List : %s', self.GetCurFunc(), AppendProcessNameList)
		return AppendProcessNameList

	def GetMpsProcessName(self,PnrConfigPath):
		self.ConfigFileCheck(PnrConfigPath)

		PnrConfig = ConfigParser.RawConfigParser()
		PnrConfig.read(PnrConfigPath)
		PnrSectionNameList = PnrConfig.sections()

		AppendProcessNameList = ['OMA']
		# PNR fork process list
		for SectionName in PnrSectionNameList:
			ProcessName=PnrConfig.get(SectionName,'name')
			ProcessName=hc_lib.comment_remove(ProcessName)
			try:
				RunningMode=PnrConfig.get(SectionName,'enable')
			except ConfigParser.NoOptionError:
				RunningMode='1'
				
			RunningMode=hc_lib.comment_remove(RunningMode)
			if RunningMode == '1':
				AppendProcessNameList.append(ProcessName)

		return AppendProcessNameList

	def CheckRemoteConnection(self):
		RESULT = "OK"

		HostClass = self.GetHostClass(LOCAL_IP_ADDR_NIC)
		if HostClass != 'SPS':
			print " This system is " + HostClass
			print " Remote connection Information is available in SPS active side "
			return RESULT
		HaStatus = cmd.ha_status()
		if HaStatus == 'STANDBY':
			print " This system is Standby side "
			print " Remote connection Information is available in SPS active side "
			return RESULT

		GipsmsConfig = ConfigParser.RawConfigParser()
		GipsmsConfig.read(SPS_SMS_CONFIG_PATH)
		VsmssIpAddress=GipsmsConfig.get('COMMON','ADDRESS')
		VsmssIpAddress=hc_lib.comment_remove(VsmssIpAddress)
#		VsmssIpAddress="121.134.202.163"

		print ' VSMSS IP ADDRESS' +' : ' +  VsmssIpAddress
		print ' CDS   IP ADDRESS' +' : ' +  CDS_IP_ADDRESS
		self.PrintDashLine()

		print ' Process           Remote IP       : Port      Status'
		self.PrintDashLine()

		AppendConnectionList = []
		ConnectionsList = psutil.net_connections(kind='inet')
		for Connection in ConnectionsList:
			if Connection.pid and Connection.raddr:
				p = psutil.Process(Connection.pid)
				ProcessName = p.name()
				raddr = "%-15s : %5s" % (Connection.raddr)
				StringConnectionList = " %-15s   %-20s     %-20s" % ( ProcessName, raddr, Connection.status)
				if not Connection.status=="ESTABLISHED":
					if Connection.raddr[0] == VsmssIpAddress or Connection.raddr[0] == CDS_IP_ADDRESS:
						RESULT="NOK"
				AppendConnectionList.append(StringConnectionList)

		for AppendConnection in AppendConnectionList :
			if VsmssIpAddress in AppendConnection:
				print AppendConnection
			elif CDS_IP_ADDRESS in AppendConnection:
				print AppendConnection

		return RESULT

	def CheckAltibaseTableSpace(self,HOST_INFO, DSN):
		RESULT = "OK"

		SystemNumber = HOST_INFO.system_name
		HostName = HOST_INFO.hostname
		HostClass = HOST_INFO.hostclass
		HaStatus = HOST_INFO.ha_operating_mode

		if HostClass == "SPS" and HaStatus == 'STANDBY':
			db_query = """
			SELECT mem_max_db_size/1024/1024 'MAX(M)',
				round(mem_alloc_page_count*32/1024, 2) 'TOTAL(M)',
				trunc((mem_alloc_page_count-mem_free_page_count)*32/1024, 2) 'ALLOC(M)',
				(SELECT round(sum((fixed_used_mem + var_used_mem))/(1024*1024),3) FROM v$memtbl_info) 'USED(M)',
				trunc(((mem_alloc_page_count-mem_free_page_count)*32*1024)/mem_max_db_size, 4)*100 'USAGE(%)'
			FROM v$database ;
			"""
			db_param = ''

			column_name=['MAX(M)','TOTAL(M)','ALLOC(M)','USED(M)','USAGE(%)']
			column_width=['-15','-15','-15','-15','-15']

			self.print_column_name(column_name, column_width)
			self.odbc_query_execute_fetchone(DSN, db_query, db_param, column_width)

			return RESULT
		else:
			print " This system is " + HostClass + " ACTIVE Side"
			print " Altibase Memory Table Space Usage is available in STANDBY Side "
			return RESULT

	def CheckIsupStatPerf(self, HOST_INFO):
		RESULT = "OK"

		SystemNumber = HOST_INFO.system_name
		HostName = HOST_INFO.hostname
		HostClass = HOST_INFO.hostclass

		if HostClass == "OMP" :
			yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
			today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")

			db_query = """
			select DATE_FORMAT(STATTIME, '%Y-%m-%d %H:%i') AS STATTIME,
				SUM(IAM_COUNT) IAM,
				ROUND(SUM(IAM_COUNT)/5/60,1) CPS,
				ROUND(ROUND(SUM(IAM_COUNT)/5/60,1)/30,3)*100 USAGE_RATIO
			from ST_ISUP_5MIN
			where ( STATTIME between ? and ? ) and CALLTYPE=0
			group by STATTIME 
			order by sum(IAM_COUNT) desc limit 0,1;
			"""
			db_param = [yesterday,today]
			self.set_db_label('통계시간','IAM','CPS','사용량(%)')
			IsupStatResult=self.MysqlIupStatPerfQueryExecute(db_query,db_param)
			return IsupStatResult
		else:
			print " This system is " + SystemNumber + ", " + HostClass
			print " ISUP Statistics is available in OMP "
			return RESULT

	def CheckTmemoIsupStatPerf(self, HOST_INFO):
		RESULT = "OK"

		SystemNumber = HOST_INFO.system_name
		HostName = HOST_INFO.hostname
		HostClass = HOST_INFO.hostclass

		if SystemNumber == "IVMS02" or SystemNumber == "IVMS03":
			if HostClass == "OMP" :
#				yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
				yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
#				today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")
				StatStartTime=yesterday + ' ' + '00:00:00'
				StatEndTime=yesterday + ' ' + '23:59:59'

				db_query = """
				select t.STATTIME, t.IAM, t.CPS, t.AVGHT, t.CPS*t.AVGHT/31 AS USED_E1
				from
				(
				select DATE_FORMAT(STATTIME, '%Y-%m-%d %H:%i') AS STATTIME,
					SUM(IAM_COUNT) AS IAM ,
					ROUND(SUM(IAM_COUNT)/5/60,1) AS CPS,
					IF(SUM(IAM_COUNT)=0, 0 , ROUND(SUM(IAM_COUNT*AVGHOLDINGTIME)/SUM(IAM_COUNT),2)) AS AVGHT
				from ST_ISUP_5MIN
				where ( STATTIME between ? and ? ) and CALLTYPE=8
				group by STATTIME 
				order by sum(IAM_COUNT) desc limit 0,1) t;
				"""
#				db_param = [yesterday,today]
				db_param = [StatStartTime,StatEndTime]
				self.set_db_label('통계시간','IAM','CPS','AVGHOLDINGTIME','USED_E1')
				TmemoIsupStatResult=self.MysqlIupStatPerfQueryExecute(db_query,db_param)
#				logger.info('%s :: TmemoIsupStatResult : %s', self.GetCurFunc(),TmemoIsupStatResult)
				return TmemoIsupStatResult
			else:
				print " This system is " + SystemNumber + ", " + HostClass
				print " T-Memo ISUP Statistics is available in iVMS#2,3 OMP "
				return RESULT
		else:
			print " This system is " + SystemNumber + ", " + HostClass
			print " T-Memo ISUP Statistics is available in iVMS#2,3 OMP "
			return RESULT

	def CheckVomoIsupStatPerf(self, HOST_INFO):
		RESULT = "OK"

		SystemNumber = HOST_INFO[0]
		HostName = HOST_INFO[1]
		HostClass = HOST_INFO[2]

		if SystemNumber == "IVMS04":
			if HostClass == "OMP" :
#				yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
				yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
#				today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")
				StatStartTime=yesterday + ' ' + '00:00:00'
				StatEndTime=yesterday + ' ' + '23:59:59'

				db_query = """
				select t.STATTIME, t.IAM, t.CPS, t.AVGHT, t.CPS*t.AVGHT/31 AS USED_E1
				from
				(
				select DATE_FORMAT(STATTIME, '%Y-%m-%d %H:%i') AS STATTIME,
					SUM(IAM_COUNT) AS IAM ,
					ROUND(SUM(IAM_COUNT)/5/60,1) AS CPS,
					IF(SUM(IAM_COUNT)=0, 0 , ROUND(SUM(IAM_COUNT*AVGHOLDINGTIME)/SUM(IAM_COUNT),2)) AS AVGHT
				from ST_ISUP_5MIN
				where ( STATTIME between ? and ? ) and CALLTYPE=9
				group by STATTIME 
				order by sum(IAM_COUNT) desc limit 0,1) t;
				"""
#				db_param = [yesterday,today]
				db_param = [StatStartTime,StatEndTime]
				self.set_db_label('통계시간','IAM','CPS','AVGHOLDINGTIME','USED_E1')
				VomoIsupStatResult=self.MysqlIupStatPerfQueryExecute(db_query,db_param)
#				logger.info('%s :: VomoIsupStatResult : %s', self.GetCurFunc(),VomoIsupStatResult)
				return VomoIsupStatResult
			else:
				print " This system is " + SystemNumber + ", " + HostClass
				print " VoMo ISUP Statistics is available in iVMS#4 OMP "
				return RESULT
		else:
			print " This system is " + SystemNumber + ", " + HostClass
			print " VoMo ISUP Statistics is available in iVMS#4 OMP "
			return RESULT

	def CheckIsupStatRatio(self, HOST_INFO):
		RESULT = "OK"

		SystemNumber = HOST_INFO[0]
		HostName = HOST_INFO[1]
		HostClass = HOST_INFO[2]

		if HostClass == "OMP" :
			yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
			today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")

			db_query = """
			SELECT DATE_FORMAT(STATTIME, '%Y-%m-%d') AS STATTIME,
					SUM(IAM_COUNT) IAM_COUNT, 
					SUM(ACM_COUNT) ACM_COUNT, 
					SUM(ANM_COUNT) ANM_COUNT, 
					SUM(FAIL_COUNT) FAIL_COUNT, 
					ROUND(SUM(ACM_COUNT)/SUM(IAM_COUNT),4)*100 COMPLETE_RATIO,
					ROUND(SUM(ANM_COUNT)/SUM(IAM_COUNT),4)*100 SUCCESS_RATIO
			FROM ST_ISUP_DAY 
			WHERE STATTIME >= ? AND STATTIME < ? AND SERVERID IN(1024,1025) AND CALLTYPE=0
			GROUP BY STATTIME ORDER BY STATTIME ASC;
			"""
			db_param = [yesterday,today]
			self.set_db_label('통계시간','IAM','ACM','ANM','FAIL_COUNT','소통률','성공률')
			IsupStatResult=self.MysqlIupStatRatioQueryExecute(db_query,db_param)
			return IsupStatResult
		else:
			print " This system is " + SystemNumber + ", " + HostClass
			print " ISUP Statistics is available in OMP "
			return RESULT


	def SaveResultCsv(self, CsvFileName):
		try :
			with open(CsvFileName, 'a') as f:
				writer = csv.writer(f)
				writer.writerows(AppendResultList)
		except Exception as e:
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
		logger.info('%s :: AppendResultList : CSV Write success.', self.GetCurFunc())



	def PrintReport(self,CsvFileName,HostName):
		print ""
		print " ****  점검 결과 **** "
		print "=" * 87
		print "           점검항목                           :                 결과  "
		self.PrintDashLine()
		templ = " %2s. %-40s : %20s"
		with open(CsvFileName, 'rt') as f:
			reader = csv.reader(f, delimiter=',')
			for row in reader:
				if row[4] == HostName:
					print templ % (row[0], row[5], row[6])
		self.PrintDashLine()
		print ''
		with open(CsvFileName, 'rt') as f:
			reader = csv.reader(f, delimiter=',')
			for row in reader:
				if row[4] == HostName and row[6] == 'NOK':
					print row[0]+'. '+row[5],
					print row[7]

def main():
	parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool perform a health check.")
	parser.add_argument('-m', '--monthly', action='store_true')
	parser.add_argument('-l', '--show-detail-result', action='store_true')
	args = parser.parse_args()

	cmd = VmsHealthCheck()
	shm = DisExtShm()

	HCConfig = ConfigParser.RawConfigParser()
	HCConfig.read(HCConfigPath)

	index = 1

	HOST_INFO = cmd.host_info()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],

	SystemNumber = HOST_INFO.system_name
	HostName = HOST_INFO.hostname
	HostClass = HOST_INFO.hostclass
	HaStatus = HOST_INFO.ha_operating_mode
	HaInstalled = HOST_INFO.ha_installed


	DayOfTheWeek = datetime.datetime.today().weekday()
	# Mon = 0, Tue = 1, Wed = 2, Thu = 3, Fri = 4, Sat = 5, Sun = 6
	DayOfTheMonth = datetime.datetime.today().strftime("%d")
	CheckDate = datetime.date.today().strftime("%Y-%m-%d")

	CPU_THRESHOLD=HCConfig.getint('threshold', 'cpu')
	MEM_THRESHOLD=HCConfig.getint('threshold', 'mem')
	DISK_THRESHOLD=HCConfig.getint('threshold', 'disk')
	UPTIME_THRESHOLD=HCConfig.getint('threshold', 'uptime')
	PASSWD_THRESHOLD=HCConfig.getint('threshold', 'passwd')
	logger.debug('threshold / cpu : %s',  CPU_THRESHOLD)

	GW_IP=HCConfig.get('ip address', 'gateway')

	logger.info("%s :: System Infomation : %s, %s, %s" , cmd.GetCurFunc(), SystemNumber, HostName, HaStatus)
	logger.debug("%s :: Today is %s days", cmd.GetCurFunc(), DayOfTheMonth)
	if DayOfTheMonth == '15' or args.monthly:
		TodayCheckPeriod = 'MONTHLY'
	elif DayOfTheWeek == 4:
		TodayCheckPeriod = 'WEEKLY'
	else:
		TodayCheckPeriod = 'DAILY'
	logger.info('%s :: Health Check Infomation : %s, %s', cmd.GetCurFunc(), CheckDate, TodayCheckPeriod)

	if HostClass == "SPS" :
		if HaStatus == "ACTIVE" :
			ProcessName=cmd.GetSpsProcessName(SPS_PNR_CONFIG_PATH,SPS_CDS_CONFIG_PATH)
		else:
			ProcessName=['HA','OMA','DBSVRPM','vMPSIF_P','vMPSIF_C 1','vMPSIF_C 2','LOGMGR']
	elif HostClass == "TSPS" :
		ProcessName=['OMA','DBSVRPM','vMPSIF_P','vMPSIF_C 1','vMPSIF_C 2','LOGMGR']
	elif HostClass == "MPS" :
		ProcessName=cmd.GetMpsProcessName(MPS_PNR_CONFIG_PATH)
	elif HostClass == "SS7" :
		ProcessName=['s7pm','lm','mtp3','isup','adax','omsa','trc']
	elif HostClass == "OMP" :
		if HaStatus == "ACTIVE" :
			ProcessName=['PNR','FMS','PMS','CMS','OMG','STMS','TMS','TSMON','MSTAT','NMS','CSMS','OMA']
		else:	
			ProcessName=['PNR','FMS','NMS','CSMS','TASKER','OMA']

	HealthCheckItems = [
	['프로세스 상태 점검', 'cmd.DisplayProcess(ProcessName)','DAILY','ALL'],
	['CPU 사용률 확인', 'cmd.DisplayCpuPercent(CPU_THRESHOLD)','DAILY','ALL'],
	['Memory 사용률 확인','cmd.DisplayMemoryUsage(MEM_THRESHOLD)','DAILY','ALL'],
	['Ping 확인', 'cmd.DisplayPingCheck(GW_IP)','DAILY','ALL'],
	['알람 발생 확인', 'cmd.DisplayAlarm(LOCAL_IP_ADDR_NIC)','DAILY','OMP'],
	['패스워드 만료 확인','cmd.CheckPasswdExpire(PASSWD_THRESHOLD)','DAILY','ALL'],
	['ISUP 통계 확인','cmd.CheckIsupStatPerf()','DAILY','OMP'],
	['T-MEMO ISUP 5분통계 확인','cmd.CheckTmemoIsupStatPerf(HOST_INFO)','DAILY','OMP'],
	['VoMo ISUP 5분통계 확인','cmd.CheckVomoIsupStatPerf(HOST_INFO)','DAILY','OMP'],
	['총 가입자수 확인','cmd.vms_subscribers(HOST_INFO, "DSN=odbc_local")','DAILY','SPS'],
	['T메모링 가입자수 확인','cmd.tmemo_subscribers(HOST_INFO, "DSN=memoring_local")','DAILY','SPS'],
	['알티베이스 메모리 사용률','cmd.CheckAltibaseTableSpace(HOST_INFO, "DSN=memoring_local")','DAILY','SPS'],
#	['외부연동 점검', 'cmd.CheckRemoteConnection()','WEEKLY','ALL'],
	['외부연동 점검', 'shm.ReadExtShm(HaStatus)','WEEKLY','SPS'],
	['NTP 연동 확인', 'cmd.PrintNtpCount()','WEEKLY','ALL'],
	['DISK 사용률 확인','cmd.PrintDiskUsage(DISK_THRESHOLD)','WEEKLY','ALL'],
	['쫌비 프로세스 확인', 'cmd.PrintProcessStatus()','MONTHLY','ALL'],
	['시스템 Uptime 확인', 'cmd.PrintUptime(UPTIME_THRESHOLD)','MONTHLY','ALL'],
	['CORE 파일 생성 확인','cmd.PrintCoreFile(CORE_BIN_PATH)','MONTHLY','ALL'],
	['디스크 이중화 상태 확인', 'cmd.PrintDiskMirror(HostName)','MONTHLY','ALL'],
	]

	TmemoSubsSystem = ['IVMS03']

	for item in HealthCheckItems:
		ItemDesc = item[0]
		Method = item[1]
		CheckPeriod = item[2]
		CheckHost = item[3]

		if TodayCheckPeriod == 'MONTHLY':
			if CheckHost == HostClass or CheckHost == 'ALL':
				RunningFlag = 1
			else:
				RunningFlag = 0
		elif TodayCheckPeriod == 'WEEKLY':
			if CheckPeriod == 'WEEKLY' or CheckPeriod == 'DAILY':
				if CheckHost == HostClass or CheckHost == 'ALL':
					RunningFlag = 1
				else:
					RunningFlag = 0
			else:
				RunningFlag = 0
		elif TodayCheckPeriod == 'DAILY':
			if CheckPeriod == 'DAILY':
				if CheckHost == HostClass or CheckHost == 'ALL':
					RunningFlag = 1
				else:
					RunningFlag = 0
			else:
				RunningFlag = 0

#		OldStdout = sys.stdout
		Out = StringIO()
		sys.stdout = Out

		if RunningFlag :
			cmd.print_label(index, ItemDesc)
			CmdResult = eval(Method)
			logger.info('%s :: %s ItemDesc : %s', cmd.GetCurFunc(), HostName, ItemDesc)
		else:
			continue

#		sys.stdout = OldStdout
		sys.stdout = sys.__stdout__
		ReturnString = Out.getvalue()

		ResultList = [index, CheckDate, TodayCheckPeriod, SystemNumber, HostName, ItemDesc, CmdResult, ReturnString]
		AppendResultList.append(ResultList)
		index += 1

	sys.stdout = sys.__stdout__

	CsvFilePath = '/nas/HC/'
	CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+SystemNumber+'.csv'
	logger.info('%s :: CsvFileName : %s', cmd.GetCurFunc(), CsvFileName)
	cmd.SaveResultCsv(CsvFileName)

	if args.show_detail_result:
		cmd.PrintReport(CsvFileName,HostName)

if __name__ == "__main__":
	sys.exit(main())
