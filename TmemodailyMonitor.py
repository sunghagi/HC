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
#MAIL_ID_LIST=['hagee@pointi.com', 'jmpark@pointi.com', 'bluebriz@pointi.com']
#MAIL_ID_LIST=['hagee@pointi.com']
MAIL_ID_LIST=['network.support@pointi.com']
smtp_server  = "222.122.219.59"
port = 587
userid = 'hagee@pointi.com'
passwd = '12345'


class VmsHealthCheck(HealthCheckCommand):
	def OdbcDBQueryExecute(self,DSN,db_query,db_param,col_index):
		from lib.odbc_conn import odbcConn
		db = odbcConn(DSN)
		db._GetConnect()

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)
		row = db.cursor.fetchone()

		return row[col_index]

	def GetKoreanWeekday(self):
		DayOfTheWeek = datetime.datetime.today().weekday()
# 		Mon = 0, Tue = 1, Wed = 2, Thu = 3, Fri = 4, Sat = 5, Sun = 6
		if DayOfTheWeek == 0:
			return "월"
		elif DayOfTheWeek == 1:
			return "화"
		elif DayOfTheWeek == 2:
			return "수"
		elif DayOfTheWeek == 3:
			return "목"
		elif DayOfTheWeek == 4:
			return "금"
		elif DayOfTheWeek == 5:
			return "토"
		elif DayOfTheWeek == 6:
			return "일"

	def NumWithCommas(self, value):
		ValueWithCommas = "{:,}".format(value)
		return ValueWithCommas

	def GetTmemoSubsResult(self,DSN,userType):
#		HostClass = self.GetHostClass(LOCAL_IP_ADDR_NIC)
#		HaStatus = self.GetHaStatus(BONDING_NIC_NAME)
#		SystemNumber = self.GetSystemNumber(LOCAL_IP_ADDR_NIC)

		db_query = """
		select count(*) as UserCount from subscribers where userType = ?
		"""
		db_param = userType
		SubsResult=self.OdbcDBQueryExecute(DSN,db_query,db_param,0)

		return SubsResult

	def GetScpStatResult(self,DSN,StatTime):
		db_query = """
		select TOTAL_CNT from ST_SCP_HOUR where STATTIME = ?;
		"""
		db_param = [StatTime]
		TmemoScpStat=self.OdbcDBQueryExecute(DSN,db_query,db_param,0)
#		logger.info('%s :: TmemoIsupStatResult : %s', self.GetCurFunc(),TmemoIsupStatResult)
		return TmemoScpStat

	def GetScpStatResult2(self,DSN,StatTime):
		db_query = """
		select SUCC_CNT from ST_SCP_HOUR where STATTIME = ?;
		"""
		db_param = [StatTime]
		TmemoScpStat=self.OdbcDBQueryExecute(DSN,db_query,db_param,0)
#		logger.info('%s :: TmemoIsupStatResult : %s', self.GetCurFunc(),TmemoIsupStatResult)
		return TmemoScpStat

	def GetIsupStatResult(self,DSN,StatTime):
		db_query = """
		SELECT SUM(IAM_COUNT)
		FROM
		ST_ISUP_HOUR 
		WHERE STATTIME = ? AND CALLTYPE=8
		GROUP BY STATTIME;
		"""
		db_param = [StatTime]
		TmemoIsupStat=self.OdbcDBQueryExecute(DSN,db_query,db_param,0)
#		logger.info('%s :: TmemoIsupStatResult : %s', self.GetCurFunc(),TmemoIsupStatResult)
		return TmemoIsupStat

	def GetSipStatResult(self,DSN,StatTime):
		db_query = """
		SELECT SUM(REQUEST)
		FROM
		ST_SIPCALL_HOUR WHERE STATTIME = ?
		GROUP BY STATTIME;
		"""
		db_param = [StatTime]
		TmemoSipStat=self.OdbcDBQueryExecute(DSN,db_query,db_param,0)
#		logger.info('%s :: TmemoIsupStatResult : %s', self.GetCurFunc(),TmemoIsupStatResult)
		return TmemoSipStat

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

#	CheckDate = datetime.date.today().strftime("%Y-%m-%d")

	ResultMerge = ''

	NormalSubs = cmd.GetTmemoSubsResult('DSN=AltiTMR',1)
	ExperienceSubs = cmd.GetTmemoSubsResult('DSN=AltiTMR',2)
	PremiumSubs = cmd.GetTmemoSubsResult('DSN=AltiTMR',3)
	TotalSubs = NormalSubs + ExperienceSubs + PremiumSubs
	TmemoSubsStr = "- 총가입자(프리미엄) : %s(%s)명" % ( cmd.NumWithCommas(TotalSubs), cmd.NumWithCommas(PremiumSubs) )

#	today = datetime.date.today().strftime("%Y-%m-%d")
#	yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime("%Y-%m-%d")
#	Weekago = (datetime.date.today() - datetime.timedelta(7)).strftime("%Y-%m-%d")
	StatTime = (datetime.datetime.now() - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:00:00")
	WeekagoStatTime = (datetime.datetime.now() - datetime.timedelta(days=7,hours=1)).strftime("%Y-%m-%d %H:00:00")

	CurrentTime = datetime.datetime.now()
	CurrentWeekday = cmd.GetKoreanWeekday()
#	if CurrentTime.hour >= 12 and CurrentTime.hour <= 17:
#		StatTime=today + ' ' + '11:00:00'
#		WeekagoStatTime=Weekago + ' ' + '11:00:00'
#	elif CurrentTime.hour >= 9 and CurrentTime.hour <= 11:
#		StatTime=today + ' ' + '8:00:00'
#		WeekagoStatTime=Weekago + ' ' + '8:00:00'
#	else:
#		StatTime=today + ' ' + '17:00:00'
#		WeekagoStatTime=Weekago + ' ' + '17:00:00'
	logger.info('%s :: StatTime : %s', cmd.GetCurFunc(), StatTime)

	Subject= "%s/%s(%s) T메모링 %s시 시스템통계" % (CurrentTime.month,CurrentTime.day,CurrentWeekday,CurrentTime.hour)

	TmemoIsupStatVMS2 = cmd.GetIsupStatResult('DSN=mysql_ivms2',StatTime)
	TmemoIsupStatVMS3 = cmd.GetIsupStatResult('DSN=mysql',StatTime)
	TmemoIsupStatTotalCount = TmemoIsupStatVMS2 + TmemoIsupStatVMS3
	TmemoIsupStatTotalCPS = round(float(TmemoIsupStatTotalCount) / 3600.0, 3)
	TmemoIsupStr = "- ISUP : %s/150CPS" % (TmemoIsupStatTotalCPS) 

	ScpStatHourTodayCount = cmd.GetScpStatResult('DSN=mysql',StatTime)
	ScpStatHourTodaySuccessCount = cmd.GetScpStatResult2('DSN=mysql',StatTime)
	ScpStatHourTodaySuccessRate = round(float(ScpStatHourTodaySuccessCount) / float(ScpStatHourTodayCount) * 100,2)

	ScpStatHourTodayCps = ScpStatHourTodayCount / 3600
	ScpStatHourTodayUsage = round(ScpStatHourTodayCps / 500.0, 2) * 100
	logger.info('%s :: ScpStatHourTodayCps : %s', cmd.GetCurFunc(), ScpStatHourTodayCps)
	logger.info('%s :: ScpStatHourTodayUsage : %s', cmd.GetCurFunc(), ScpStatHourTodayUsage)
	ScpStatHourWeekagoCount = cmd.GetScpStatResult('DSN=mysql',WeekagoStatTime)

	TmemoTrafficStr4 = "- 성공율:%d%%" % (ScpStatHourTodaySuccessRate)
	TmemoTrafficStr1 = "- 트레픽(전주):\n  %s(%s)호" % ( cmd.NumWithCommas(ScpStatHourTodayCount), cmd.NumWithCommas(ScpStatHourWeekagoCount) )
	TmemoTrafficStr2 = "- 용량대비 SCP %s%%(%sCPS) 사용" % ( ScpStatHourTodayUsage, ScpStatHourTodayCps )
	TmemoTrafficStr3 = "- SCP : %s/500CPS" % (ScpStatHourTodayCps)

	SipStatHourTodayCount = cmd.GetSipStatResult('DSN=mysql',StatTime)
	SipStatHourTodayCps = round(SipStatHourTodayCount / 3600,1)
	SipStatHourTodayUsage = round(SipStatHourTodayCps / 256.0, 2) * 100
	TmemoSipTrafficStr = "- SIP : %s/256CPS" % (SipStatHourTodayCps)
	TmemoTrafficStr5 = "- 용량대비 SIP %s%%(%sCPS) 사용" % ( SipStatHourTodayUsage, SipStatHourTodayCps )

	ResultMerge = ResultMerge + Subject
	ResultMerge = ResultMerge + '\n' + TmemoSubsStr
	ResultMerge = ResultMerge + '\n' + TmemoTrafficStr4
	ResultMerge = ResultMerge + '\n' + TmemoTrafficStr1
	ResultMerge = ResultMerge + '\n' + TmemoTrafficStr2
	ResultMerge = ResultMerge + '\n' + TmemoTrafficStr5
	ResultMerge = ResultMerge + '\n\n' + "※ 기타 용량"
	ResultMerge = ResultMerge + '\n' + TmemoTrafficStr3
	ResultMerge = ResultMerge + '\n' + TmemoSipTrafficStr
	ResultMerge = ResultMerge + '\n' + TmemoIsupStr

#	MailText = Subject + ResultMerge
	MailText = ResultMerge
	logger.info('%s :: MAIL TEXT : \n%s', cmd.GetCurFunc(), MailText)
	logger.info('%s :: MAIL receive list : %s', cmd.GetCurFunc(), ', '.join(MAIL_ID_LIST))

	cmd.SendMail(Subject, MailText)

if __name__ == "__main__":
	sys.exit(main())
