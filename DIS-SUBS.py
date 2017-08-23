#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: euckr -*-
import sys
import lib.vms_hc
#import datetime
import argparse
import re
from lib.vms_hc import *


def dis_subs(phoneid):
   vic_subs = OdbcQuery('VIC 가입자 정보','altibase')  

   vic_subs.db_column_name=['가입자 전화번호','가입자 구분','가입자 이름 설정 여부',
									'사서함 구분','단말 구분','CREATEDDATE','lastUpdatedDate']
   vic_subs.db_column_width=['17','10','10','20','20']
   vic_subs.set_vertical="on"

   vic_subs.db_query = """
   select PHONEID,
   userClass,
   greetFlag,
   mmcType,
   termType,
   to_char(createdDate, 'YYYY-MM-DD'),
   to_char(lastUpdatedDate, 'YYYY-MM-DD')
   from SUBSCRIBERS
   where phoneid = ?
   """
   vic_subs.db_param = phoneid
   vic_subs_result = vic_subs.make_output()

   result_templ = "   %-10s %3s %-30s "
   if vic_subs_result.result == "OK":
      print vic_subs_result.output
      print result_templ % ("RESULT", "=", vic_subs_result.result)
   else:
      print vic_subs_result.header
      print result_templ % ("RESULT", "=", vic_subs_result.result)
      print result_templ % ("REASON", "=", vic_subs_result.reason)
   print ""

def is_phone_number(phoneid):
#   rule = re.compile('01[0-9]{1}[0-9]{8}')
   rule = re.compile(r'(01[0-9]{1}[0-9]{8})')

   if not rule.search(phoneid):
      msg = "%s is Invalid phone number." % phoneid
      raise argparse.ArgumentTypeError(msg)
   return phoneid

def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
   parser.add_argument('-p', '--phoneid', action='store', required=True, type=is_phone_number, help="phoneid, ex) 01090874208")
   args = parser.parse_args()

#   HOST_INFO = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
#   HOST_INFO._host_info()

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode
#   HaInstalled = HOST_INFO.ha_installed

   dis_subs(args.phoneid)

if __name__ == "__main__":
   sys.exit(main())
