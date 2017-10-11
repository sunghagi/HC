#!/nas/HC/PYTHON2.7/bin/python -tt
from os import path
import inspect
import logging
from logging.handlers import RotatingFileHandler
from logging.handlers import TimedRotatingFileHandler

#LOG_FILE_PATH='/nas/HC/log/hc.log'
LOG_FILE_PATH = path.join(path.abspath(path.dirname(__file__)), \
												'../log', 'hc.log')

def HcLogger():
    FORMAT = logging.Formatter('%(asctime)s.%(msecs)03d [%(levelname)-5s] %(message)s', \
                              datefmt='%H:%M:%S')
    '''
    hdlr = RotatingFileHandler(
       LOG_FILE_PATH,
       maxBytes= 1024 * 1024 * 10,
       backupCount = 5
    )
    '''
    try:
       logger = logging.getLogger(__name__)
       logger.setLevel(logging.INFO)
 
       hdlr = TimedRotatingFileHandler(
          LOG_FILE_PATH,
          when='midnight',
          backupCount = 30
       )
       hdlr.suffix = "%m%d"
       hdlr.setFormatter(FORMAT)
    except Exception as e:
       logger = logging.getLogger(__name__)
       logger.setLevel(logging.INFO)
 
       hdlr = logging.StreamHandler()
       hdlr.setFormatter(FORMAT)
 
    if not logger.handlers:
       logger.addHandler(hdlr)
 
    return logger
 										

def GetCurFunc():
    return inspect.stack()[1][3]
