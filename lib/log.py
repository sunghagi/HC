#!/nas/HC/PYTHON2.7/bin/python -tt
import sys
import inspect
import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import TimedRotatingFileHandler

LOG_FILE_PATH='/nas/HC/log/hc.log'

def HcLogger():
   logger = logging.getLogger(__name__)
   logger.setLevel(logging.INFO)
   '''
   hdlr = RotatingFileHandler(
      LOG_FILE_PATH,
      maxBytes= 1024 * 1024 * 10,
      backupCount = 5
   )
   '''
   hdlr = TimedRotatingFileHandler(
      LOG_FILE_PATH,
      when='midnight',
      backupCount = 30
   )
   FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)-5s] %(message)s', \
                              datefmt='%H:%M:%S')
   hdlr.suffix = "%m%d"
   hdlr.setFormatter(FORMAT)
   if not logger.handlers:
      logger.addHandler(hdlr)

   return logger

def hcLogger(name):
   FORMAT = logging.Formatter('%(asctime)-15s [%(levelname)-5s] %(module)s : %(message)s')

   hdlr = logging.FileHandler(LOG_FILE_PATH)
   hdlr.setFormatter(FORMAT)

   logger = logging.getLogger(name)
   logger.addHandler(hdlr)
   logger.setLevel(logging.INFO)
#  logger.setLevel(logging.DEBUG)

   return logger

def GetCurFunc():
   return inspect.stack()[1][3]
