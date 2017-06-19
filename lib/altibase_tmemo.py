#!/nas/HC/PYTHON2.7/bin/python -tt
import sys
import pyodbc

class AltibaseConn(object):
	cnxn = pyodbc.connect('DSN=odbc_local')
	cursor = cnxn.cursor()

	def print_value(self,col_count):
		while 1:
			row = self.cursor.fetchone()
			if not row:
				print "=" * 13 * col_count 
				break
			for value in row:
				print '%-12s' % value,
			print ""
