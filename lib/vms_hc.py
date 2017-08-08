#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import psutil
import lib.hostconf
import csv
import subprocess
import re
import datetime
import time
import socket
import os.path
import ConfigParser
from lib.log import *

#logger = hcLogger('root')
logger = HcLogger()

class ConfigLoad():
   default_config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), '../config', 'hc.cfg')
   logger.debug('%s :: config path : %s', GetCurFunc(), default_config_path)

   def __init__(self, config_file=default_config_path):
      self.load_config(config_file)
      self.flag = True

   def load_config(self, config_file):
      if os.path.exists(config_file)==False:
#         raise Exception("%s file does not exist.\n" % config_file)
         print "%s file does not exist.\n" % config_file
         sys.exit()

      self.hc_config = ConfigParser.RawConfigParser()
      self.hc_config.read(config_file)

   def get_item_from_section(self, section, item):
      return self.hc_config.get(section, item)

   def getint_item_from_section(self, section, item):
      return self.hc_config.getint(section, item)

   def get_items_from_section(self, section):
      return self.hc_config.items(section)

   def get_sections(self):
      return self.hc_config.sections()

class HcResult(object):
   ''' Health check status

   Attributes:
      result: the health check result as a string
      output: the health check running status as a string
	'''

   def __init__(self):
      self.result = 'OK'
      self.outout = ""
#      self.width = width
#   ResultList = [index, CheckDate, TodayCheckPeriod, SystemNumber, HostName, ItemDesc, CmdResult, ReturnString]

   def _insert_status_endline(self, column_width):
      if self.output.endswith('\n'):
         status_end = '=' * column_width + '\n'
      else:
         status_end = '\n' + '=' * column_width + '\n'
      self.output = string_concate(self.output, status_end)

class OdbcQuery(object):
   yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
   today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")
   stattime = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")

   def __init__(self, item_name, dbname_config):
      self.hc_item_name = item_name
      self.db_column_name = []
      self.db_column_width = []
      self.db_query = ""
      self.db_parameter = ""

      config = ConfigLoad()
      self.omc_type = config.get_item_from_section('omc type', 'type')
      dsn_from_config = config.get_item_from_section('DB DSN', dbname_config)
      self.dsn_string = 'DSN=%s' % (dsn_from_config)
      logger.info('%s :: DB DSN : %s', GetCurFunc(), self.dsn_string)

   def make_output(self):
      hc_result = HcResult()

      column_width = sum(int(CW) for CW in self.db_column_width)
      hc_result_table = HcCmdResultTalbe(self.db_column_name, column_width)

      title_table_row = print_column_name(self.db_column_name, self.db_column_width)

      output_buf = string_concate(hc_result_table.output, title_table_row)

      logger.info('%s :: DB Query : %s', GetCurFunc(), self.db_query)
      output_table_row, result = odbc_query_execute_fetchall(self.dsn_string, self.db_query, self.db_param, self.db_column_width)

      if result.result == "OK":
         hc_result.output = string_concate(output_buf, output_table_row)
         hc_result.result = "OK"
      else:
         logger.info('%s :: result.reason : %s', GetCurFunc(), result.reason)
         hc_result.output = string_concate(output_buf, oneline_print(result.reason))
         hc_result.result = "NOK"
         hc_result.resaon = result.reason

      return hc_result


class HcCmdResultTalbe(object):
   ''' Health check contents

   Attributes:
      column_name: the column name as a string
      column_width: the column width as a string
      output: command execute result  as a string
      status_end: the health check result end as a string
   '''
   def __init__(self, column_name, column_width):
      self.column_name = column_name
      self.column_width = column_width

      output_single_line  = "-" * abs(self.column_width) + '\n'

      output_header = '\n' + output_single_line
      output_header += '  %-*s' % (self.column_width, self.column_name) + '\n'
      output_header += output_single_line

      self.hc_header = output_header
      self.hc_content = ""
      self.output = ""

   def _insert_tail(self):
      if self.output.endswith('\n'):
         status_end = '=' * self.column_width + '\n'
      else:
         status_end = '\n' + '=' * self.column_width + '\n'
      self.output = string_concate(self.output, status_end)

   def _concate(self, content):
      self.hc_content = content
      self.output = string_concate(self.hc_header, self.hc_content)
      self._insert_tail()



class HostInfo(object):
   ''' Health check HA

   Attributes:
      system_name hostname hostclass ip_address ha_operating_mode ha_installed
	'''

   def __init__(self):
      ips_list = ip_address_List()
      logger.debug('%s :: ip address : %s', GetCurFunc(), ips_list )

      for ip in ips_list:
         for hostlist in lib.hostconf.HostConf:
            if ip in hostlist:
               host_class = hostlist[2]
               if hostlist[1] == 'VIP':
                  self.ha_operating_mode = 'ACTIVE'
                  break
               else:
                  self.ha_operating_mode = 'STANDBY'
      for hostlist in lib.hostconf.HostConf:
         if host_class in hostlist:
            if hostlist[1] == 'VIP':
               self.ha_installed = 1
               break
            else:
               self.ha_installed = 0

   def _host_info(self):
      ips_list = ip_address_List()

      for ip in ips_list:
         for hostlist in lib.hostconf.HostConf:
            if ip in hostlist:
               if hostlist[1] == 'VIP':
                  continue
               self.system_name = hostlist[0]
               self.hostname = hostlist[1]
               self.hostclass = hostlist[2]
               self.ip_address = hostlist[3]
               logger.info('%s : hostname is %s', GetCurFunc(), self.hostname)

#      logger.info('%s :: unknown IP address, check HostConf List', GetCurFunc())
#      sys.exit()


def GetCurFunc():
   return inspect.stack()[1][3]

def oneline_print(str):
   return str[:75] + '...'

def string_concate(a, b):
   if not isinstance(b, str):
      b = str(b)

   string_list = []
   string_list.append(a)
   string_list.append(b)

   try:
      return ''.join(string_list)
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e)

def SaveResultCsv(CsvFileName, ResultList):
   try :
      with open(CsvFileName, 'a') as f:
         writer = csv.writer(f)
         writer.writerows(ResultList)
         logger.info('%s :: ResultList : CSV Write success.', GetCurFunc())
   except Exception as e:
      logger.exception('%s :: CSV file handle error : %s', GetCurFunc(), e)

def bytes2human(n): 
   # http://code.activestate.com/recipes/578019 
   # >>> bytes2human(10000) 
   # '9.8K' 
   # >>> bytes2human(100001221) 
   # '95.4M' 
   symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y') 
   prefix = {} 
   for i, s in enumerate(symbols): 
      prefix[s] = 1 << (i + 1) * 10 
   for s in reversed(symbols): 
      if n >= prefix[s]: 
         value = float(n) / prefix[s] 
         return '%.1f%s' % (value, s) 
   return "%sB" % n 

def get_dashes(perc): 
   dashes = "|" * int((float(perc) / 10 * 4)) 
   empty_dashes = " " * (40 - len(dashes)) 
   return dashes, empty_dashes 


def pprint_ntuple(nt): 
   for name in nt._fields: 
      value = getattr(nt, name) 
      if name != 'percent': 
         value = bytes2human(value) 
      print('%-10s : %7s' % (name.capitalize(), value)) 

def single_grep(STR, FILE_PATH):
   for line in open(FILE_PATH):
      if STR in line:
         line_without_crlf = ''.join(line.splitlines())
         return line_without_crlf

def netmask2cidr(NETMASK):
   cidr = sum([bin(int(x)).count("1") for x in NETMASK.split(".")])
   return str(cidr)

def get_alarm_checkday():
   ''' return one month ago and today '''
   today =  datetime.datetime.today()
   today_Ymd = today.strftime("%Y-%m-%d")
   lastMonthday = today - datetime.timedelta(days=30)
   lastMonthday_Ymd = lastMonthday.strftime("%Y-%m-%d")
   two_month_ago_day = today - datetime.timedelta(days=60)
   two_month_ago_day_Ymd = two_month_ago_day.strftime("%Y-%m-%d")
   alarm_checkday = [lastMonthday_Ymd, today_Ymd, two_month_ago_day_Ymd]

   return alarm_checkday

def cpu_usage():
   cpu_usage_result = HcResult()

   config = ConfigLoad()
   CPU_THRESHOLD = config.getint_item_from_section('threshold', 'cpu')

   tot_percs = psutil.cpu_percent(interval=0, percpu=False)
   percs = psutil.cpu_percent(interval=0, percpu=True) 
   buf = ""
   for cpu_num, perc in enumerate(percs): 
      dashes, empty_dashes = get_dashes(perc) 
      templ = " CPU%-2s [%s%s] %5s%%"
      buf += templ % (cpu_num, dashes, empty_dashes, perc) + '\n'

   if (tot_percs > CPU_THRESHOLD):
      cpu_usage_result.result = "NOK"
      cpu_usage_result.reason = "CPU %s usage is %s" % ( cpu_num, tot_percs )

   hc_result_table = HcCmdResultTalbe('CPU 사용률('+str(tot_percs)+'%)',70)
   hc_result_table._concate(buf)
   cpu_usage_result.output = hc_result_table.output
   logger.debug('%s :: hc_result_table.output : %s', 
      GetCurFunc(), hc_result_table.output)

   return cpu_usage_result


def memory_usage():
   memory_usage_result = HcResult()

   config = ConfigLoad()
   MEM_THRESHOLD = config.getint_item_from_section('threshold', 'mem')
   SWAP_THRESHOLD = config.getint_item_from_section('threshold', 'swap_memory')

   mem = psutil.virtual_memory()
   total_mem = bytes2human(mem.total)
   avail_mem = bytes2human(mem.available)
   '''
   percent_mem = mem.percent
   templ = "%10s      %10s   %10s%%"
   buf = '     Total           Available     Use(%)\n'
   buf += "-" * 65 + '\n'
   buf += templ % (total_mem, avail_mem, percent_mem) + '\n'
   '''
   dashes, empty_dashes = get_dashes(mem.percent)
   templ = " Mem   [%s%s] %5s%% %6s / %s \n"
   buf = templ % (  dashes, empty_dashes, 
            mem.percent, 
            str(int(mem.used / 1024 / 1024)) + "M", 
            str(int(mem.total / 1024 / 1024)) + "M" )

   if (mem.percent > MEM_THRESHOLD):
      memory_usage_result.result = "NOK"

   swap = psutil.swap_memory()
   dashes, empty_dashes = get_dashes(swap.percent)
   templ = " Swap  [%s%s] %5s%% %6s / %s"
   buf += templ % ( dashes, empty_dashes, 
            swap.percent, 
            str(int(swap.used / 1024 / 1024)) + "M", 
            str(int(swap.total / 1024 / 1024)) + "M") 

   if (swap.percent > SWAP_THRESHOLD):
      memory_usage_result.result = "NOK"

   hc_result_table = HcCmdResultTalbe('(SWAP)MEMORY 사용률(%)',70)
   hc_result_table._concate(buf)
   memory_usage_result.output = hc_result_table.output

   return memory_usage_result


def disk_usage():
   disk_usage_result = HcResult()

   config = ConfigLoad()
   DISK_THRESHOLD = config.getint_item_from_section('threshold', 'disk')

   list_partitions = psutil.disk_partitions()
   buf = ' Filesystem            Size   Used  Avail   Use%     Mounted on\n'
   templ = "% -20s %6s %6s %6s %6s     %-20s"
   for part in list_partitions:
      fs = part.device
      size = psutil.disk_usage(part.mountpoint).total
      used = psutil.disk_usage(part.mountpoint).used
      avail = psutil.disk_usage(part.mountpoint).free
      usage = psutil.disk_usage(part.mountpoint).percent
      if (usage > DISK_THRESHOLD):
         disk_usage_result.result = "NOK"
      mounton = part.mountpoint
      buf = buf + templ % (fs, bytes2human(size), bytes2human(used), \
                           bytes2human(avail), usage, mounton) + '\n'

   hc_result_table = HcCmdResultTalbe('DISK 사용률 확인',65)
   hc_result_table._concate(buf)
   disk_usage_result.output = hc_result_table.output

   return disk_usage_result


def uptime_status():
   uptime_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('시스템 Uptime 확인',65)

   config = ConfigLoad()
   UPTIME_THRESHOLD = config.getint_item_from_section('threshold', 'uptime')

   float_boot_time = psutil.boot_time()
   BootTime = datetime.datetime.fromtimestamp(float_boot_time).strftime("%Y-%m-%d %H:%M:%S")
   t = time.localtime()
   current_time = time.mktime(t)
   uptime = current_time - float_boot_time
   day = uptime / 60 / 60 / 24

   templ = " %20s        %3s days "

   buf = '      Booting 일자          Uptime 일자\n'
   buf += "-" * hc_result_table.column_width + '\n'
   buf += templ % (BootTime, int(day)) + '\n'

   if (day > UPTIME_THRESHOLD):
      uptime_status_result.result = "NOK"
      uptime_status_result.reason = "uptime이 %s를 초과" % (UPTIME_THRESHOLD) 

   hc_result_table._concate(buf)
   uptime_status_result.output = hc_result_table.output

   return uptime_status_result

def etc_backup():
   backup_result = HcResult()
   hc_result_table = HcCmdResultTalbe('/etc Backup',78)

   config = ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')
   backup_shell=os.path.join(hc_home_path,'etc_backup.sh')

   sudo_backup_shell='sudo ' + backup_shell
   backup_status = os_execute(sudo_backup_shell)

   BackupDate = datetime.date.today().strftime("%Y%m%d")
   BackupHost = socket.gethostname()

   etc_backup_path = config.get_item_from_section('path', 'etc_backup')
   BackupFileName = os.path.join(etc_backup_path, 'etc_bkup_'+BackupHost+'_'+BackupDate+'.tar.gz')
   logger.info('%s :: BackupFileName : %s', GetCurFunc(), BackupFileName)

   CMD = '/usr/bin/file '+BackupFileName
   backup_status = os_execute(CMD)

   if os.path.exists(BackupFileName):
      backup_result.result = "OK"
   else:
      backup_result.result = "NOK"

   hc_result_table._concate(backup_status)
   backup_result.output = hc_result_table.output

   return backup_result

def sipa_fdump_status():
   sipa_fdump_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('sipa full dump 설정  확인',78)

   config = ConfigLoad()
   sipa_trace_path = config.get_item_from_section('main', 'sipa_trace')

   sipa_config = ConfigParser.RawConfigParser()
   sipa_config.read(sipa_trace_path)
   dump = sipa_config.getint('MAIN','dump')
   full_dump = sipa_config.getint('MAIN','full_dump')

   sipa_fdump_status_output = "    dump : %s , full_dump : %s" % ( dump, full_dump )
   logger.info('%s :: sipa_fdump_status_output : %s', GetCurFunc(), sipa_fdump_status_output)

   if dump:
      if full_dump:
         sipa_fdump_status_result.result = "NOK"
   else:
      sipa_fdump_status_result.result = "OK"

   hc_result_table._concate(sipa_fdump_status_output)
   sipa_fdump_status_result.output = hc_result_table.output

   return sipa_fdump_status_result

def process_display():
   process_display_result = HcResult()
   hc_result_table = HcCmdResultTalbe('PROCESS 확인',78)

   config = ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')

   process_display_command = os.path.join(hc_home_path,'DIS-PRCS.py')
   process_display_output = os_execute(process_display_command)

   hc_result_table._concate(process_display_output)
   process_display_result.output = hc_result_table.output

   return process_display_result

def ntp_status():
   ntp_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('NTP 연동 확인 : ntpq -p',78)

   ntp_status = os_execute("/usr/sbin/ntpq -p")

   sync_char = re.findall("\*.*", ntp_status)

   if sync_char:
      ntp_status_result.result = "OK"
   else:
      ntp_status_result.result = "NOK"

   hc_result_table._concate(ntp_status)
   ntp_status_result.output = hc_result_table.output

   return ntp_status_result


def process_status():
   process_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('좀비프로세스 확인',78)

   buf = 'Process Name     PID   PPID   USER  %MEM    PATH                      CREATE TIME\n'
   buf += "-" * hc_result_table.column_width + '\n'

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
               process_status_result.result = "NOK"
               cmdline = '['+p.name()+'] <defunct>'
               create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
               templ = "%-13s %6s %6s   %-5s %-4s %-25s %-s\n"
               buf += templ % (p.name(), p.pid, p.ppid(), p.username(), round(p.memory_percent(),1), cmdline, create_time)

   hc_result_table._concate(buf)
   process_status_result.output = hc_result_table.output

   return process_status_result

def corefile_status():
   corefile_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('CORE 파일 생성 확인 : file CORE_FILE',78)

   config = ConfigLoad()
   core_file_path = config.get_item_from_section('path', 'core')
   logger.info('%s :: core_file_path : %s', GetCurFunc(), core_file_path)

   import fnmatch, os
   try:
      files = fnmatch.filter(os.listdir(core_file_path), "core.*")
   except Exception as e:
      logger.exception('%s :: %s', GetCurFunc(), e)
      corefile_status_result.reason = e
      corefile_status_result.result = "NOK"
      buf = e
   else:
      buf = ''
      for CoreFileName in files:
         # OMA는 root 권한 필요
         CMD = 'sudo /usr/bin/file '+core_file_path+'/'+CoreFileName
         output = os_execute(CMD)
         buf += output
      if files:
         corefile_status_result.result = "NOK"

   hc_result_table._concate(buf)
   corefile_status_result.output = hc_result_table.output

   return corefile_status_result

def disk_mirror_status():
   disk_mirror_status_result = HcResult()
   SYS_MANUF = GetSystemManufacturer()
   logger.info('%s :: SYS_MANUF : %s', GetCurFunc(), SYS_MANUF)

   if SYS_MANUF == 'HP':
      if os.path.exists("/usr/sbin/hpssacli"):
         hp_storage_admin_tool = "hpssacli"
      else :
         hp_storage_admin_tool = "hpacucli"
      os_command = hp_storage_admin_tool + " ctrl slot=0 show config"
   elif SYS_MANUF == 'Advantech':
      os_command = "SKIP (Console Cable연결 필요)"
   elif SYS_MANUF == 'Red Hat':
      os_command = "SKIP (KVM Host)"
   else :
      os_command = 'mpt-status -i SCSI_ID'

   hc_result_table = HcCmdResultTalbe('디스크 이중화 상태 확인 : '+os_command, 78)

   if SYS_MANUF == 'HP':
      CheckAnotherInstanceOfHpacucli='ps -ef | /bin/grep ' + hp_storage_admin_tool + ' | /bin/grep -v grep'
      CheckAnotherInstanceOfHpacucliResult = os_execute(CheckAnotherInstanceOfHpacucli)
      logger.info('%s :: CheckAnotherInstanceOfHpacucliResult : \n%s', GetCurFunc(), CheckAnotherInstanceOfHpacucliResult)
      CMD='sudo /usr/sbin/'+ hp_storage_admin_tool +' ctrl slot=0 show config | /bin/grep logicaldrive'
      if CheckAnotherInstanceOfHpacucliResult:
         logger.info('%s :: Another instance of %s is running! waiting 3 seconds', GetCurFunc(), hp_storage_admin_tool)
         time.sleep(3)
         std_out = os_execute(CMD)
      else:
         std_out = os_execute(CMD)
      logger.info('%s :: %s ctrl slot=0 show config result : \n%s', GetCurFunc(), hp_storage_admin_tool, std_out)

      OK = re.findall("OK", std_out)
   elif SYS_MANUF == 'Advantech':
      std_out = "SKIP"
      OK = True
   elif SYS_MANUF == 'Red Hat':
      std_out = "SKIP"
      OK = True
   else:
      std_out = os_execute("sudo mpt-status -p | /bin/grep Found")
      logger.info('%s :: std_out : |%s| ', GetCurFunc(), std_out)
      Buf = re.sub(",.*",'', std_out)
      SCSI_ID = re.sub("\D",'', Buf)

      CMD='sudo mpt-status -i '+SCSI_ID+' | /bin/grep state'
      logger.info('%s :: CMD : %s ', GetCurFunc(), CMD)
      std_out = os_execute(CMD)
      OK = re.findall("OPTIMAL", std_out)

   if OK:
      disk_mirror_status_result.result = "OK"
   else:
      disk_mirror_status_result.result = "NOK"

   hc_result_table._concate(std_out)
   disk_mirror_status_result.output = hc_result_table.output

   return disk_mirror_status_result


def vms_subscribers():
   column_name = '소리샘 총가입자'

   db_column_name = ['SUBSCRIBERS']
   db_column_width = ['60']
   column_width = sum(int(CW) for CW in db_column_width)
   hc_result_table = HcCmdResultTalbe(column_name, column_width)

   vms_subscribers_result = HcResult()

   config = ConfigLoad()
   dsn_from_config = config.get_item_from_section('DB DSN', 'altibase')
   dsn_string = 'DSN=%s' % ( dsn_from_config)
   logger.info('%s :: DB DSN : %s', GetCurFunc(), dsn_string)

   db_query = """
   select count(*) from subscribers
   """
   db_param = ''
   vms_subscribers, result = odbc_query_execute_fetchone(dsn_string, db_query, db_param, hc_result_table.column_width)

   db_column_name = lib.vms_hc.print_column_name(db_column_name, db_column_width)
   output_buf = string_concate(hc_result_table.output, db_column_name)

   vms_subscribers_result.output = string_concate(output_buf, vms_subscribers)

   if result.result == "OK":
      vms_subscribers_result.output = string_concate(output_buf, vms_subscribers)
      vms_subscribers_result.result = "OK"

   result_templ = "   %-10s %3s %-30s "
   if result.result == "NOK":
      vms_subscribers_result.output = string_concate(output_buf, result.reason)
      vms_subscribers_result.result = "NOK"
#      print result_templ % ("REASON", "=", result.reason)
#      print result_templ % ("HELP","=","Subscribers count is available in SPS01/02")

   return vms_subscribers_result

def tars_subscribers():
   column_name = 'T-ARS 총가입자'

   db_column_name = ['SUBSCRIBERS']
   db_column_width = ['78']
   column_width = sum(int(CW) for CW in db_column_width)
   hc_result_table = HcCmdResultTalbe(column_name, column_width)

   vms_subscribers_result = HcResult()

   config = ConfigLoad()
   dsn_from_config = config.get_item_from_section('DB DSN', 'altibase')
   dsn_string = 'DSN=%s' % ( dsn_from_config)
   logger.info('%s :: DB DSN : %s', GetCurFunc(), dsn_string)

   db_query = """
   select count(*) from subscribers where usertype=?
   """
   db_param = 1
   ac_subscribers, result = odbc_query_execute_fetchone(dsn_string, db_query, db_param, hc_result_table.column_width)
   ac_subscribers_cnt = ac_subscribers.split("\n")[0].strip(" ")
   db_param = 2
   cf_subscribers, result = odbc_query_execute_fetchone(dsn_string, db_query, db_param, hc_result_table.column_width)
   cf_subscribers_cnt = cf_subscribers.split("\n")[0].strip(" ")
   total_cnt = int(ac_subscribers_cnt) + int(cf_subscribers_cnt)

#   db_column_name = lib.vms_hc.print_column_name(db_column_name, db_column_width)
   db_column_name = hc_result_table.hc_header
   output_buf = string_concate(hc_result_table.output, db_column_name)

#   tars_subscribers = "자동연결 : %10s 명 \n착신전환 : %10s 명\n합    계 : %10s" % (ac_subscribers.split("\n")[0].strip(" "), cf_subscribers.split("\n")[0].strip(" "), )
   tars_subscribers = "자동연결 : %10s 명 \n착신전환 : %10s 명\n합    계 : %10s 명\n" % (ac_subscribers_cnt, cf_subscribers_cnt, total_cnt )
   vms_subscribers_result.output = string_concate(output_buf, tars_subscribers)

   if result.result == "OK":
#      vms_subscribers_result.output = string_concate(output_buf, vms_subscribers)
      vms_subscribers_result.result = "OK"

   result_templ = "   %-10s %3s %-30s "
   if result.result == "NOK":
      vms_subscribers_result.output = string_concate(output_buf, result.reason)
      vms_subscribers_result.result = "NOK"
#      print result_templ % ("REASON", "=", result.reason)
#      print result_templ % ("HELP","=","Subscribers count is available in SPS01/02")

   return vms_subscribers_result

def isup_stat():
   isup_stat_omp = OdbcQuery('ISUP 통계 확인','mysql')
   isup_stat_omp.db_column_name=['통계시간','IAM','CPS','사용량(%)']
   isup_stat_omp.db_column_width=['-20','-20','-20', '-20']
   if isup_stat_omp.omc_type == '1' or isup_stat_omp.omc_type == '2' :
      isup_stat_omp.db_query = """
      select DATE_FORMAT(collectTime, '%Y-%m-%d %H:%i') AS collectTime,
      SUM(iam_rx) IAM,
      ROUND(SUM(iam_rx)/5/60,1) CPS,
      ROUND(ROUND(SUM(iam_rx)/5/60,1)/250,3)*100 USAGE_RATIO
      from tmr_st_isup_min
      where ( collectTime between ? and ? )
      group by collectTime
      order by sum(iam_rx) desc limit 0,1;
      """
   elif isup_stat_omp.omc_type == '3' :
      isup_stat_omp.db_query = """
      select DATE_FORMAT(STATTIME, '%Y-%m-%d %H:%i') AS STATTIME,
      SUM(IAM_COUNT) IAM,
      ROUND(SUM(IAM_COUNT)/5/60,1) CPS,
      ROUND(ROUND(SUM(IAM_COUNT)/5/60,1)/30,3)*100 USAGE_RATIO
      from ST_ISUP_5MIN
      where ( STATTIME between ? and ? ) and CALLTYPE=0
      group by STATTIME
      order by sum(IAM_COUNT) desc limit 0,1;
      """
   isup_stat_omp.db_param = [isup_stat_omp.yesterday,isup_stat_omp.today]
   isup_stat_result = isup_stat_omp.make_output()
   return isup_stat_result

def scp_stat():
   scp_stat_omp = OdbcQuery('SCP 통계 확인','mysql')
   scp_stat_omp.db_column_name=['통계시간','TotalCount','CPS','사용량(%)/250 CPS']
   scp_stat_omp.db_column_width=['-20','-20','-20', '-20']
   scp_stat_omp.db_query = """
   select DATE_FORMAT(collectTime, '%Y-%m-%d %H:%i') AS collectTime,
   SUM(totalCount) totalCount,
   ROUND(SUM(totalCount)/5/60,1) CPS,
   ROUND(ROUND(SUM(totalCount)/5/60,1)/250,3)*100 USAGE_RATIO
   from tmr_st_scp_min
   where ( collectTime between ? and ? )
   group by collectTime
   order by sum(totalCount) desc limit 0,1;
   """
   scp_stat_omp.db_param = [scp_stat_omp.yesterday,scp_stat_omp.today]
   scp_stat_result = scp_stat_omp.make_output()
   return scp_stat_result

def cpu_stat():
   cpu_stat_omp = OdbcQuery('CPU 통계확인','mysql')
   cpu_stat_omp.db_column_name = ['시스템','Peak 값','평균값']
   cpu_stat_omp.db_column_width = ['20','10','10']

   if cpu_stat_omp.omc_type == '1' or cpu_stat_omp.omc_type == '2' :
      cpu_stat_omp.db_query = """
      SELECT B.SYSNAME, max(A.usages) as max_usages , round(avg(A.usages),1) as avg_usages
      FROM SAM_ST_CPU_HOUR A INNER JOIN SAM_SYSTEM B
      ON A.SYSTEMID = B.SYSTEMID
      group by sysname;
      """
      cpu_stat_omp.db_param = ''
   elif cpu_stat_omp.omc_type == '3' :
      cpu_stat_omp.db_query = """
      SELECT B.SERVERNAME, maxcpu, cpu
      FROM ST_SYS_MON A INNER JOIN SERVER B
      ON A.SERVERID = B.SERVERID
      WHERE A.STATTIME  BETWEEN ? AND ?;
      """
      checkday = get_alarm_checkday()
      alarm_start_time=checkday[2] + ' ' + '00:00:00'
      alarm_end_time=checkday[1] + ' ' + '23:59:59'
      cpu_stat_omp.db_param = [alarm_start_time, alarm_end_time]

   cpu_stat_result = cpu_stat_omp.make_output()
   return cpu_stat_result


def tars_sip_stat():
   sip_stat_omp = OdbcQuery('SIP 통계 확인','mysql')
   sip_stat_omp.db_column_name=['통계시간','TOTAL','SUCCESS','FAIL','HT']
   sip_stat_omp.db_column_width=['-25','-15','-15', '-15','-15']
   sip_stat_omp.db_query = """
   SELECT collectTime, SUM(totalCount) totalCount,
   SUM(IF(endCode IN (0, 403), totalCount, 0)) successCount,
   SUM(IF(endCode NOT IN (0, 403), totalCount, 0)) failCount,
   ROUND(SUM(holdingTime * totalCount)/SUM(totalCount)) holdingTime
   FROM SAM_ST_SIPRM_HOUR
   WHERE collectTime = ?
   GROUP BY collectTime
   """
   sip_stat_omp.db_param = [sip_stat_omp.stattime]
   sip_stat_result = sip_stat_omp.make_output()
   return sip_stat_result

def dis_alarm():
   dis_alarm_omp = OdbcQuery('MONTHLY ALARM INFORMATION','mysql')
   dis_alarm_omp.db_column_name=['FIRST_TIME','SOURCE','MESSAGE']
   dis_alarm_omp.db_column_width=['-21','-25','-40']

   checkday = get_alarm_checkday()
   alarm_start_time=checkday[0] + ' ' + '00:00:00'
   alarm_end_time=checkday[1] + ' ' + '23:59:59'

#   print "알람 조회 기간 : %s ~ %s " % ( alarm_start_time, alarm_end_time )
#   print "작업시간(02:00 ~ 05:59) 알람은 제외"
   if dis_alarm_omp.omc_type == '1' or dis_alarm_omp.omc_type == '2' :
      dis_alarm_omp.db_query = """
      select A.firstTime,
   #  B.sysname,
      A.source,
      A.alarmMessage
      from SAM_ALARM A inner join SAM_SYSTEM B
      on A.systemid = B.systemid
      where A.firstTime between ? and ?
      and A.firstTime not regexp '.*\ 0[2-5].*'
      and A.severity = 1;
      """
   elif dis_alarm_omp.omc_type == '3':
      dis_alarm_omp.db_query = """
      SELECT DATE_FORMAT(EVENTTIME, '%Y-%m-%d %H:%i:%S') AS EVENTTIME,
         SOURCE,
         CAUSE
      FROM ALARM
      WHERE EVENTTIME BETWEEN ? AND ?
      AND EVENTTIME NOT regexp '.*\ 0[1-5].*'
      AND SEVERITY = 2
      AND ALARMCODE != "A0037"  # AvrHoldingtime is too low
      AND ALARMCODE != "A0054"  # E1 Sync Error
      AND ALARMCODE != "A0017"  # sync error
      AND ALARMCODE != "A9203"  # ARS User Cert ERROR[
      ORDER BY EVENTTIME ASC;
      """
   dis_alarm_omp.db_param = [alarm_start_time, alarm_end_time]
   dis_alarm_result = dis_alarm_omp.make_output()
   return dis_alarm_result


def sip_stat():
   column_name = 'SIP 통계 확인'

   db_column_name=['통계시간','TotalCount','CPS','사용량(%)/300 CPS']
   db_column_width=['-20','-20','-20', '-20']
   column_width = sum(int(CW) for CW in db_column_width)
   vms_hc_cmd_result_table = HcCmdResultTalbe(column_name, column_width)

   sip_stat_result = HcResult()

   config = ConfigLoad()
   dsn_from_config = config.get_item_from_section('DB DSN', 'mysql')
   dsn_string = 'DSN=%s' % ( dsn_from_config)
   logger.info('%s :: DB DSN : %s', GetCurFunc(), dsn_string)

   yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d %H:%M:%S")
   today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")

   db_query = """
   select DATE_FORMAT(collectTime, '%Y-%m-%d %H:%i') AS collectTime,
   SUM(invite) invite,
   ROUND(SUM(invite)/5/60,1) CPS,
   ROUND(ROUND(SUM(invite)/5/60,1)/300,3)*100 USAGE_RATIO
   from sam_st_sipmsg_min
   where ( collectTime between ? and ? )
   group by collectTime
   order by sum(invite) desc limit 0,1;
   """
   db_param = [yesterday,today]

   db_column_name = print_column_name(db_column_name, db_column_width)
   output_buf = string_concate(vms_hc_cmd_result_table.output, db_column_name)

   stat, result = odbc_query_execute_fetchall(dsn_string, db_query, db_param, db_column_width)
   sip_stat_result.output = string_concate(output_buf, stat)

   if stat:
      sip_stat_result.result = "OK"
   else:
      sip_stat_result.result = "NOK"

   return sip_stat_result

def altibase_tablespace():
   column_name = '알티베이스 메모리 사용률'
   column_width = 78
   hc_result_table = HcCmdResultTalbe(column_name, column_width)
   altibase_tablespace_result = HcResult()

   config = ConfigLoad()
   dsn_from_config = config.get_item_from_section('DB DSN', 'altibase')
   dsn_string = 'DSN=%s' % ( dsn_from_config)
   logger.info('%s :: DB DSN : %s', GetCurFunc(), dsn_string)

   db_column_name=['MAX(M)','TOTAL(M)','ALLOC(M)','USED(M)','USAGE(%)']
   db_column_width=['-17','-17','-17','-17','-17']

   db_query = """
   SELECT mem_max_db_size/1024/1024 'MAX(M)',
      round(mem_alloc_page_count*32/1024, 2) 'TOTAL(M)',
      trunc((mem_alloc_page_count-mem_free_page_count)*32/1024, 2) 'ALLOC(M)',
      (SELECT round(sum((fixed_used_mem + var_used_mem))/(1024*1024),3) FROM v$memtbl_info) 'USED(M)',
      trunc(((mem_alloc_page_count-mem_free_page_count)*32*1024)/mem_max_db_size, 4)*100 'USAGE(%)'
   FROM v$database ;
   """
   db_param = ''

   db_column_name = print_column_name(db_column_name, db_column_width)
#   db_column_name = hc_result_table.hc_header
   output_buf = string_concate(hc_result_table.output, hc_result_table.hc_header)
   output_buf = string_concate(output_buf, db_column_name)

   tablespace, result = odbc_query_execute_fetchone(dsn_string, db_query, db_param, db_column_width)
   altibase_tablespace_result.output = string_concate(output_buf, tablespace)

   if result.result == "OK":
#      vms_subscribers_result.output = string_concate(output_buf, vms_subscribers)
      altibase_tablespace_result.result = "OK"

   result_templ = "   %-10s %3s %-30s "
   if result.result == "NOK":
      altibase_tablespace_result.output = string_concate(output_buf, result.reason)
      altibase_tablespace_result.result = "NOK"
#      print result_templ % ("REASON", "=", result.reason)
#      print result_templ % ("HELP","=","Subscribers count is available in SPS01/02")


   return altibase_tablespace_result

def print_column_name(column_name, column_width):
   total_width = sum(int(CW) for CW in column_width)
   
   buf = "\n"
   buf += "-" * abs(total_width) + '\n'
   for name, width in zip(column_name, column_width):
      buf += '%*s' % (int(width), name)
   buf += "\n"
   buf += "-" * abs(total_width) + '\n'

   return buf


def odbc_query_execute_fetchone(DSN,db_query,db_param, column_width):
   from lib.odbc_conn import odbcConn
   fetch_result = HcResult()

   output_buf = ""
   if type(column_width) is not list:
      column_width = [column_width]

   total_width = sum(int(CW) for CW in column_width)

   db = odbcConn(DSN)
   try:
      db._GetConnect()
      logger.info('%s :: DB connection success ', GetCurFunc())
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e)
#      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = db.error
      return output_buf, fetch_result

   try:
      if db_param == '':
         db.cursor.execute(db_query)
      else :
         db.cursor.execute(db_query, db_param)
      logger.debug('%s :: DB execute : query : %s', GetCurFunc(), db_query)
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e[1])
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = e[1]
      return output_buf, fetch_result

   while 1:
      row = db.cursor.fetchone()
      if not row:
         output_buf += "-" * abs(total_width) + '\n'
         break
      for value, width in zip(row, column_width):
         output_buf += '%*s' % (int(width), value)
      output_buf += "\n"

   return output_buf, fetch_result

def odbc_query_execute_fetchall(DSN,db_query,db_param, column_width):
   fetch_result = HcResult()

   output_buf = ""
   if type(column_width) is not list:
      column_width = [column_width]

   total_width = sum(int(CW) for CW in column_width)
#   try:
#      total_width = sum(int(CW) for CW in column_width)
#   except:
#      total_width = column_width

   try:
      from lib.odbc_conn import odbcConn
   except ImportError as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e)
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = e
      return output_buf, fetch_result

   db = odbcConn(DSN)
   try:
      db._GetConnect()
      logger.info('%s :: DB connection success ', GetCurFunc())
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e)
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = db.error
      return output_buf, fetch_result

   try:
      if db_param == '':
         db.cursor.execute(db_query)
      else :
         db.cursor.execute(db_query, db_param)
      logger.debug('%s :: DB execute : query : %s', GetCurFunc(), db_query)
   except Exception as e:
      logger.exception('%s :: error : %s', GetCurFunc(), e[1])
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = e[1] + '\n' + output_buf
      return output_buf, fetch_result

   rows = db.cursor.fetchall()
   if len(rows) == 0:
      output_buf += "=" * abs(total_width) + '\n'
      fetch_result.result = "NOK"
      fetch_result.reason = "NOT_EXIST: empty list is returned"
      return output_buf, fetch_result
   for row in rows:
      for value, width in zip(row, column_width):
         output_buf += '%*s' % (int(width), value)
      output_buf += "\n"
   output_buf += "=" * abs(total_width) + '\n'
#   output_buf += "\n"

   return output_buf, fetch_result


def GetSystemManufacturer():
   output = os_execute('sudo /usr/sbin/dmidecode -s system-manufacturer | tail -1')
   logger.debug('%s :: Type output : %s', GetCurFunc(), type(output))
   SystemManufacturer = re.sub('\n','',output)
   return SystemManufacturer

def os_execute(OsCommand):
   try:
      std_out = subprocess.check_output(OsCommand, stderr=subprocess.STDOUT, shell=True)
   except subprocess.CalledProcessError as e:
      logger.exception('%s :: error return code : %s', GetCurFunc(), e.returncode)
      std_out = e.output
   logger.debug('%s :: std_out : \n%s', GetCurFunc(), std_out)

   return std_out

def ip_address_List():
   ''' return IP address list
   '''
   retlist = []
   for nic, addrs in psutil.net_if_addrs().items():
      for addr in addrs:
         if addr.family == 2 :
            retlist.append(addr.address)
#              print(" address   : %s" % addr.address)
#              print(" family :  : %s" % addr.family)
   return retlist

def net_io_counters():
   ''' Check Net io counters 
   '''
   net_io_counters_result = HcResult()
   hc_result_table = HcCmdResultTalbe('NET IO 확인',78)

   buf = ""
   net_io_counters_result.result = "OK"
   for nic, netio_counters in psutil.net_io_counters(pernic=True).items():
      if nic == 'lo' or nic == 'sit0':
         continue

      buf += " NIC : %5s, errin : %3s, errout : %3s" % (nic, netio_counters.errin, netio_counters.errout)  + '\n'
      if netio_counters.errin >= 100 or netio_counters.errout >= 100:
         net_io_counters_result.result = "NOK"

   hc_result_table._concate(buf)
   net_io_counters_result.output = hc_result_table.output

   return net_io_counters_result

def net_if_stats():
   ''' Check Net if stats 
   '''
   duplex_map = {
      psutil.NIC_DUPLEX_FULL: "full",
      psutil.NIC_DUPLEX_HALF: "half",
      psutil.NIC_DUPLEX_UNKNOWN: "?",
   }

   net_if_stats_result = HcResult()
   hc_result_table = HcCmdResultTalbe('NET interface 확인',78)

   buf = ""
   net_if_stats_result.result = "OK"
   for nic, nic_stats in psutil.net_if_stats().items():
      if nic == 'lo' or nic == 'sit0':
         continue

      buf += " NIC : %4s, isup : %5s, duplex : %3s, speed : %4s" % (nic, nic_stats.isup, duplex_map[nic_stats.duplex], nic_stats.speed)  + '\n'
      if nic_stats.isup != True or nic_stats.duplex != 2:
         net_if_stats_result.result = "NOK"

   hc_result_table._concate(buf)
   net_if_stats_result.output = hc_result_table.output

   return net_if_stats_result

def net_if_address():
   ''' Check Net if address 
   '''
   net_if_addrs_result = HcResult()
   hc_result_table = HcCmdResultTalbe('Net interface address 확인',78)

   config = ConfigLoad()
   net_if_addrs_from_config = config.get_items_from_section('ipa')
   logger.info('%s :: net_if_addrs_from_config  : %s', GetCurFunc(), net_if_addrs_from_config)

   ipa_dic = {}
   for nic_name, nic_value_list in psutil.net_if_addrs().items():
      if nic_name == 'lo' or nic_name == 'sit0':
         continue
      for nic_value in nic_value_list: 
         if nic_value.family == socket.AF_INET:
            ip_addrs = nic_value.address
         else:
            continue
      ipa_dic[nic_name] = ip_addrs

   buf = ""
   net_if_addrs_result.result = "OK"
   for nic_name_conf, ip_addrs_conf in net_if_addrs_from_config:
      search_result = "OK"
      ip_addrs_sys = ipa_dic.get(nic_name_conf)
      if ip_addrs_sys != ip_addrs_conf:
         net_if_addrs_result.result = "NOK"
         search_result = "NOK"

      buf += "  %4s : %15s                                 [ %3s ]" \
		   % (nic_name_conf, ip_addrs_conf, search_result  )  + '\n'

   hc_result_table._concate(buf)
   net_if_addrs_result.output = hc_result_table.output

   return net_if_addrs_result

def ping_status():
   ping_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('Ping 확인 : ping -c 4 -w 4 gateway_ip',78)

   config = ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')

   HC_CONFIG_PING_PATH= os.path.join(hc_home_path, 'config/ping')
   HostInfo = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HostInfo._host_info()
   ping_config_file = HostInfo.hostname + '.cfg'
   ping_config_file_path = os.path.join(HC_CONFIG_PING_PATH, ping_config_file)

   config = ConfigLoad(ping_config_file_path)
   gateway_ip = config.get_item_from_section('default', 'gateway')

   ping_command='ping -c 4 -w 4 ' + gateway_ip
   ping_result = os_execute(ping_command)
   ping_result_list = ping_result.split('\n')

   for line in ping_result_list:
      if 'packet loss' in line:
         PingResult = line.split(',')
   PacketLoss = re.findall(r'\d', PingResult[2])

   if int(PacketLoss[0]) < 20:
      ping_status_result.result = "OK"
   else:
      ping_status_result.result = "NOK"

#   print ' Packet Loss : %2s %% ' % (PacketLoss[0])

   hc_result_table._concate(ping_result)
   ping_status_result.output = hc_result_table.output

   return ping_status_result

def route_status():
   route_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('route 확인 : netstat -rn',78)

   config = ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')

   HC_CONFIG_ROUTE_PATH= os.path.join(hc_home_path, 'config/route')

   route_command='/bin/netstat -rn'
   route_command_result = os_execute(route_command)
   route_command_result_list = route_command_result.split('\n')

   route_result = ''
   route_result += "Kernel IP routing table\n"
   route_result += "Destination     Gateway         Genmask         Flags   MSS Window  irtt Iface "
   route_result += "Netconf파일정보유무               비고\n"

   route_status_result.result = "OK"

   HostInfo = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HostInfo._host_info()
   route_config_file = HostInfo.hostname + '.cfg'
   route_config_file_path = os.path.join(HC_CONFIG_ROUTE_PATH, route_config_file)
   logger.info('%s :: route_config_file_path : %s', GetCurFunc(), route_config_file_path)

   route_config = ConfigLoad(route_config_file_path)
   route_dest_sections_from_config = route_config.get_sections()

   for route_dest_section in route_dest_sections_from_config:
      DEST = route_config.get_item_from_section(route_dest_section, 'DEST')
      GW = route_config.get_item_from_section(route_dest_section, 'GW')
      DESC = route_config.get_item_from_section(route_dest_section, 'DESC')

      search_result = "NOK"
      for route_command_result_line in route_command_result_list:
         if DEST in route_command_result_line and GW in route_command_result_line:
            if DEST == '0.0.0.0':
               netconf_file_info = 'Default Gateway'
            else :
               Iface = route_command_result_line.split()
               NETMASK = Iface[2]
               cidr = netmask2cidr(NETMASK)
               NIC = Iface[7]
               network_scripts_file = '/etc/sysconfig/network-scripts/'+'route-'+NIC
               logger.info('%s :: network_scripts_file : %s', GetCurFunc(), network_scripts_file)
               dest_with_cidr = DEST + '/' + cidr
               if GW == '0.0.0.0':
                  netconf_file_info = '자체 네트워크'
               else :
                  netconf_file_info = single_grep(DEST, network_scripts_file)
                  logger.info('%s :: %s in netconf_file_info ?: %s', \
                               GetCurFunc(), dest_with_cidr, netconf_file_info)
                  if netconf_file_info == None:
                     netconf_file_info = '미존재'
                     route_status_result.result = "NOK"
            route_result += "%-78s %-33s %s\n" % \
                            ( route_command_result_line, netconf_file_info, DESC)
            search_result = "OK"
            break
      if search_result != "OK":
         route_result += " %-10s : %-s " % ( DEST, GW)
         route_result += ' routing table에 없음\n'
         route_status_result.result = "NOK"

   hc_result_table._concate(route_result)
   route_status_result.output = hc_result_table.output

   return route_status_result


def crontab_status():
   crontab_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('crontab 확인 : crontab -l',78)

   config = ConfigLoad()
   crontab_from_config = config.get_items_from_section('crontab')
   logger.info('%s :: crontab_from_config  : %s', GetCurFunc(), crontab_from_config)

   crontab_command='sudo crontab -l'
   crontab_command_result = os_execute(crontab_command)
   crontab_command_result_list = crontab_command_result.split('\n')

   crontab_result = ''
   crontab_status_result.result = "OK"
   for crontab_entry,crontab_command in crontab_from_config:
      search_result = "NOK"
      for crontab_command_result_line in crontab_command_result_list:
         if crontab_command in crontab_command_result_line:
            crontab_result += " %-10s : " % ( crontab_entry )
            crontab_result += crontab_command_result_line + '\n'
            search_result = "OK"			
            break
      if search_result != "OK":
         crontab_result += crontab_entry + ' : ' + crontab_command
         crontab_result += ' crontab 목록에 없음\n'
         crontab_status_result.result = "NOK"

   hc_result_table._concate(crontab_result)
   crontab_status_result.output = hc_result_table.output

   return crontab_status_result

def sshd_status():
   ''' Check sshd status
   '''
   sshd_status_result = HcResult()
   hc_result_table = HcCmdResultTalbe('sshd running 확인',78)

   sshd_status_result.result = "OK"

   SSHD_PID = "/var/run/sshd.pid"
   try:
      f = open(SSHD_PID, 'r')
   except IOError as e:
      sshd_status_result.result = "NOK"
      hc_result_table._concate(e)
      sshd_status_result.output = hc_result_table.output
      return sshd_status_result

   pid = int(f.read())

   buf = 'Process Name     PID   PPID   USER  %MEM  PATH                 CREATE TIME\n'
   buf += "-" * hc_result_table.column_width + '\n'

   p = psutil.Process(pid)

   create_time=datetime.datetime.fromtimestamp(p.create_time()).strftime("%Y-%m-%d %H:%M:%S")
   templ = "%-13s %6s %6s   %-5s %-5s %-20s %-s\n"
   buf += templ % (p.name(), p.pid, p.ppid(), p.username(), round(p.memory_percent(),1),"".join(p.cmdline()), create_time)

   if p.name() == 'sshd':
      sshd_status_result.result = "OK"

   hc_result_table._concate(buf)
   sshd_status_result.output = hc_result_table.output

   return sshd_status_result
