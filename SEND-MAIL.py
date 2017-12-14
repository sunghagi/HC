#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import argparse
import csv
import smtplib
import base64
import lib.vms_hc
from lib.vms_hc import logger, GetCurFunc
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from email import Utils
from email.header import Header

#MAIL_ID_LIST=['hagee@pointi.com', 'jmpark@pointi.com','ksunglok@pointi.com','bluebriz@pointi.com']

MAIL_ID_LIST=['hagee@iok.co.kr']
smtp_server  = "222.122.219.59"
port = 587
userid = 'hagee@iok.co.kr'
passwd = '12345'

def get_vic_result(CsvFileName, SystemNumber):
    ResultMerge = ''
    try:
       with open(CsvFileName, 'rt') as f:
          reader = csv.reader(f, delimiter=',')
          for row in reader:
             logger.info('%s :: Check Item : %s', GetCurFunc(), row[5])
             if row[5] == 'Process 확인':
                CheckDate = row[1]
                CheckSystem = row[3]
                CheckHost = row[4]
                CheckItem = row[5]
                result = row[7]   
                logger.info('%s :: Check Result : \n%s', GetCurFunc(), result)
    except Exception as e:
       logger.exception('%s :: CSV file handle error : %s', GetCurFunc(), e)
       sys.exit()
    MailText = CheckDate + ": " + CheckSystem + ": " + CheckItem + result

    return MailText

def send_mail(subject, text):
    COMMASPACE = ", "

    from_user = 'rd3@iok.co.kr'
    to_user = COMMASPACE.join(MAIL_ID_LIST)
#    cc_users = 'network.support@pointi.com'
    cc_users = 'hagee@pointi.com'
#    sender = 'ivms'
    attach = ''
    msg = MIMEMultipart("alternative")
    msg["From"] = from_user
#    msg['From'] = '=?euc-kr?B?' + base64.standard_b64encode(sender) + '?=' + '<' + from_user + '>'
    msg["To"] = to_user
#    msg["Cc"] = cc_users
    msg["Subject"] = Header(s=subject, charset="euc-kr")
#    msg["Subject"] = '=?euc-kr?B?' + base64.standard_b64encode(subject) + '?='
    msg["Date"] = Utils.formatdate(localtime = 1)
#    msg.attach(MIMEText(text, _subtype='html', _charset='euc-kr'))
    msg.attach(MIMEText(text, _charset='euc-kr'))

#    if (attach != None):
#       part = MIMEBase("application", "octet-stream")
#       part.set_payload(open(attach, "rb").read())
#       Encoders.encode_base64(part)
#       part.add_header("Content-Disposition", "attachment; filename=\"%s\"" % os.path.basename(attach))
#       msg.attach(part)

    smtp = smtplib.SMTP(smtp_server, port)
    smtp.login(userid, passwd)
#    smtp.sendmail(from_user, cc_users, msg.as_string())
    smtp.sendmail(from_user, MAIL_ID_LIST, msg.as_string())
    smtp.close()


def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool send a sms.")
   parser.add_argument('-m', '--monthly', action='store_true')
   args = parser.parse_args()

   host_info = lib.hclib.get_host_info()
   logger.info('%s : get host information completed', GetCurFunc())

   CheckDate = datetime.date.today().strftime("%Y-%m-%d")

#   TmemoIsupSystemList = ['IVMS02','IVMS03']
   vic_system_list = ['VIC01']

   Subject = CheckDate + ' VIC 점검결과'
   ResultMerge = ''
   for System in vic_system_list:
      CsvFilePath = '/nas/HC/'
      CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
      logger.info('%s :: CsvFileName : %s', GetCurFunc(), CsvFileName)
      ResultPerSystem = get_vic_result(CsvFileName,System)
      ResultMerge = ResultMerge + '\n' + ResultPerSystem 

   MailText = ResultMerge
   logger.info('%s :: MAIL TEXT : \n%s', GetCurFunc(), MailText)
   logger.info('%s :: MAIL receive list : %s', GetCurFunc(), ', '.join(MAIL_ID_LIST))

   send_mail(Subject, MailText)

if __name__ == "__main__":
   sys.exit(main())
