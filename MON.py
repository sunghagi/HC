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
#LOCAL_IP_ADDR_NIC='bond0'
LOCAL_IP_ADDR_NIC='eth0'
#MAIL_ID_LIST=['hagee@pointi.com', 'jmpark@pointi.com', 'bluebriz@pointi.com']
MAIL_ID_LIST=['hagee@pointi.com']
smtp_server  = "222.122.219.59"
port = 587
userid = 'hagee@pointi.com'
passwd = '12345'


class VmsHealthCheck(HealthCheckCommand):
	def AltibaseQueryExecute(self,DSN,db_query,db_param):
		from lib.altibase import AltibaseConn
#		db = AltibaseConn('DSN=memoring_local')
		db = AltibaseConn(DSN)
		db._GetConnect()

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)
		row = db.cursor.fetchone()

		return row[0]

	def MysqlQueryExecute(self,DSN,db_query,db_param):
		from lib.altibase import AltibaseConn
#		db = AltibaseConn('DSN=mysql')
		db = AltibaseConn(DSN)
		db._GetConnect()

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)
		row = db.cursor.fetchone()

		return row[3]

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


	def GetTmemoSubsResult(self,DSN,userType):
		HostClass = self.GetHostClass(LOCAL_IP_ADDR_NIC)
		HaStatus = self.GetHaStatus(BONDING_NIC_NAME)
		SystemNumber = self.GetSystemNumber(LOCAL_IP_ADDR_NIC)

		if SystemNumber == "IVMS03" and HostClass == "SPS" and HaStatus == 'STANDBY':
			db_query = """
			select count(*) as UserCount from subscribers where userType = ?
			"""
			db_param = userType
			SubsResult=self.AltibaseQueryExecute(DSN,db_query,db_param)

			return SubsResult
		else:
			print " This system is " + SystemNumber + ", " + HostClass + " ACTIVE Side "
			print " T-Memoring Subscribers Count is available in iVMS#3 STANDBY Side "

	def GetIsupStatResult(self,DSN):
#		yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
		today = datetime.date.today().strftime("%Y-%m-%d %H:%M:%S")
		StatStartTime=today + ' ' + '11:00:00'
		StatEndTime=today + ' ' + '11:59:59'

		db_query = """
		select t.STATTIME, t.IAM, t.CPS, t.AVGHT, t.CPS*t.AVGHT/31 AS USED_E1
		from
		(
		select DATE_FORMAT(STATTIME, '%Y-%m-%d %H:%i') AS STATTIME,
		SUM(IAM_COUNT) AS IAM ,
		ROUND(SUM(IAM_COUNT)/5/60,1) AS CPS,
		IF(SUM(IAM_COUNT)=0, 0 , ROUND(SUM(IAM_COUNT*AVGHOLDINGTIME)/SUM(IAM_COUNT),2)) AS AVGHT
		from ST_ISUP_5MIN
		where ( STATTIME between ? and ? ) and CALLTYPE=8
		group by STATTIME 
		order by sum(IAM_COUNT) desc limit 0,1) t;
		"""
		db_param = [StatStartTime,StatEndTime]
#		self.set_db_label('통계시간','IAM','CPS','AVGHOLDINGTIME','USED_E1')
		TmemoIsupStatResult=self.MysqlQueryExecute(DSN,db_query,db_param)
#           logger.info('%s :: TmemoIsupStatResult : %s', self.GetCurFunc(),TmemoIsupStatResult)
		return TmemoIsupStatResult


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

	Subject = CheckDate + ' T메모링 점검결과'
	ResultMerge = ''

#	for System in TmemoIsupSystemList:
#		CsvFilePath = '/nas/HC/'
#		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
#		logger.info('%s :: CsvFileName : %s', cmd.GetCurFunc(), CsvFileName)
#		ResultPerSystem = cmd.GetTmemoIsupResult(CsvFileName,System)
#		ResultMerge = ResultMerge + '\n' + ResultPerSystem 

	NormalSubs = cmd.GetTmemoSubsResult('DSN=memoring_local',1)
	ExperienceSubs = cmd.GetTmemoSubsResult('DSN=memoring_local',2)
	PremiumSubs = cmd.GetTmemoSubsResult('DSN=memoring_local',3)
	TotalSubs = NormalSubs + ExperienceSubs + PremiumSubs
	TmemoSubsStr = "총가입자(프리미엄) : %d(%d) 명" % ( TotalSubs, PremiumSubs )
	TmemoIsupStat = cmd.GetIsupStatResult('DSN=mysql')
	TmemoIsupStr = "- ISUP : %d/150CPS" % (TmemoIsupStat) 

	ResultMerge = ResultMerge + '\n' + TmemoSubsStr
	ResultMerge = ResultMerge + '\n' + "※ 기타 용량"
	ResultMerge = ResultMerge + '\n' + TmemoIsupStr

	print TmemoSubsStr

#	MailText = Subject + ResultMerge
	MailText = ResultMerge
	logger.info('%s :: MAIL TEXT : \n%s', cmd.GetCurFunc(), MailText)
	logger.info('%s :: MAIL receive list : %s', cmd.GetCurFunc(), ', '.join(MAIL_ID_LIST))

	cmd.SendMail(Subject, MailText)

if __name__ == "__main__":
	sys.exit(main())
