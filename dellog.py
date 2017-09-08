#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import os
import sys
import time
import datetime
import glob
import shutil
import ConfigParser

from lib.vms_hc import *

#LOG_FILE_PATH='/nas/HC/log/dellog.log'
DellogConfigPath='/nas/HC/config/dellog.cfg'
SCHEDULE_TIME='17:51'

def ConfigFileCheck(ConfigPath):
   import os.path
   if not os.path.isfile(ConfigPath):
      return False
   else:
      return True

def main():
   logger.info('dellog.py Start ===================')
   doesConfigFile = ConfigFileCheck(DellogConfigPath)
   if not doesConfigFile:
      logger.info('Dellog Configuration File:%s does not exist !!', DellogConfigPath)
      logger.info('Dellog Exit !!')
      sys.exit()

   DellogConfig = ConfigParser.RawConfigParser()
   DellogConfig.read(DellogConfigPath)
   DellogSectionNameList = DellogConfig.sections()

   for SectionName in DellogSectionNameList:
      LogPath=DellogConfig.get(SectionName, 'log-path')
      logger.info('[ %-5s ] log-path : %s', SectionName, LogPath)

      try:
         log_type=DellogConfig.get(SectionName, 'log-type')
      except ConfigParser.NoOptionError:
         logger.info("No option 'log-type' in section: %s", SectionName)
         log_type="None"

      try:
         LogFileExtention=DellogConfig.get(SectionName, 'log-extention')
      except ConfigParser.NoOptionError:
         logger.info("No option 'log-extention' in section: %s", SectionName)
         logger.info('sys.exit')
         sys.exit()

      try:
         RetentionPeriodDay=DellogConfig.get(SectionName, 'retention-period')
      except ConfigParser.NoOptionError:
         logger.info("No option 'retention-period' in section: %s", SectionName)
         logger.info('sys.exit')
         sys.exit()

      logger.info('[ %-5s ] log-type : %s, log-extention : %s , retention-period : %s Days', \
                          SectionName, log_type, LogFileExtention, RetentionPeriodDay)

      RetentionPeriodSec=int(RetentionPeriodDay)*24*60*60
      RetentionPeriodAgo=time.time() - RetentionPeriodSec

      if log_type == 'file':
         LogfileList = glob.glob(LogPath+'/*.'+LogFileExtention)
      elif log_type == 'dir':
         LogfileList = glob.glob(LogPath+'/'+LogFileExtention)

      for LogFile in LogfileList:
         logger.info('%s :: Log File : %s', GetCurFunc(), LogFile)
         StatResult=os.stat(LogFile)
         mtime=StatResult.st_mtime
         if mtime < RetentionPeriodAgo:
            try:
               if log_type == 'file':
                  os.unlink(LogFile)
               if log_type == 'dir':
                  shutil.rmtree(LogFile, ignore_errors=True)
               logger.info('%s :: Removed Log File : %s', GetCurFunc(), LogFile)
            except Exception as e:
               logger.info('%s :: Remove Log File Failure : %s', GetCurFunc(), e)
   logger.info('dellog.py End   ===================')

if __name__ == "__main__":
   main()
