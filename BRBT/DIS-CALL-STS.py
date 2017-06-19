#!/NAS/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import sys
import lib.vms_hc
import datetime
import argparse

def valid_date(d):
   try:
      return datetime.datetime.strptime(d, "%Y-%m-%d")
   except ValueError:
      msg = "Not a valid date: '{0}'.".format(d)
      raise argparse.ArgumentTypeError(msg)

def dis_call_sts(DSN, checkday):
   cmd_result = lib.vms_hc.HcResult()	

   column_name = ' BIZ RING CALL STAT INFORMATION '
#   db_column_name=['STATTIME','CALL','AHT']
   db_column_name=['STATTIME','CALL','USER_NOT_FOUND','DB_ERR','PRCS_ERR','HOLIDAY','TEMP_STOP','NO_SCHEDULE','ETC','AHT']
   db_column_width=['21','10','20','10','10','10','12','12','7','7']
   column_width = sum(int(CW) for CW in db_column_width)
   cmd_result_table = lib.vms_hc.HcCmdResultTalbe(column_name, column_width)

   print cmd_result_table.output

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode


#   if HaStatus == 'ACTIVE':
#   checkday = datetime.date.today().strftime("%Y-%m-%d")
   stat_start_time=checkday + ' ' + '00:00:00'
   stat_end_time=checkday + ' ' + '23:59:59'
	
   db_query = """
	select collectTime,
	SUM(totalCallCount) TOTAL_CALL,
	SUM(user_not_found) USER_NOT_FOUND,
	SUM(db_query_error) DB_ERR,
	SUM(br_process_error) PRCS_ERR,
	SUM(holiday) HOLIDAY,
	SUM(temp_stop) TEMP_STOP,
	SUM(no_schedule) NO_SCHEDULE,
	SUM(unknown_error) ETC,
	ROUND(SUM(totalCallCount*holdingTime)/SUM(totalCallCount),1) AHT
	from  brbt_st_cdr_hour 
	where collectTime between ? and ?
	group by collectTime;
   """
   db_param = [stat_start_time, stat_end_time]
   subs, result = lib.vms_hc.odbc_query_execute_fetchall(DSN, db_query, db_param, db_column_width)

   db_column_name = lib.vms_hc.print_column_name(db_column_name, db_column_width)

   if result.result == "OK":
      output_buf = lib.vms_hc.string_concate(db_column_name, subs)
      print output_buf

   result_templ = "   %-10s %3s %-30s "
   print result_templ % ("RESULT", "=", result.result)
   if result.result == "NOK":
      print result_templ % ("REASON", "=", result.reason)
   print ""

def main():
   today = datetime.date.today().strftime("%Y-%m-%d")
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
#   parser.add_argument('-d', '--date', help="date, ex) 2015-09-08", default=today, type=valid_date)
   parser.add_argument('-d', '--date', help="date, ex) 2015-09-08", default=today)
   args = parser.parse_args()

#   HOST_INFO = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
#   HOST_INFO._host_info()

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode
#   HaInstalled = HOST_INFO.ha_installed

   if args.date:
      db_parameter = args.date
#   dis_subs(HOST_INFO, "DSN=odbc_db1", db_parameter)
   dis_call_sts("DSN=mysql", db_parameter)
#   dis_call_sts("DSN=mysql")

if __name__ == "__main__":
   sys.exit(main())
