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
   rule = re.compile(r'(01[0-9]{1}[0-9]{8})')

   if not rule.search(phoneid):
      msg = "%s is Invalid phone number." % phoneid
      raise argparse.ArgumentTypeError(msg)
   return phoneid

def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
   args = parser.parse_args()

   dis_svc_sts()

if __name__ == "__main__":
   sys.exit(main())
