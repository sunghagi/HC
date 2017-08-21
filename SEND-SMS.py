#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import argparse
import ConfigParser
import csv
import time

from lib.vms_hc import *

def AltibaseInsertQueryExecute(db_query,db_param):
   from lib.odbc_conn import odbcConn

   config = ConfigLoad()
   dsn_from_config = config.get_item_from_section('DB DSN', 'altibase')
   dsn_string = 'DSN=%s' % (dsn_from_config)
#   db = AltibaseConn(dsn_string)
   db = odbcConn(dsn_string)
   db._GetConnect()

   if db_param == '':
      db.cursor.execute(db_query)
   else :
      db.cursor.execute(db_query, db_param)
   db.cnxn.commit()

def gen_sms_text():
   HostInfo = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
   HostInfo._host_info()

   config = ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')
   check_date = datetime.date.today().strftime("%Y-%m-%d")
   csv_file_name = os.path.join(hc_home_path, check_date.replace('-','')+'_'+HostInfo.system_name+'.csv')

   RESULT='OK'
   reason_text = ''
   try:
      with open(csv_file_name, 'rt') as f:
         reader = csv.reader(f, delimiter=',')
         for row in reader:
            if row[6] == "NOK":
               logger.info('%s :: SystemNumber : %s, %s result : %s', GetCurFunc(), row[4], row[5], row[6])
               REASON=row[4] + ' ' + row[5] + '\n'
               reason_text += REASON
               RESULT='NOK'
   except Exception as e:
      logger.exception('%s :: CSV file handle error : %s',GetCurFunc(), e)
      reason_text = str(e)
      RESULT='NOK'

   if RESULT == 'OK':
      sms_text_hcresult = HostInfo.system_name + ': ' + RESULT
   else:
      sms_text_hcresult = HostInfo.system_name + ': ' + RESULT +'\n'
      sms_text_hcresult += reason_text

   HcPeriodCsv = GetHcPeriod(csv_file_name, HostInfo.system_name)
   if HcPeriodCsv == 'DAILY':
      HcPeriod = "일일"
   elif HcPeriodCsv == 'WEEKLY':
      HcPeriod = '주간'
   elif HcPeriodCsv == 'MONTHLY':
      HcPeriod = '월간'
   else :
      HcPeriod = '일일'
      
   sms_text_head = check_date + ' ' + HcPeriod + '점검 결과\n'
   SMS_TEXT = sms_text_head + sms_text_hcresult
   logger.info('%s :: SMS TEXT : \n%s', GetCurFunc(), SMS_TEXT)

   sms_text_list = split2len(SMS_TEXT,80)
#   print ('\n'.join(sms_text_list))

#   if len(SMS_TEXT) > 80:
#      # sms head text : 24 bytes : 2017-08-16 일일점검 결과
#      SMS_TEXT = SMS_TEXT[:77] + '...'
#      logger.info('%s :: sms length : %s', GetCurFunc(), len(SMS_TEXT))

   return sms_text_list


def GetHcPeriod(CsvFileName, SystemNumber):
   try:
      with open(CsvFileName, 'rt') as f:
         reader = csv.reader(f, delimiter=',')
         for row in reader:
            Period = row[2]
            logger.info('%s :: HC Period : %s', GetCurFunc(), Period)
            if not Period == '':
               break
   except Exception as e:
      logger.exception('%s :: CSV file handle error : %s',GetCurFunc(), e)
      print "%s 실행결과가 없습니다." % ( CsvFileName )
      sys.exit()
      Period='DAILY'
   return Period

def SendSms(Phoneid, Message):
   #SmsType 
   #0 - OMC 알람
   #1 - 공지사항
   #2 - 업데이트 안내
   #3 - 서비스 가입 알림
   #4 - 서비스 해지 알림
   pStmt = """
   INSERT INTO SMSINFO(SerialNo,PhoneId,CallerId,SmsType,Message) 
   VALUES(seq_smsinfo_serialno.NEXTVAL,?,'0112008585',0,?);
   """
   Message_unicode = unicode(Message,'euc-kr')
   db_param = [Phoneid,Message_unicode]

   AltibaseInsertQueryExecute(pStmt,db_param)

def phoneid_from_config():
   config = ConfigLoad()
   hc_home_path = config.get_item_from_section('main', 'path')
   CONFIG_PATH = os.path.join(hc_home_path, 'config/sendsms.cfg')

   config = ConfigLoad(CONFIG_PATH)
   phoneid_list = dict(config.get_items_from_section('hc result')).values()

   logger.debug('Phoneid List : %s', phoneid_list)

   return phoneid_list

def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool send a sms.")
   parser.add_argument('-m', '--monthly', action='store_true')
   args = parser.parse_args()

   sms_text_list = gen_sms_text()

   phoneid_list = phoneid_from_config()
   logger.info('%s :: SMS receive list : %s', GetCurFunc(), ', '.join(phoneid_list))
   for sms_text in sms_text_list:
      logger.info('%s :: sms_text : %s', GetCurFunc(), sms_text)
      for PhoneId in phoneid_list:
         SendSms(PhoneId, sms_text)

if __name__ == "__main__":
   main()
