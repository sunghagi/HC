#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import lib.vms_hc
import datetime
import argparse
import ConfigParser
from lib.vms_hc import logger, GetCurFunc

MONTHLY = 100
WEEKLY = 10
DAILY = 1

def get_current_check_mode(args_monthly):
   ''' get check mode ? DAILY, WEEKLY,  MONTHLY '''
   DayOfTheWeek = datetime.datetime.today().weekday()
   # Mon = 0, Tue = 1, Wed = 2, Thu = 3, Fri = 4, Sat = 5, Sun = 6
   DayOfTheMonth = datetime.datetime.today().strftime("%d")
   if DayOfTheMonth == '25':
      current_check_mode = MONTHLY
   elif DayOfTheWeek == 4:
      current_check_mode = WEEKLY
   else:
      current_check_mode = DAILY

   if args_monthly:
      current_check_mode = MONTHLY

   logger.info('%s :: Health Check Infomation : %s', GetCurFunc(), current_check_mode)

   return current_check_mode

def get_exec_mode(check_host, current_check_mode, config_check_mode):
   '''
   check_host : ALL, SPS, OMP ... from main() health_check_items 
	'''
   HostInfo = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HostInfo._host_info()

   host_class = HostInfo.hostclass

   if check_host == host_class or check_host == 'ALL':
      if current_check_mode >= config_check_mode:
         exec_flag = 1
      else:
         exec_flag = 0
   else:
      exec_flag = 0

   return exec_flag	

def csv_save(list_result):
   alarm_checkday = lib.vms_hc.get_alarm_checkday()

   HostInfo = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HostInfo._host_info()

   config = lib.vms_hc.ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')

   Csv_file_name = os.path.join(hc_home_path, alarm_checkday[1].replace('-','')+'_'+HostInfo.system_name+'.csv')
   logger.info('%s :: CsvFileName : %s', lib.log.GetCurFunc(), Csv_file_name)
   lib.vms_hc.SaveResultCsv(Csv_file_name, list_result)


def run_method(health_check_items, current_check_mode):
   result_chunks = []
   _append = result_chunks.append

   HostInfo = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HostInfo._host_info()

   alarm_checkday = lib.vms_hc.get_alarm_checkday()

   index = 1
   for item in health_check_items:
      ItemDesc = item[0]
      Method = item[1]
      config_check_mode = item[2]
      check_host = item[3]

      logger.info('%s :: exec_flag : %s,%s,%s,%s', lib.log.GetCurFunc(), ItemDesc, check_host, current_check_mode, config_check_mode)
      exec_flag = get_exec_mode(check_host, current_check_mode, config_check_mode)

      if exec_flag :
         item_status = eval(Method)
         logger.info('%s :: %s ItemDesc : %s, %s', GetCurFunc(), HostInfo.hostname, ItemDesc, Method)
      else:
         continue   

      try:
         output = item_status.output 
      except Exception as e:
         logger.exception('%s :: error : %s', GetCurFunc(), e)
         output = ""

      try:
         result = item_status.result 
      except Exception as e:
         logger.exception('%s :: error : %s', GetCurFunc(), e)
         result = "NOK"
      
      ResultList = [index, alarm_checkday[1], current_check_mode, HostInfo.system_name, HostInfo.hostname, ItemDesc, result, output]
      _append(ResultList)
      print "%2s. %-30s : [ %3s ]" % ( index, ItemDesc, result )
      index += 1

   return result_chunks
   
def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool perform a health check.")
   parser.add_argument('-m', '--monthly', action='store_true')
   parser.add_argument('-c', '--console', action='store_false')
   parser.add_argument('-l', '--show-detail-result', action='store_true')
   args = parser.parse_args()

   health_check_items = [
   ['Process 확인', 'lib.vms_hc.process_display()',DAILY,'ALL'],
   ['sshd 확인', 'lib.vms_hc.sshd_status()',DAILY,'ALL'],
   ['CORE 파일 생성 확인','lib.vms_hc.corefile_status()',DAILY,'ALL'],
   ['Ping 확인', 'lib.vms_hc.ping_status()',DAILY,'ALL'],
   ['route 확인', 'lib.vms_hc.route_status()',DAILY,'ALL'],
   ['crontab 확인', 'lib.vms_hc.crontab_status()',DAILY,'ALL'],
   ['NTP 연동 확인', 'lib.vms_hc.ntp_status()',DAILY,'ALL'],
   ['CPU 사용률 확인', 'lib.vms_hc.cpu_usage()',DAILY,'ALL'],
   ['Memory 사용률 확인','lib.vms_hc.memory_usage()',DAILY,'ALL'],
   ['DISK 사용률 확인','lib.vms_hc.disk_usage()',DAILY,'ALL'],
   ['시스템 Uptime 확인', 'lib.vms_hc.uptime_status()',DAILY,'ALL'],
   ['디스크 이중화 상태 확인', 'lib.vms_hc.disk_mirror_status()',DAILY,'ALL'],
   ['Net If Address 확인', 'lib.vms_hc.net_if_address()',DAILY,'ALL'],
   ['NIC IF 확인', 'lib.vms_hc.net_if_stats()',DAILY,'ALL'],
#   ['NIC IO 확인', 'lib.vms_hc.net_io_counters()',DAILY,'ALL'],
#   ['알티베이스 메모리 사용률','lib.vms_hc.altibase_tablespace("DSN=odbc_local")',DAILY,'SPS'],
   ['좀비 프로세스 확인', 'lib.vms_hc.process_status()',DAILY,'ALL'],
   ['/etc 백업', 'lib.vms_hc.etc_backup()',DAILY,'ALL'],
   ['총 가입자수 확인','lib.vms_hc.vic_subscribers()',DAILY,'SPS'],
   ['altibase tablespace 확인','lib.vms_hc.altibase_tablespace()', DAILY,'SPS'],
   ['월간 alarm', 'lib.vms_hc.dis_alarm()',MONTHLY,'OMP'],
   ['월간 CPU 통계 확인', 'lib.vms_hc.cpu_stat()',MONTHLY,'OMP'],
   ['SIP 통계 확인','lib.vms_hc.tars_sip_stat()',DAILY,'OMP'],
   ['NAS Fault 확인','lib.vms_hc.nas_status()',DAILY,'OMP'],
   ]

   current_check_mode = get_current_check_mode(args.monthly)
   hc_result = run_method(health_check_items, current_check_mode)

   if args.console :
      csv_save(hc_result)

if __name__ == '__main__': 
   main() 
