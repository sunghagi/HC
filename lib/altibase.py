#!/nas/HC/PYTHON2.7/bin/python -tt
import sys
import pyodbc

class AltibaseConn(object):
	def __init__(self, dsn):
		self.DSN = dsn


	def _GetConnect(self):
		''' Connect to the Altibase '''
		self.cnxn = pyodbc.connect(self.DSN)
		self.cursor = self.cnxn.cursor()

	def print_value(self,col_count):
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print "=" * 13 * col_count 
				break
			for value in row:
				print '%-12s' % value,
			print ""

	def PrintValueWidth(self, ColumnCount, ColumnWidth):
		TotalWidth = sum(int(CW) for CW in ColumnWidth)
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print "=" * abs(TotalWidth)
				break
			for value, width in zip(row, ColumnWidth):
				print '%*s' % (int(width), value),
			print ""
