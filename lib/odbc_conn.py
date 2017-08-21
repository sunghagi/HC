#!/nas/HC/PYTHON2.7/bin/python -tt
#-*- coding: utf-8 -*-
import sys
import pyodbc

class odbcConn(object):
	def __init__(self, dsn):
		self.DSN = dsn
		self.error = ""

	def _GetConnect(self):
		''' Connect to the DB '''
		try:
			self.cnxn = pyodbc.connect(self.DSN)
#			self.cnxn.setencoding(unicode, encoding='euckr')
		except Exception as e:
			self.error = e[1]
			raise(NameError,"DB Connected failed!!")
		else:
			self.cursor = self.cnxn.cursor()
			if not self.cursor:
				raise(NameError,"Connected failed!!")
#			else:
#				return self.cur, self.conn

	def print_value(self,col_count):
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print("=" * 13 * col_count)
				break
			for value in row:
				print("%-12s" % value,)
			print ("")

	def PrintValueWidth(self, ColumnCount, ColumnWidth):
		TotalWidth = sum(int(CW) for CW in ColumnWidth)
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print("=" * abs(TotalWidth))
				break
			for value, width in zip(row, ColumnWidth):
				print("%*s" % (int(width), value),)
			print ("")
