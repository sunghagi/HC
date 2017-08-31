#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: euckr -*-
import sys
#import datetime
import argparse
import re
from lib.vms_hc import *


def dis_svc_sts():
   vic_svc_sts = OdbcQuery('VIC 서비스 통계','mysql')  
   print(vic_svc_sts.yesterday, vic_svc_sts.today)

   vic_svc_sts.db_column_name=[
   '통계 수집시간',
	'menuId',
   'sum(menuCount)',
	]
   vic_svc_sts.db_column_width=['20','15','15']
#   vic_svc_sts.set_vertical="on"

   vic_svc_sts.db_query = """
   SELECT 
	collectTime, 
	menuId, 
   SUM(menuCount) menuCount
	FROM VIC_ST_SERVICE_HOUR
   WHERE collectTime >= ? AND collectTime <= ? 
   GROUP BY collectTime, menuId
   """
#AND systemId = 101 AND serviceType = 1
   vic_svc_sts.db_param = [vic_svc_sts.yesterday, vic_svc_sts.today]
   vic_svc_sts_result = vic_svc_sts.make_output()

   result_templ = "   %-10s %3s %-30s "
   if vic_svc_sts_result.result == "OK":
      print vic_svc_sts_result.output
      print result_templ % ("RESULT", "=", vic_svc_sts_result.result)
   else:
      print vic_svc_sts_result.header
      print result_templ % ("RESULT", "=", vic_svc_sts_result.result)
      print result_templ % ("REASON", "=", vic_svc_sts_result.reason)
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
#   parser.add_argument('-p', '--phoneid', action='store', required=True, type=is_phone_number, help="phoneid, ex) 01090874208")
   args = parser.parse_args()

#   HOST_INFO = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
#   HOST_INFO._host_info()

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode
#   HaInstalled = HOST_INFO.ha_installed

#   dis_svc_sts(args.phoneid)
   dis_svc_sts()

if __name__ == "__main__":
   sys.exit(main())
