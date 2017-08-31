#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import sys
import lib.vms_hc
import argparse
import re
from lib.vms_hc import *


def dis_subs(phoneid, direction):
   vic_subs = OdbcQuery('VIC 가입자 정보','altibase')  

   vic_subs.db_column_name=['가입자전화번호','가입자구분','가입자이름설정여부',
									'사서함 구분','단말 구분','CREATEDDATE','lastUpdatedDate']
   vic_subs.db_column_width=['15','17','22','12','12','20','20']

   vic_subs.db_query = """
   select PHONEID,
   decode(userClass, 1, '일반 사용자',
                     2, 'ISUP 자동가입',
                     3, '시험용 가입자'),
   decode(greetFlag, 0, 'play 안함',
                     1, 'play 함'),
   decode(mmcType, 1, '324',
                   2, 'SIP'),
   decode(termType, 1, 'old UI(TEXT)',
                     2, 'new UI(mmc)',
                     3, 'new UI(mmc)',
                     4, 'Global'),
   to_char(createdDate, 'YYYY-MM-DD HH24:MI:SS'),
   to_char(lastUpdatedDate, 'YYYY-MM-DD HH24:MI:SS')
   from SUBSCRIBERS
   where phoneid = ?
   """
   vic_subs.db_param = phoneid
   vic_subs.set_vertical = direction
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
      dis_subs(args.phoneid, direction)
   else:
      direction = "off"
      dis_subs(args.phoneid, direction)

if __name__ == "__main__":
   sys.exit(main())
