#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import argparse
import csv
import smtplib
import base64
from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email.MIMEText import MIMEText
from email import Encoders
from email import Utils
from email.header import Header
from lib.cmd import *

BONDING_NIC_NAME=['bond0:1','bond1:1']
LOCAL_IP_ADDR_NIC='bond0'
#LOCAL_IP_ADDR_NIC='eth0'
MAIL_ID_LIST=['hagee@pointi.com', 'jmpark@pointi.com','ksunglok@pointi.com','bluebriz@pointi.com']
#MAIL_ID_LIST=['hagee@pointi.com']
smtp_server  = "222.122.219.59"
port = 587
userid = 'hagee@pointi.com'
passwd = '12345'


class VmsHealthCheck(HealthCheckCommand):
	def AltibaseInsertQueryExecute(self,db_query,db_param):
		from lib.altibase import AltibaseConn
		db = AltibaseConn()

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)
		db.cnxn.commit()

	def GenSmsText(self, CsvFileName, SystemNumber):
		RESULT='OK'
		ResultMerge = ''
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
					if row[3] == SystemNumber:
						if row[6] == "NOK":
							RESULT='NOK'
		except Exception as e:
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
			RESULT='NOK'
		SmeText = SystemNumber + ':' + RESULT 
		return SmeText

	def GetTmemoIsupResult(self, CsvFileName, SystemNumber):
		ResultMerge = ''
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
					logger.info('%s :: Check Item : %s', self.GetCurFunc(), row[5])
					if row[5] == 'T-MEMO ISUP 5분통계 확인':
						CheckDate = row[1]
						CheckSystem = row[3]
						CheckItem = row[5]
						TmemoIsupResult = row[7]	
						logger.info('%s :: TmemoIsupResult : \n%s', self.GetCurFunc(), TmemoIsupResult)
					else:
						logger.info('%s :: T-memo isup stat is not include in itemlist  ', self.GetCurFunc())
		except Exception as e:
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
			sys.exit()
		MailText = CheckDate + ": " + CheckSystem + ": " + CheckItem + TmemoIsupResult
		return MailText

	def GetVomoIsupResult(self, CsvFileName, SystemNumber):
		ResultMerge = ''
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
					logger.info('%s :: Check Item : %s', self.GetCurFunc(), row[5])
					if row[5] == 'VoMo ISUP 5분통계 확인':
						CheckDate = row[1]
						CheckSystem = row[3]
						CheckItem = row[5]
						TmemoIsupResult = row[7]	
						logger.info('%s :: VomoIsupResult : \n%s', self.GetCurFunc(), TmemoIsupResult)
					else:
						logger.info('%s :: Vomo isup stat is not include in itemlist  ', self.GetCurFunc())
		except Exception as e:
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
			sys.exit()
		MailText = CheckDate + ": " + CheckSystem + ": " + CheckItem + TmemoIsupResult
		return MailText

	def GetTmemoSubsResult(self, CsvFileName, SystemNumber):
		ResultMerge = ''
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
					logger.info('%s :: Check Item : %s', self.GetCurFunc(), row[5])
					if row[5] == 'T메모링 가입자수 확인' and row[4] == 'SPS02':
						CheckDate = row[1]
						CheckSystem = row[3]
						CheckHost = row[4]
						CheckItem = row[5]
						TmemoSubsResult = row[7]	
						logger.info('%s :: TmemoSubsResult : \n%s', self.GetCurFunc(), TmemoSubsResult)
		except Exception as e:
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
			sys.exit()
		MailText = CheckDate + ": " + CheckSystem + ": " + CheckItem + TmemoSubsResult
		return MailText

	def SendMail(self, subject, text):
		COMMASPACE = ", "

		from_user = 'network.support@pointi.com'
		to_user = COMMASPACE.join(MAIL_ID_LIST)
#		cc_users = 'network.support@pointi.com'
		cc_users = 'hagee@pointi.com'
#		sender = 'ivms'
		attach = ''
		msg = MIMEMultipart("alternative")
		msg["From"] = from_user
#		msg['From'] = '=?euc-kr?B?' + base64.standard_b64encode(sender) + '?=' + '<' + from_user + '>'
		msg["To"] = to_user
#		msg["Cc"] = cc_users
		msg["Subject"] = Header(s=subject, charset="euc-kr")
#		msg["Subject"] = '=?euc-kr?B?' + base64.standard_b64encode(subject) + '?='
		msg["Date"] = Utils.formatdate(localtime = 1)
#		msg.attach(MIMEText(text, _subtype='html', _charset='euc-kr'))
		msg.attach(MIMEText(text, _charset='euc-kr'))

#		if (attach != None):
#			part = MIMEBase("application", "octet-stream")
#			part.set_payload(open(attach, "rb").read())
#			Encoders.encode_base64(part)
#			part.add_header("Content-Disposition", "attachment; filename=\"%s\"" % os.path.basename(attach))
#			msg.attach(part)

		smtp = smtplib.SMTP(smtp_server, port)
		smtp.login(userid, passwd)
#		smtp.sendmail(from_user, cc_users, msg.as_string())
		smtp.sendmail(from_user, MAIL_ID_LIST, msg.as_string())
		smtp.close()


def main():
	parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool send a sms.")
	parser.add_argument('-m', '--monthly', action='store_true')
	args = parser.parse_args()

	cmd = VmsHealthCheck()

	HaStatus = cmd.GetHaStatus(BONDING_NIC_NAME)
	HostName = cmd.GetHostName(LOCAL_IP_ADDR_NIC)
	HostClass = cmd.GetHostClass(LOCAL_IP_ADDR_NIC)
	SystemNumber = cmd.GetSystemNumber(LOCAL_IP_ADDR_NIC)

	CheckDate = datetime.date.today().strftime("%Y-%m-%d")
	logger.info("%s :: System Infomation : %s, %s, %s, %s", cmd.GetCurFunc(), SystemNumber, HostClass, HostName, HaStatus)
#	if not HaStatus == 'ACTIVE':
#		logger.info('%s :: This System is not ACTIVE, sys.exit()', cmd.GetCurFunc())
#		sys.exit()

	SystemList = ['IVMS01','IVMS02','IVMS03','IVMS04']
	TmemoIsupSystemList = ['IVMS02','IVMS03']
	VomoIsupSystemList = ['IVMS04']
#	TmemoIsupSystemList = ['IVMS02']
	TmemoSubsSystemList = ['IVMS03']

	Subject = CheckDate + ' VoMo, T메모링 점검결과'
	ResultMerge = ''
#	for System in SystemList:
#		CsvFilePath = '/nas/HC/'
#		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
#		ResultPerSystem = cmd.GenSmsText(CsvFileName,System)
#		ResultMerge = ResultMerge + '\n' + ResultPerSystem 
	for System in VomoIsupSystemList:
		CsvFilePath = '/nas/HC/'
		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
		logger.info('%s :: CsvFileName : %s', cmd.GetCurFunc(), CsvFileName)
		ResultPerSystem = cmd.GetVomoIsupResult(CsvFileName,System)
		ResultMerge = ResultMerge + '\n' + ResultPerSystem 

	for System in TmemoIsupSystemList:
		CsvFilePath = '/nas/HC/'
		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
		logger.info('%s :: CsvFileName : %s', cmd.GetCurFunc(), CsvFileName)
		ResultPerSystem = cmd.GetTmemoIsupResult(CsvFileName,System)
		ResultMerge = ResultMerge + '\n' + ResultPerSystem 

	for System in TmemoSubsSystemList:
		CsvFilePath = '/nas/HC/'
		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
		logger.info('%s :: CsvFileName : %s', cmd.GetCurFunc(), CsvFileName)
		ResultPerSystem = cmd.GetTmemoSubsResult(CsvFileName,System)
		ResultMerge = ResultMerge + '\n' + ResultPerSystem 

#	MailText = Subject + ResultMerge
	MailText = ResultMerge
	logger.info('%s :: MAIL TEXT : \n%s', cmd.GetCurFunc(), MailText)
	logger.info('%s :: MAIL receive list : %s', cmd.GetCurFunc(), ', '.join(MAIL_ID_LIST))

	cmd.SendMail(Subject, MailText)

if __name__ == "__main__":
	sys.exit(main())
