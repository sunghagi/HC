#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
from daemon import runner
from daemon.pidfile import PIDLockFile
from lockfile import LockTimeout

import os
import sys
import time
import datetime
import glob
import ConfigParser

import inspect
import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import TimedRotatingFileHandler

LOG_FILE_PATH='/nas/HC/log/dellog.log'
DellogConfigPath='/nas/HC/config/dellog.cfg'
SCHEDULE_TIME='13:00'


class DaemonLogger(object):
   def __init__(self):
#      self.name = name
      self.logger = logging.getLogger(__name__)
      self.logger.setLevel(logging.INFO)
      '''
      self.hdlr = RotatingFileHandler(
         LOG_FILE_PATH,
         maxBytes= 1024 * 1024 * 10,
         backupCount = 5
      )
      '''
      self.hdlr = TimedRotatingFileHandler(
         LOG_FILE_PATH,
         when='midnight',
         backupCount = 30 
      )
#      FORMAT = logging.Formatter('%(asctime)-15s [%(levelname)-5s] %(module)s : %(message)s')
      FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)-5s] %(message)s', \
                                 datefmt='%H:%M:%S')
      self.hdlr.suffix = "%m%d"
      self.hdlr.setFormatter(FORMAT)
      if not self.logger.handlers:
         self.logger.addHandler(self.hdlr)


class App():
   def __init__(self):
      self.stdin_path = '/dev/null'
      self.stdout_path = '/dev/tty'
      self.stderr_path = '/dev/tty'
#      self.pidfile_path = '/nas/HC/log/dellog.pid'
      self.pidfile_path = '/tmp/dellog.pid'
      self.pidfile_timeout = 5
   def run(self):
      logger = DaemonLogger()
      while True:
         dateSTR = datetime.datetime.now().strftime("%H:%M" )
         # Main code goes here ... 
         if dateSTR == (SCHEDULE_TIME): 
            logger.logger.info('Now(%s) schedule time.. Start!! ', dateSTR)
            main()
            time.sleep(60)
         else:
            logger.logger.info('%s not running time.. sleeping 60 Secs', dateSTR)
            time.sleep(60)
            pass

def GetCurFunc():
   return inspect.stack()[1][3]

def ConfigFileCheck(ConfigPath):
   import os.path
   if not os.path.isfile(ConfigPath):
      return False
   else:
      return True

def main():
#   logger = DaemonLogger('root')
   logger = DaemonLogger()
   logger.logger.info('dellog.py Start ===================')
   doesConfigFile = ConfigFileCheck(DellogConfigPath)
   if not doesConfigFile:
      logger.logger.info('Dellog Configuration File:%s does not exist !!', DellogConfigPath)
      logger.logger.info('Dellog Exit !!')
      sys.exit()

   DellogConfig = ConfigParser.RawConfigParser()
   DellogConfig.read(DellogConfigPath)
   DellogSectionNameList = DellogConfig.sections()

   for SectionName in DellogSectionNameList:
      LogPath=DellogConfig.get(SectionName, 'log-path')
      logger.logger.info('[ %-5s ] log-path : %s', SectionName, LogPath)

      try:
         LogFileExtention=DellogConfig.get(SectionName, 'log-extention')
      except ConfigParser.NoOptionError:
         logger.logger.info("No option 'log-extention' in section: %s", SectionName)
         logger.logger.info('sys.exit')
         sys.exit()

      try:
         RetentionPeriodDay=DellogConfig.get(SectionName, 'retention-period')
      except ConfigParser.NoOptionError:
         logger.logger.info("No option 'retention-period' in section: %s", SectionName)
         logger.logger.info('sys.exit')
         sys.exit()

      logger.logger.info('[ %-5s ] log-extention : %s , retention-period : %s Days', \
                          SectionName, LogFileExtention, RetentionPeriodDay)

      RetentionPeriodSec=int(RetentionPeriodDay)*24*60*60
      RetentionPeriodAgo=time.time() - RetentionPeriodSec

      LogfileList = glob.glob(LogPath+'/*.'+LogFileExtention)
#     !!!! insert check LogPath
#     os.chdir(LogPath)
#     for LogFile in os.listdir('.'):
      for LogFile in LogfileList:
         StatResult=os.stat(LogFile)
         mtime=StatResult.st_mtime
#        print "%s : %s : %s" % (somefile, mtime, RetentionPeriodAgo)
         if mtime < RetentionPeriodAgo:
            try:
               os.unlink(LogFile) # uncomment only if you are sure
               logger.logger.info('%s :: Remove Log File : %s', GetCurFunc(), LogFile)
            except:
               logger.logger.info('Remove Log File Failure : %s', GetCurFunc(), LogFile)
               sys.exit()
   logger.logger.info('dellog.py End   ===================')

if __name__ == "__main__":
#   logger = DaemonLogger("dellogLog")
   logger = DaemonLogger()

   app = App()
   daemon_runner = runner.DaemonRunner(app)
   daemon_runner.daemon_context.files_preserve = [logger.hdlr.stream.fileno()]
   try:
      daemon_runner.do_action()
   except LockTimeout:
      pidLockfile = PIDLockFile(app.pidfile_path)
      if pidLockfile.is_locked():
         print "dellog running already (pid: %s)" % ( pidLockfile.read_pid() )
         logger.logger.info("dellog running already (pid: %s)",pidLockfile.read_pid() )
         logger.logger.info('sys.exit')
         sys.exit()
   except runner.DaemonRunnerStopFailureError:
      print "dellog not running !!"
      sys.exit()
