#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import psutil
import datetime
import time
import struct
import socket
import fcntl
import re
import ConfigParser
import subprocess
import inspect
from log import *
from hostconf import *
from collections import namedtuple

logger = hcLogger('root')


class HealthCheckCommand(object):
	def __init__(self):
		pass

	def GetCurFunc(self):
		return inspect.stack()[1][3]
	
	def PrintDashLine(self):
		print "-" * 80

	def PrintEqualLine(self):
		print "=" * 80

	def GetIP(self,Iface='eth0'):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sockfd = sock.fileno()
		SIOCGIFADDR = 0x8915

		ifreq = struct.pack('16sH14s',Iface, socket.AF_INET, '\x00'*14)
		try:
			res = fcntl.ioctl(sockfd, SIOCGIFADDR, ifreq)
		except:
			return None
		ip = struct.unpack('16sH2x4s8x', res)[2]
		return socket.inet_ntoa(ip)

	def GetNetworkInterface(self):
		output = self.os_execute('/sbin/ifconfig -s')
		NetworkInterfaceNameList = re.findall(r'bond[0-9]\:[0-9]',output)
		return NetworkInterfaceNameList

	def GetSystemManufacturer(self):
		output = self.os_execute('sudo dmidecode -s system-manufacturer | tail -1')
		logger.info('%s :: Type output : %s', self.GetCurFunc(), type(output))
		SystemManufacturer = re.sub('\n','',output)
		return SystemManufacturer


	def IP_address_List(self):
		''' return IP address list
		'''
		retlist = []
		for nic, addrs in psutil.net_if_addrs().items():
			for addr in addrs:
				if addr.family == 2 :
					retlist.append(addr.address)
#					print(" address   : %s" % addr.address)
#           	print(" family :  : %s" % addr.family)
		return retlist

	def ha_status(self):
		ha_status = []

		IPs = self.IP_address_List()
		logger.info('%s :: ip address : %s', self.GetCurFunc(),IPs )

		for IP in IPs:
			for hostlist in HostConf:
				if IP in hostlist:
					host_class = hostlist[2]
					if hostlist[1] == 'VIP':
						st_ha_operating_mode = 'ACTIVE'
						logger.info('%s : This host is Active', self.GetCurFunc())
						break
					else:
						st_ha_operating_mode = 'STANDBY'
		for hostlist in HostConf:
			if host_class in hostlist:
				if hostlist[1] == 'VIP':
					ha_installed = 1
					logger.info('%s : This %s is HA', self.GetCurFunc(), host_class)
					break
				else:
					ha_installed = 0

		ha_status.append(st_ha_operating_mode)
		ha_status.append(ha_installed)

		return ha_status

	def host_info(self):
		ATTR_HOST_INFO = 'system_name hostname hostclass ip_address ha_operating_mode ha_installed'
		host_info_tpl = namedtuple('host_info_tpl', ATTR_HOST_INFO)

		IPs = self.IP_address_List()
		ha_status = self.ha_status()

		for IP in IPs:
			for hostlist in HostConf:
				if IP in hostlist:
					if hostlist[1] == 'VIP':
						continue
					logger.info('%s : hostname is %s', self.GetCurFunc(), hostlist[1])
					HOST_INFO = hostlist + ha_status
					host_info = host_info_tpl._make(HOST_INFO)

					return host_info   # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE,'1'],

		logger.info('%s :: unknown IP address, check HostConf List',self.GetCurFunc())
		sys.exit()

	def GetHostClass(self,IP_ADDR):
		LocalIpAddress = self.GetIP(IP_ADDR)
		logger.debug('%s :: Local IP Address : %s', self.GetCurFunc(), LocalIpAddress)
		for host in HostConf:
			if LocalIpAddress in host:
				HostClass = host[2]
		return HostClass  # SPS, MPS, SS7, OMP

	def GetSystemNumber(self,IP_ADDR):
		LocalIpAddress = self.GetIP(IP_ADDR)
		for host in HostConf:
			if LocalIpAddress in host:
				HostName = host[0]
		return HostName   # iVMS01, iVMS02, iVMS03

	def GetCommandFilename(self):
		file_name,file_ext = os.path.splitext(os.path.basename(sys.argv[0]))
		return file_name

	def os_execute(self,os_command):
		cmd_input = os_command
		pipe_input = subprocess.Popen(cmd_input, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		pipe_input.wait()
		(std_out, std_err) = pipe_input.communicate()
		rc = pipe_input.returncode
		if rc:
			return None
#			logger.info('%s :: std_out : %s', self.GetCurFunc(), std_out)
		else:
			return std_out

	def os_execute2(self, OsCommand):
		StdOut = subprocess.check_output(OsCommand, shell=True)
		logger.info('%s :: std_out : \n%s', self.GetCurFunc(), StdOut)
		return StdOut
	
	def print_label(self,*argv):
		Index = argv[0]
		ItemDesc = argv[1]
		try:
			ItemDesc2 = argv[2]
		except:
			ItemDesc2 = ''
		print ""
		logger.debug('%s :: Index, ItemDesc : %s. %s', self.GetCurFunc(), Index, ItemDesc)
		print "=" * 80
		if ItemDesc2 == '':
			pass
		else:
			print "%s" % ItemDesc2
			print "-" * 80

	def PrintDiskMirror(self,HostName):
		SystemManufacturer = self.GetSystemManufacturer()
		logger.info('%s :: SystemManufacturer : %s', self.GetCurFunc(), SystemManufacturer)

		if SystemManufacturer == 'HP':
			CheckAnotherInstanceOfHpacucli='ps -ef | /bin/grep hpacucli | /bin/grep -v grep'
			CheckAnotherInstanceOfHpacucliResult = self.os_execute(CheckAnotherInstanceOfHpacucli)
			logger.info('%s :: CheckAnotherInstanceOfHpacucliResult : \n%s', self.GetCurFunc(), CheckAnotherInstanceOfHpacucliResult)
			CMD='sudo hpacucli ctrl slot=0 show config | /bin/grep logicaldrive'
			if CheckAnotherInstanceOfHpacucliResult:
				logger.info('%s :: Another instance of hpacucli is running! waiting 3 seconds', self.GetCurFunc())
				time.sleep(3)
				std_out = self.os_execute(CMD)
			else:
				std_out = self.os_execute(CMD)
			logger.info('%s :: hpacucli ctrl slot=0 show config result : \n%s', self.GetCurFunc(), std_out)
			print std_out
			OK = re.findall("OK", std_out)
		else:
			std_out = self.os_execute("sudo mpt-status -p | /bin/grep Found")
			logger.info('%s :: std_out : |%s| ', self.GetCurFunc(), std_out)
			if std_out is None: # SCSI_ID is grater than 15, ATCA 6150
				if HostName == 'TC01':
					SCSI_ID = '20'
				elif HostName == 'SIP02':
					SCSI_ID = '18'
				else:
					SCSI_ID = '0'
			else :
				Buf = re.sub(",.*",'', std_out)
				SCSI_ID = re.sub("\D",'', Buf)

			CMD='sudo mpt-status -i '+SCSI_ID+' | /bin/grep state'
			logger.info('%s :: CMD : %s ', self.GetCurFunc(), CMD)
			std_out = self.os_execute(CMD)
			print std_out
			OK = re.findall("OPTIMAL", std_out)

		if OK:
			DiskMirrorResult = "OK"
		else:
			DiskMirrorResult = "NOK"			

		return DiskMirrorResult

	def PrintNtpCount(self):
		std_out = self.os_execute("/usr/sbin/ntpq -p")
		print std_out
		star = re.findall("\*.*", std_out)
		if star:
			NtpResult = "OK"
		else:
			NtpResult = "NOK"			

		return NtpResult

	def PrintProcessStatus(self):
		RESULT = "OK"
		print 'Process Name     PID   PPID   USER  %MEM    PATH                      CREATE TIME'
		self.PrintDashLine()

		pid_list = psutil.pids()
		                     
		RunningProcessList = []

		for pl in pid_list:
			try:
				p = psutil.Process(pl)
			except:
				pass
			else:
				if p.status() == psutil.STATUS_ZOMBIE:
					if p.name() == "Xsession":
						pass
					else :
						RESULT = "NOK"
						cmdline = '['+p.name()+'] <defunct>'
						create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
						templ = "%-13s %6s %6s   %-5s %-4s %-25s %-s"
						print templ % (p.name(), p.pid, p.ppid(), p.username(), round(p.memory_percent(),1), cmdline, create_time)
		print "-" * 87
		print "=" * 87
		return RESULT

	def DisplayProcess(self,ProcessName):
		RESULT = "OK"
		print 'Process Name    PID  PPID  USER  %MEM  PATH                               CREATE TIME'
		print "-" * 87

		pid_list = psutil.pids()
		                     
		RunningProcessList = []
		AppendRunningProcessList = []

		for pl in pid_list:
			try:
				p = psutil.Process(pl)
			except:
				pass
			else:
				PidProcessName = p.name()
#				if PidProcessName in ProcessName :
				if filter(lambda x:PidProcessName in x, ProcessName)  :
					create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
					if p.cmdline():
						cmdline = " ".join(p.cmdline())
						logger.debug('%s ::  cmdline : %s ',self.GetCurFunc(), cmdline)
					else:
						if p.status() == psutil.STATUS_ZOMBIE:
							cmdline = '['+p.name()+'] <defunct>'
						else:
							cmdline = 'STATUS_UNKNOWN'
					templ = "%-13s %5s %5s  %-5s %-5s %-34s %-s"
					AppendRunningProcessList.append(templ % (p.name(), p.pid, p.ppid(), p.username(), round(p.memory_percent(),1), cmdline, create_time))
		logger.debug('%s :: Running process list : \n%s ', self.GetCurFunc(), '\n'.join(AppendRunningProcessList))
		
		for pl2 in ProcessName:
			for pl3 in AppendRunningProcessList:
#				if filter(lambda x:pl2 in x, pl3):
				if pl2 in pl3:
#				if re.match(r'^'+pl2, pl3):
					process_status = "Running"
					print pl3
					break
			else:
				process_status = "Not Running"
				RESULT = "NOK"
				print '%-60s %-s' % (pl2, process_status)

			if pl2 =='OMA':
				print "-" * 87
		print "=" * 87
		return RESULT

	def DisplayPingCheck(self, GW_IP):
		RESULT = "OK"

		CMD='ping -c 4 -w 4 ' + GW_IP
		std_out = self.os_execute(CMD)
		buf = std_out.split('\n')
		for line in buf:
			if 'packet loss' in line:
				PingResult = line.split(',')
		PacketLoss = re.findall(r'\d', PingResult[2])
		if int(PacketLoss[0]) > 20:
			RESULT='NOK'

		print ' Packet Loss : %2s %% ' % (PacketLoss[0])
		self.PrintDashLine()
		print std_out
		self.PrintDashLine()

		return RESULT

	def DisplayCpuCount(self):
		RESULT = "OK"
		print '  cpu_physical_count     cpu_logical_count '
		self.PrintDashLine()

		cpu_physical_count = psutil.cpu_count(logical=False)
		cpu_logical_count = psutil.cpu_count()

		templ = "%20s %20s"
		print templ % (cpu_physical_count, cpu_logical_count)
		self.PrintDashLine()

		return RESULT

	def DisplayCpuPercent(self, CpuThreshold):
		THRESHOLD = CpuThreshold
		logger.debug('%s :: THRESHOLD : %s', self.GetCurFunc(), THRESHOLD)

		RESULT = "OK"
		templ = " The current system-wide CPU utilization : %s"
		CpuPercent = psutil.cpu_percent(interval=1)
		print templ % (CpuPercent)

		if (CpuPercent > THRESHOLD):
			result = "NOK"

		self.PrintDashLine()

		return RESULT


	def DisplayMemoryUsage(self,threshold):
		THRESHOLD = threshold
		logger.debug('%s :: THRESHOLD : %s', self.GetCurFunc(), THRESHOLD)

		RESULT = "OK"
		print '      Total           Available        Use(%)'
		self.PrintDashLine()

		mem = psutil.virtual_memory()
		TotalMem = mem.total / 1024 / 1024
		FreeMem = mem.available / 1024 / 1024
		PercentMem = mem.percent
		if (PercentMem > THRESHOLD):
			result = "NOK"

		templ = "%10s MB     %10s MB %10s %%"
		print templ % (TotalMem, FreeMem, PercentMem)
		self.PrintDashLine()

		return RESULT

	def DisplayAlarm(self, IP_ADDR_NIC):
		RESULT = "OK"
		HostClass = self.GetHostClass(IP_ADDR_NIC)

		if HostClass == "OMP" :
			db_query = """
			SELECT DATE_FORMAT(EVENTTIME, '%Y-%m-%d %H:%i:%S') AS EVENTTIME,
				SOURCE,
				CAUSE,
				ACKED
			FROM ALARM
			WHERE CLOSED = '0'
			ORDER BY EVENTTIME ASC;
			"""
			db_param = ''
			self.set_db_label('시간','SOURCE','CAUSE','ACKED')
			RESULT = self.MysqlAlarmQueryExecute(db_query,db_param)
		else:
			print " This system is " + HostClass
			print " Alarm check is available in OMP "
		return RESULT

	def PrintUptime(self,THRESHOLD):
		RESULT = "OK"
		print '      Booting 일자          Uptime 일자 '
		self.PrintDashLine()

		floatBootTime = psutil.boot_time()
		BootTime = datetime.datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S") 
		t = time.localtime()
		CurrentTime = time.mktime(t)
		uptime = CurrentTime - floatBootTime
		day = uptime / 60 / 60 / 24
		if (day > THRESHOLD):
			RESULT = "NOK"
		print " %20s        %3s days " %  ( BootTime, int(day) )
		print "-" * 87

		return RESULT

	def PrintDiskUsage(self,threshold):
		THRESHOLD = threshold
		RESULT = "OK"
		print ' Filesystem                Use%      Mounted on '
		self.PrintDashLine()

		list_partitions = psutil.disk_partitions()

		for part in list_partitions:
			fs = part.device
			usage = psutil.disk_usage(part.mountpoint).percent
			if (usage > THRESHOLD):
				RESULT = "NOK"
			mounton = part.mountpoint
			templ = "% -20s %10s      %-20s"
			print templ % (fs, usage, mounton)
		print "-" * 87
		return RESULT

	def PrintCoreFile(self,BinPath):
		RESULT = "OK"

		import fnmatch, os
		Path=BinPath
		files = fnmatch.filter(os.listdir(Path), "core.*")
		if files:
			RESULT = "NOK"
		for CoreFileName in files:
			CMD = '/usr/bin/file '+Path+'/'+CoreFileName
			output = self.os_execute(CMD)
			print output,
		return RESULT

	def set_db_label(self,*args):
		global count_args
		global print_label
		count_args=len(args)
		print_label = args

		logger.info('%s :: count_args : %s', self.GetCurFunc(), count_args)

#		return count_args

	def print_db_label(self,*args):
		print "-" * 20 * count_args
		for label in args:
			print '%-19s' % label,
		print ""
		print "-" * 20 * count_args

	def print_column_name(self, column_name, column_width):
		total_width = sum(int(CW) for CW in column_width)

		print "-" * abs(total_width)
		for name, width in zip(column_name, column_width):
			print '%*s' % (int(width), name),
		print ""
		print "-" * abs(total_width)

	def odbc_query_execute_fetchone(self,DSN,db_query,db_param, column_width):
		from lib.odbc_conn import odbcConn
		db = odbcConn(DSN)
		db._GetConnect()
		logger.info('%s :: Altibase connection success ', self.GetCurFunc())

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)

		total_width = sum(int(CW) for CW in column_width)
		while 1:
			row = db.cursor.fetchone()
			if not row:
				print "=" * abs(total_width)
				break
			for value, width in zip(row, column_width):
				print '%*s' % (int(width), value),
#				print '%-19s' % value,
			print ""


	def AltibasePrefixQueryExecute(self,db_query,db_param):
		from altibase import AltibaseConn

		db = AltibaseConn('DSN=odbc_local')
		db._GetConnect()
		logger.info('%s :: Altibase connection success ', self.GetCurFunc())

		ColumnWidth=['-19','-19','-22']

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.print_db_label(*print_label)
		db.PrintValueWidth(count_args, ColumnWidth)

	def AltibaseMailinfoQueryExecute(self,db_query,db_param):
		from altibase import AltibaseConn

		db = AltibaseConn('DSN=odbc_local')
		db._GetConnect()
		logger.info('%s :: Altibase connection success ', self.GetCurFunc())

		ColumnWidth=['-12','-10','-12','-4','-12','-12']

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.PrintMailinfoLabel(*print_label)
		db.PrintValueWidth(count_args, ColumnWidth)


	def AltibaseQueryExecute(self,db_query,db_param):
		from altibase import AltibaseConn

		db = AltibaseConn('DSN=odbc_local')
		db._GetConnect()
		logger.info('%s :: Altibase connection success ', self.GetCurFunc())

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)

		row = db.cursor.fetchone()
		if not row :
			cmd_exec_result="NOK"
			Result = "NOK"
			print "%-10s = %s" % ('RESULT', cmd_exec_result)
			print "%-10s = %s" % ('REASON', 'There is a no data')
		else:
			cmd_exec_result="OK"
			Result = "OK"
#			print "%-10s = %s" % ('RESULT', cmd_exec_result)

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.print_db_label(*print_label)
		db.print_value(count_args)

		return Result

	def AltibaseTmemoSubsQueryExecute(self,db_query,db_param):
		from altibase import AltibaseConn

		db = AltibaseConn('DSN=memoring_local')
		db._GetConnect()

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)

		row = db.cursor.fetchone()
		if not row :
			cmd_exec_result="NOK"
			Result = "NOK"
			print "%-10s = %s" % ('RESULT', cmd_exec_result)
			print "%-10s = %s" % ('REASON', 'There is a no data')
		else:
			cmd_exec_result="OK"
			Result = "OK"
#			print "%-10s = %s" % ('RESULT', cmd_exec_result)

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.print_db_label(*print_label)
		db.print_value(count_args)

		return Result

	def MysqlIupStatRatioQueryExecute(self,db_query,db_param):
		from mysql_odbc import MysqlConn

		db = MysqlConn()
		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		row = db.cursor.fetchone()
		SuccessRatio=row.SUCCESS_RATIO
		CompleteRatio=row.COMPLETE_RATIO
#		print '소통률 : ', CompleteRatio
#		print '성공률 : ', SuccessRatio
		if CompleteRatio < 95 or SuccessRatio < 70 :
			Result = "NOK"
		elif CompleteRatio >= 95 and SuccessRatio >= 70 :
			Result = "OK"

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.print_db_label(*print_label)
		db.print_value(count_args)
#		self.print_tail()
		return Result

	def MysqlIupStatPerfQueryExecute(self,db_query,db_param):
		from mysql_odbc import MysqlConn

		db = MysqlConn()
#		if db_param == '':
#			db.cursor.execute(db_query)
#		else:
#			db.cursor.execute(db_query, db_param)

#		row = db.cursor.fetchone()
#		IsupUsage=row.USAGE_RATIO
#		IsupCallCount=row.IAM_COUNT
#		CurrentCps = IsupCallCount / 5 / 60
#		logger.info('MysqlIupStatPerfQueryExecute : Current CPS : %s', CPS)
#		logger.info('%s :: Current Usage : %s', self.GetCurFunc(), IsupUsage)
#		MaxCps = 30
#		CurrentUsage = CurrentCps / MaxCps * 100
#		logger.info('MysqlIupStatPerfQueryExecute : Current Usage : %s', CurrentUsage)

#		if IsupUsage > 90 :
#			Result = "NOK"
#		else :
		Result = "OK"

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.print_db_label(*print_label)
		db.print_value(count_args)
#		self.print_tail()
		return Result

	def MysqlAlarmQueryExecute(self,db_query,db_param):
		from mysql_odbc import MysqlConn
		ColumnWidth=['-12','-25','-60','5']
		db = MysqlConn()

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		row = db.cursor.fetchone()
		if row:
			RESULT='NOK'
		else:
			RESULT='OK'

		if db_param == '':
			db.cursor.execute(db_query)
		else:
			db.cursor.execute(db_query, db_param)

		self.PrintAlarmLabel(*print_label)
		db.PrintValueWidth(count_args, ColumnWidth)

		return RESULT

	def PrintAlarmLabel(self, *args):
		ColumnWidth=['-12','-25','-60','5']
		TotalWidth = sum(abs(int(CW)) for CW in ColumnWidth)
		logger.info('%s :: TotalWidth is %s', self.GetCurFunc(), TotalWidth)
		print "-" * ( TotalWidth + len(ColumnWidth))
		for label,width in zip(args, ColumnWidth):
			print '%*s' % (int(width), label),
		print ""
		print "-" * ( TotalWidth + len(ColumnWidth))

	def PrintMailinfoLabel(self, *args):
		ColumnWidth=['-12','-10','-12','-4','-12','-12']
		TotalWidth = sum(abs(int(CW)) for CW in ColumnWidth)
		logger.info('%s :: TotalWidth is %s', self.GetCurFunc(), TotalWidth)
		print "-" * ( TotalWidth + len(ColumnWidth))
		for label,width in zip(args, ColumnWidth):
			print '%*s' % (int(width), label),
		print ""
		print "-" * ( TotalWidth + len(ColumnWidth))
