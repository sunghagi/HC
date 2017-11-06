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

   logger.info('%s :: current Check mode : %s', GetCurFunc(), current_check_mode)

   return current_check_mode

def get_exec_mode(host_info, check_host, current_check_mode, config_check_mode):
   '''
   check_host : ALL, SPS, OMP ... from main() health_check_items 
	'''
   if check_host == host_info.hostclass or check_host == 'ALL':
      if current_check_mode >= config_check_mode:
         exec_flag = 1
      else:
         exec_flag = 0
   else:
      exec_flag = 0

   return exec_flag	

def csv_save(host_info, list_result):
   alarm_checkday = lib.vms_hc.get_alarm_checkday()

   config = lib.vms_hc.ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')

   Csv_file_name = os.path.join(hc_home_path, alarm_checkday[1].replace('-','')+'_'+host_info.system_name+'.csv')
   logger.info('%s :: CsvFileName : %s', GetCurFunc(), Csv_file_name)
   lib.vms_hc.SaveResultCsv(Csv_file_name, list_result)


def run_method(host_info, health_check_items, current_check_mode):
   result_chunks = []
   _append = result_chunks.append

   alarm_checkday = lib.vms_hc.get_alarm_checkday()

   VmsHc = lib.vms_hc.HcItem() 

   index = 1
   for item in health_check_items:
      ItemDesc = item[0]
      Method = item[1]
      config_check_mode = item[2]
      check_host = item[3]

      logger.debug('%s : exec_flag : %s,%s,%s,%s', GetCurFunc(), ItemDesc, check_host, current_check_mode, config_check_mode)
      exec_flag = get_exec_mode(host_info, check_host, current_check_mode, config_check_mode)

      if exec_flag :
         logger.info('%s : %s ItemDesc : %s, %s', GetCurFunc(), host_info.hostname, ItemDesc, Method)
         item_status = eval(Method)
      else:
         continue   

      try:
         output = item_status.output 
      except Exception as e:
         logger.exception('%s : error : %s', GetCurFunc(), e)
         output = ""

      try:
         result = item_status.result 
      except Exception as e:
         logger.exception('%s : error : %s', GetCurFunc(), e)
         result = "NOK"
      
      ResultList = [index, alarm_checkday[1], current_check_mode, host_info.system_name, host_info.hostname, ItemDesc, result, output]
      _append(ResultList)
      if result == "OK":
          print("%2s. %-30s : [ %3s ]" % (index, ItemDesc, result))
      else:
          print("%2s. %-30s : [ %3s ] %s " % (index, ItemDesc, result, item_status.reason))
      
      index += 1

   return result_chunks
   
def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool perform a health check.")
   parser.add_argument('-m', '--monthly', action='store_true')
   parser.add_argument('-c', '--console', action='store_false')
   parser.add_argument('-l', '--show-detail-result', action='store_true')
   args = parser.parse_args()

   health_check_items = [
   ['Process Ȯ��', 'VmsHc.process_display()',DAILY,'ALL'],
   ['Ping Ȯ��', 'VmsHc.ping_status()',DAILY,'ALL'],
   ['route Ȯ��', 'VmsHc.route_status()',DAILY,'ALL'],
   ['crontab Ȯ��', 'VmsHc.crontab_status()',DAILY,'ALL'],
   ['CPU ���� Ȯ��', 'VmsHc.cpu_usage()',DAILY,'ALL'],
   ['Memory ���� Ȯ��','VmsHc.memory_usage()',DAILY,'ALL'],
   ['DISK ���� Ȯ��','VmsHc.disk_usage()',DAILY,'ALL'],
   ['DISK inode ���� Ȯ��','VmsHc.disk_inode_usage()',DAILY,'ALL'],
   ['�ý��� Uptime Ȯ��', 'VmsHc.uptime_status()',DAILY,'ALL'],
   ['CORE ���� ���� Ȯ��','VmsHc.corefile_status()',DAILY,'ALL'],
   ['/etc ���', 'VmsHc.etc_backup()',DAILY,'ALL'],
   ['bond status Ȯ��','VmsHc.bond_status_check()',DAILY,'ALL'],
   ['Net If Address Ȯ��', 'VmsHc.net_if_address()',DAILY,'ALL'],
   ['NIC status Ȯ��', 'VmsHc.net_if_stats()',DAILY,'ALL'],
   ['NIC IO Ȯ��', 'VmsHc.net_io_counters()',DAILY,'ALL'],
   ['sshd Ȯ��', 'lib.vms_hc.sshd_status()',DAILY,'ALL'],
   ['NTP ���� Ȯ��', 'lib.vms_hc.ntp_status()',DAILY,'ALL'],
   ['��ũ ����ȭ ���� Ȯ��', 'lib.vms_hc.disk_mirror_status()',DAILY,'ALL'],
   ['���� ���μ��� Ȯ��', 'lib.vms_hc.process_status()',DAILY,'ALL'],
   ['/var/log/messages Ȯ��','lib.vms_hc.messages_check()',DAILY,'ALL'],
#   ['�� �����ڼ� Ȯ��','lib.vms_hc.vic_subscribers()',DAILY,'SPS'],
#   ['altibase tablespace Ȯ��','lib.vms_hc.altibase_tablespace()', DAILY,'SPS'],
#   ['���� CPU ��� Ȯ��', 'lib.vms_hc.cpu_stat()',MONTHLY,'OMP'],
#   ['��Ƽ���̽� �޸� ����','lib.vms_hc.altibase_tablespace("DSN=odbc_local")',DAILY,'SPS'],
#   ['���� alarm', 'lib.vms_hc.dis_alarm()',MONTHLY,'OMP'],
#   ['SIP ��� Ȯ��','lib.vms_hc.tars_sip_stat()',DAILY,'OMP'],
#   ['NAS Fault Ȯ��','lib.vms_hc.nas_status()',DAILY,'OMP'],
   ]

   logger.info('%s : Health Check Start !!', GetCurFunc())

   host_info = lib.hclib.get_host_info()
   logger.info('%s : get host information completed', GetCurFunc())

   logger.info('%s : get current check mode', GetCurFunc())
   current_check_mode = get_current_check_mode(args.monthly)

   hc_result = run_method(host_info, health_check_items, current_check_mode)

   if args.console :
      csv_save(host_info, hc_result)

if __name__ == '__main__': 
   main() 
