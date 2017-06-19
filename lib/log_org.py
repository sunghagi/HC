#!/nas/HC/PYTHON2.7/bin/python -tt
import sys
import inspect
import logging

LOG_FILE_PATH='/nas/HC/log/hc.log'

def hcLogger(name):
	FORMAT = logging.Formatter('%(asctime)-15s [%(levelname)-5s] %(module)s : %(message)s')

	hdlr = logging.FileHandler(LOG_FILE_PATH)
	hdlr.setFormatter(FORMAT)

	logger = logging.getLogger(name)
	logger.addHandler(hdlr)
	logger.setLevel(logging.INFO)
#	logger.setLevel(logging.DEBUG)

	return logger

def GetCurFunc():
	return inspect.stack()[1][3]
