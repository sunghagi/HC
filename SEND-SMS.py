#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import datetime
import argparse
import ConfigParser
import csv
import time

from lib.cmd import *

SendSmsConfigPath='/nas/HC/config/sendsms.cfg'
BONDING_NIC_NAME=['bond0:1','bond1:1']

SITE = 'TB'
#SITE = 'BNDN'

if SITE == 'TB':
	LOCAL_IP_ADDR_NIC='eth0'
	SystemList = ['IVMS03']
else :
	LOCAL_IP_ADDR_NIC='bond0'
	SystemList = ['IVMS01','IVMS02','IVMS03','IVMS04']

class VmsHealthCheck(HealthCheckCommand):
	def AltibaseInsertQueryExecute(self,db_query,db_param):
		from lib.altibase import AltibaseConn
		db = AltibaseConn('DSN=odbc_local')
		db._GetConnect()

		if db_param == '':
			db.cursor.execute(db_query)
		else :
			db.cursor.execute(db_query, db_param)
		db.cnxn.commit()

	def GenHcResultSmsText(self, CsvFileName, SystemNumber):
		RESULT='OK'
		ResultMerge = ''
#		logger.info('%s :: CsvFileName : %s, SystemNumber : %s', self.GetCurFunc(), CsvFileName, SystemNumber)
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
#					logger.info('%s :: SystemNumber : %s, %s result : %s', self.GetCurFunc(), row[3], row[5], row[6])
#					if row[3] == SystemNumber and row[6] == "NOK":
					if row[6] == "NOK":
						RESULT='NOK'
		except Exception as e:
			logger.info('%s :: result : %s', self.GetCurFunc(), ', '.join(row))
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
			RESULT='NOK'
		SmeText = SystemNumber + ': ' + RESULT 
		return SmeText

	def GetHcPeriod(self, CsvFileName, SystemNumber):
#     logger.info('%s :: CsvFileName : %s, SystemNumber : %s', self.GetCurFunc(), CsvFileName, SystemNumber)
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
					Period = row[2]
					logger.info('%s :: HC Period : %s', self.GetCurFunc(), Period)
					if not Period == '':
						break
		except Exception as e:
			logger.info('%s :: result : %s', self.GetCurFunc(), ', '.join(row))
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
			Period='DAILY'
		return Period

	def GetIsupStat(self, CsvFileName, SystemNumber):
		if SITE == 'TB':
			return 0

#		RESULT='OK'
#		ResultList = [index, CheckDate, SystemNumber, HostName, ItemDesc, CmdResult, ReturnString]
		ItemDescList = ['ISUP ��� Ȯ��','T-MEMO ISUP 5����� Ȯ��']

		VmsIsupResult = ''
		TmemoIsupResult = ''
		try:
			with open(CsvFileName, 'rt') as f:
				reader = csv.reader(f, delimiter=',')
				for row in reader:
					if row[4] == 'OMP' and row[5] == ItemDescList[0]:
						VmsIsupResult = row[7]
						for line in VmsIsupResult.splitlines(True):
							StatData=re.match('^\d.*', line)
							if StatData:
								RawData = StatData.group().split()
								VmsTime = RawData[0]
								VmsIam = RawData[2]
								VmsCps = RawData[3]
					elif row[4] == 'OMP' and row[5] == ItemDescList[1]:
						TmemoIsupResult = row[7]
						for line in TmemoIsupResult.splitlines(True):
							StatData=re.match('^\d.*', line)
							if StatData:
								RawData = StatData.group().split()
								TmemoTime = RawData[0]
								TmemoIam = RawData[2]
								TmemoCps = RawData[3]
					else:
						IsupResult = 0
		except Exception as e:
			logger.info('%s :: result : %s', self.GetCurFunc(), ', '.join(row))
			logger.exception('%s :: CSV file handle error : %s',self.GetCurFunc(), e)
#			RESULT='NOK'

		logger.info('%s :: TmemoIsupResult: %s', self.GetCurFunc(), TmemoIsupResult)
		if IsupResult :
			logger.info('%s :: Isup result not include', self.GetCurFunc())
			return 0
#		if SystemNumber == 'IVMS01':
#			SystemNumber = '#1'
#		elif SystemNumber == 'IVMS02':
#			SystemNumber = '#2'
#		elif SystemNumber == 'IVMS03':
#			SystemNumber = '#3'
#		elif SystemNumber == 'IVMS04':
#			SystemNumber = '#4'

		if 'TmemoIam' in locals():
			tmpl = "%s : VMS %s(%s), Tmemo %s(%s)"
			SmsText = tmpl % ( SystemNumber, VmsIam, VmsCps, TmemoIam, TmemoCps )
		else:
			tmpl = "%s : VMS %s(%s)"
			SmsText = tmpl % ( SystemNumber, VmsIam, VmsCps )

		return SmsText

	def SendSms(self, Phoneid, Message):
		# msgtype : 13 - OMC Ticket
		pStmt = """
		INSERT INTO gipsmsinfo(serialno, phoneid, msgtype, callbackid, message, created)
		VALUES(seq_gipsmsinfo_serialno.NEXTVAL, ?, '13', '0112008585', ?, SYSDATE)
		"""
		db_param = [Phoneid,Message]
		self.AltibaseInsertQueryExecute(pStmt,db_param)

	def GetRecvSmsPhoneIdListFromConf(self, SectionName):
		SendSmsConfig = ConfigParser.RawConfigParser()
		SendSmsConfig.read(SendSmsConfigPath)

		logger.info('Get Config Value Start ===================')
		SectionName = SectionName
		RecvPhoneidItemsList=SendSmsConfig.items(SectionName)
		RecvPhoneNumList=[]
		for RecvPhoneidItems in RecvPhoneidItemsList:
			RecvPhoneNumList.append(RecvPhoneidItems[1])
		logger.info('%s / Phoneid List : %s', SectionName, RecvPhoneNumList)

		return RecvPhoneNumList

def main():
	parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool send a sms.")
	parser.add_argument('-m', '--monthly', action='store_true')
	args = parser.parse_args()

	cmd = VmsHealthCheck()

	HaStatus = cmd.GetHaStatus(BONDING_NIC_NAME)
	HostName = cmd.GetHostName(LOCAL_IP_ADDR_NIC)
	HostClass = cmd.GetHostClass(LOCAL_IP_ADDR_NIC)

	CheckDate = datetime.date.today().strftime("%Y-%m-%d")
	logger.info("%s :: System Infomation : %s, %s, %s", cmd.GetCurFunc(), HostClass, HostName, HaStatus)
#	HaStatus = 'ACTIVE'
	if not HaStatus == 'ACTIVE' and not SITE == 'TB':
		logger.info('%s :: This System is not ACTIVE, sys.exit()', cmd.GetCurFunc())
		sys.exit()

	IsupStatRecvPhoneNumList = cmd.GetRecvSmsPhoneIdListFromConf('isup stat')
	HcResultRecvPhoneNumList = cmd.GetRecvSmsPhoneIdListFromConf('hc result')

	IsupStatResultMerge = ''
	for System in SystemList:
		CsvFilePath = '/nas/HC/'
		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
		IsupStatResultPerSystem = cmd.GetIsupStat(CsvFileName,System)
		if not IsupStatResultPerSystem :
			logger.info('%s not include IsupStat result', System)
			break
		SmsTextHead = CheckDate + ' �ֹ��� 5�� ȣ���(CPS)'
		SmsText = SmsTextHead + '\n' + IsupStatResultPerSystem
		logger.info('%s :: %s SMS TEXT : \n%s', cmd.GetCurFunc(), System, SmsText)
		logger.info('%s :: SMS receive list : %s', cmd.GetCurFunc(), ', '.join(IsupStatRecvPhoneNumList))
		for PhoneId in IsupStatRecvPhoneNumList:
			cmd.SendSms(PhoneId, SmsText)

	HcResultMerge = ''
	for System in SystemList:
		CsvFilePath = '/nas/HC/'
		CsvFileName = CsvFilePath+CheckDate.replace('-','')+'_'+System+'.csv'
		ResultPerSystem = cmd.GenHcResultSmsText(CsvFileName,System)
		HcResultMerge = HcResultMerge + '\n' + ResultPerSystem 

	HcPeriodCsv = cmd.GetHcPeriod(CsvFileName,System)
	if HcPeriodCsv == 'DAILY':
		HcPeriod = '����'
	elif HcPeriodCsv == 'WEEKLY':
		HcPeriod = '�ְ�'
	elif HcPeriodCsv == 'MONTHLY':
		HcPeriod = '����'
	else :
		HcPeriod = '����'
		
	SmsTextHead = CheckDate + ' ' + HcPeriod + '���� ���'
	SmsText = SmsTextHead + HcResultMerge
	logger.info('%s :: SMS TEXT : \n%s', cmd.GetCurFunc(), SmsText)
	logger.info('%s :: SMS receive list : %s', cmd.GetCurFunc(), ', '.join(HcResultRecvPhoneNumList))

	for PhoneId in HcResultRecvPhoneNumList:
		cmd.SendSms(PhoneId, SmsText)

if __name__ == "__main__":
	sys.exit(main())