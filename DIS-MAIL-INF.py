#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import sys
#import datetime
import argparse
import re
from lib.vms_hc import OdbcQuery


def dis_mailinfo(phoneid, direction):
   vic_subs = OdbcQuery('VIC 가입자 사서함 정보','altibase')  

   vic_subs.db_column_name=[
   '가입자전화번호',
	'사서함종류',
   '확인여부',
   '장기보존여부',
   '파일정보',
   '남긴번호',
   '발신자전화번호',
   '착신자전화번호',
	'저장시각',
	'최종수정시각']
   vic_subs.db_column_width=[16,11,9,13,21,12,16,16,20,20]

   vic_subs.db_query = """
   select
   PHONEID,
   CASE
      WHEN msgType = 1
      THEN 'VOICE'
      WHEN msgType = 2
      THEN 'TEXT'
      WHEN msgType = 3
      THEN 'MMC'
      WHEN msgType = 4
      THEN 'EMAIL'
      WHEN msgType = 5
      THEN 'PHONEMAIL'
      WHEN msgType = 6
      THEN 'EXTRA'
      END AS msgType,
   CASE
      WHEN Played = 0
      THEN '미청취'
      WHEN Played = 1
      THEN '청취'
      END AS Played,
   CASE
      WHEN Played = 0
      THEN '일반'
      WHEN Played = 1
      THEN '장기'
      END AS preserved,
   fileName,
	reqCallId,
   callerId,
   destPhoneId,
   to_char(createdDate, 'YYYY-MM-DD HH24:MI:SS'),
   to_char(lastUpdatedDate, 'YYYY-MM-DD HH24:MI:SS')
   from MAILINFO
   where phoneid = ?
   """
   vic_subs.db_param = phoneid
   vic_subs.set_vertical= direction
   vic_subs_result = vic_subs.make_output()

   result_templ = "   %-10s %3s %-30s "
   if vic_subs_result.result == "OK":
      print(vic_subs_result.output)
      print(result_templ % ("RESULT", "=", vic_subs_result.result))
   else:
      print(vic_subs_result.header)
      print(result_templ % ("RESULT", "=", vic_subs_result.result))
      print(result_templ % ("REASON", "=", vic_subs_result.reason))
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
   parser.add_argument('-p', '--phoneid', action='store', required=True, type=is_phone_number, help="phoneid, ex) 01090874208")
   args = parser.parse_args()

#   HOST_INFO = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
#   HOST_INFO._host_info()

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode
#   HaInstalled = HOST_INFO.ha_installed
   if args.vertical :
      direction = "on"
      dis_mailinfo(args.phoneid, direction)
   else:
      direction = "off"
      dis_mailinfo(args.phoneid, direction)

if __name__ == "__main__":
   sys.exit(main())
