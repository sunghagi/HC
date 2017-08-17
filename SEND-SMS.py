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

SendSmsConfigPath='/nas/HC/config/sendsms.cfg'

def AltibaseInsertQueryExecute(db_query,db_param):
   from lib.altibase import AltibaseConn
   db = AltibaseConn('DSN=tars_local')
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
      HcPeriod = '����'
   elif HcPeriodCsv == 'WEEKLY':
      HcPeriod = '�ְ�'
   elif HcPeriodCsv == 'MONTHLY':
      HcPeriod = '����'
   else :
      HcPeriod = '����'
      
   sms_text_head = check_date + ' ' + HcPeriod + '���� ���\n'
   SMS_TEXT = sms_text_head + sms_text_hcresult
   logger.info('%s :: SMS TEXT : \n%s', GetCurFunc(), SMS_TEXT)

   if len(SMS_TEXT) > 80:
      # sms head text : 24 bytes : 2017-08-16 �������� ���
      SMS_TEXT = SMS_TEXT[:77] + '...'
      logger.info('%s :: sms length : %s', GetCurFunc(), len(SMS_TEXT))

   return SMS_TEXT


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
      logger.info('%s :: result : %s', GetCurFunc(), ', '.join(row))
      logger.exception('%s :: CSV file handle error : %s',GetCurFunc(), e)
      Period='DAILY'
   return Period

def SendSms(Phoneid, Message):
   #SmsType 
   #0 - OMC �˶�
   #1 - ��������
   #2 - ������Ʈ �ȳ�
   #3 - ���� ���� �˸�
   #4 - ���� ���� �˸�
   pStmt = """
   INSERT INTO SMSINFO(SerialNo,PhoneId,CallerId,SmsType,Message) 
   VALUES(seq_smsinfo_serialno.NEXTVAL,?,'0112008585',0,?);
   """
   db_param = [Phoneid,Message]
   AltibaseInsertQueryExecute(pStmt,db_param)

def phoneid_from_config():
   config = ConfigLoad(SendSmsConfigPath)
   phoneid_list = dict(config.get_items_from_section('hc result')).values()

   logger.debug('Phoneid List : %s', phoneid_list)

   return phoneid_list

def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool send a sms.")
   parser.add_argument('-m', '--monthly', action='store_true')
   args = parser.parse_args()

   sms_text_hcresult = gen_sms_text()
#   HcResultMerge = ''
#   HcResultMerge = HcResultMerge + '\n' + ResultPerSystem 

   print sms_text_hcresult

   phoneid_list = phoneid_from_config()
   logger.info('%s :: SMS receive list : %s', GetCurFunc(), ', '.join(phoneid_list))
#   for PhoneId in phoneid_list:
#      SendSms(PhoneId, sms_text_hcresult)

if __name__ == "__main__":
   main()
