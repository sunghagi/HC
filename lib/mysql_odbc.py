#!/nas/HC/PYTHON2.7/bin/python -tt
import sys
import pyodbc

class MysqlConn(object):
	try:
		cnxn = pyodbc.connect('DSN=mysql')
	except pyodbc.Error, err:
		print err
	cursor = cnxn.cursor()

	def print_value(self,col_count):
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print "=" * 20 * col_count 
				break
			for value in row:
				print '%-19s' % value,
			print ""

	def PrintValueWidth(self, ColumnCount, ColumnWidth):
		TotalWidth = sum(int(CW) for CW in ColumnWidth)
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print "=" * TotalWidth
				break
			for value, width in zip(row, ColumnWidth):
				print '%*s' % (int(width), value),
			print ""
