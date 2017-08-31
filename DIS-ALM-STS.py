#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import sys
import argparse
import re
from lib.vms_hc import OdbcQuery, HostInfo


def dis_alm_sts(direction):
   vic_alm = OdbcQuery('VIC 알람 정보','mysql')  

   vic_alm.db_column_name=[
   '등급',
   '인지',
   '최초발생',
   '종류',
   '장비',
	'발생지점',
   '내용']
   vic_alm.db_column_width=[
	'-6',
	'-5',
	'-15',
	'-22',
	'-10',
	'-35',
	'-40']

   vic_alm.db_query = """
   SELECT 
   CASE 
      WHEN A.severity = 1
		THEN 'CRIT'
      WHEN A.severity = 2
		THEN 'MAGER'
      WHEN A.severity = 3
		THEN 'MINOR'
		END AS serveriy,
   CASE
	   WHEN A.confirmed = 0
		THEN '[ ]'
	   WHEN A.confirmed = 1
		THEN '[V]'
		END AS confirmed,
   DATE_FORMAT(A.firstTime, "%c-%e %T"),
   C.eventName,
   B.sysname,
   A.source,
   A.alarmMessage
   from SAM_ALARM A inner join SAM_SYSTEM B on A.systemid = B.systemid 
					     inner join SAM_EVENTTYPE C on A.eventTypeId = C.eventTypeId
   WHERE A.cleared = 0 
	ORDER by A.firstTime DESC;
   """
   vic_alm.db_param = ''
   vic_alm.set_vertical= direction
   vic_alm_result = vic_alm.make_output()

   result_templ = "   %-10s %3s %-30s "
   if vic_alm_result.result == "OK":
      print(vic_alm_result.output)
      print(result_templ % ("RESULT", "=", vic_alm_result.result))
   else:
      print(vic_alm_result.header)
      print(result_templ % ("RESULT", "=", vic_alm_result.result))
      print(result_templ % ("REASON", "=", vic_alm_result.reason))
   print("")

def is_phone_number(phoneid):
#   rule = re.compile('01[0-9]{1}[0-9]{8}')
   rule = re.compile(r'(01[0-9]{1}[0-9]{8})')

   if not rule.search(phoneid):
      msg = "%s is Invalid phone number." % phoneid
      raise argparse.ArgumentTypeError(msg)
   return phoneid

def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
   parser.add_argument('-v', '--vertical', action='store_true')
#   parser.add_argument('-p', '--phoneid', action='store', required=True, type=is_phone_number, help="phoneid, ex) 01090874208")
   args = parser.parse_args()

   HOST_INFO = HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HOST_INFO._host_info()

   if HOST_INFO.hostclass != 'OMP':
      print("OMP에서 실행해주세요..")
      sys.exit()

   if args.vertical :
      direction = "on"
      dis_alm_sts(direction)
   else:
      direction = "off"
      dis_alm_sts(direction)

if __name__ == "__main__":
   sys.exit(main())
