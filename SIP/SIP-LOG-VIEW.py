#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
"""SIP LOG ANALYZER. 
This tool search a sipa_fdump.MMDD log and print a sip call flows.

Usage: SIP-LOG-VIEW.py [options] MDN DATE

Options:
	-h / --help
		Print this message and exit.

	-l / --log
		Print call flows and sip log.

`MDN' is the phone number of the sender.
	ex) 01090874208

`DATE' is the date, format is 'MMDD'.
	ex) 0220
"""

import sys
import getopt
import time
import datetime
import re
import glob
import SocketServer
#import xml.etree.ElementTree as ET

udp_chunk = []
flow_number = 1
log_number = 1
flag_log = 0

def usage(code, msg=''):
	print >> sys.stderr, __doc__
	if msg:
		print >> sys.stderr, msg
	sys.exit(code)

def parse_number(_to):
	nums = re.findall(r'(\d+)',_to)
	return nums

class MyUDPHandler(SocketServer.BaseRequestHandler):
	def handle(self):
		global udp_chunk
		global flag_log
		udp_chunk.append(self.request[0])

		separator = '\\n'
		if self.request[0] == separator:
#			print "callflow start!!!!!!!! ------------------------------------------------"
			show_callflows(udp_chunk)
			if flag_log:
				show_calllogs(udp_chunk)
			udp_chunk = []

class Paragraphs:
	def __init__(self, udp_data, separator='\\n'):
		self.seq = udp_data

		self.line_num = 0
		self.para_num = 0

		self.separator = separator

	def __getitem__(self, index):
		if index != self.para_num:
			raise TypeError, "Only sequential access supported"
		self.para_num += 1
		while 1:
			line = self.seq[self.line_num]
			self.line_num += 1
			if line != self.separator: break
		result = [line]
		self.flow_time = re.findall('..:..:......',line)
		dirc = re.findall('RECV|SEND',line)
		if 'SEND' in dirc:
			self.flow_dirc = '|<----XXXXXXXXXXXXXX-----|'
		elif 'RECV' in dirc:
			self.flow_dirc = '|-----XXXXXXXXXXXXXX---->|'

		line = self.seq[self.line_num]
		method = re.findall("INVITE|100\ Trying|180\ Ringing|200\ OK|ACK|BYE|INFO",line)
		if method[0] == "INVITE" :
			method_arrow = "--- INVITE ---"
		elif method[0] == "200 OK" :
			method_arrow = "--- 200 OK ---"
		elif method[0] == "INFO" :
			method_arrow = "---- INFO ----"
		elif method[0] == "BYE" :
			method_arrow = "---- BYE -----"
		elif method[0] == "ACK" :
			method_arrow = "---- ACK -----"
		elif method[0] == "100 Trying" :
			method_arrow = "- 100 Trying -"
		elif method[0] == "180 Ringing" :
			method_arrow = "- 180 Ringing-"
		else :
			method_arrow = "--------------"
		self.sip_method_arrow = re.sub( "XXXXXXXXXXXXXX", method_arrow, self.flow_dirc )
		self.sip_method = method[0]
		while 1:
			try:
				line = self.seq[self.line_num]
			except IndexError:
				break
			self.line_num += 1
			if line == self.separator: break
			result.append(line)
		return ''.join(result)

def show_callflows(sipa_data):
	pp = Paragraphs(sipa_data)
	global flow_number
#	print "#    Time            TAS                T-Memo Ring   Comment"
#	print "------------------------------------------------------------------------------------------"
	for p in pp:
		print_comment = ''
		if pp.sip_method == 'INVITE':
			_from = re.findall('From.*>', p)
			_to = re.findall('To.*>', p)
			_to_mdn = parse_number(''.join(_to))
			if re.findall('^1578290', ''.join(_to_mdn)):
				call_type = '3G HD, BRBT Only'
			elif re.findall('^1578291', ''.join(_to_mdn)):
				call_type = '3G HD, BRBT + RATA'
				_rata_para = ''.join(_to_mdn)[7:12]
			else:
				call_type = 'HDV, BRBT'
#				time.sleep(100)
			_OTCI = re.findall('P-SKT-O-TCI:.*\', p)
			_o = re.findall('o=.*\', p)
			_m = re.findall('m=.*\', p)
			_a = re.findall('a=rtpmap.*\', p)
			_via_pattern = re.search('(Via.*) (\d.*);', p)
			_via = _via_pattern.group(2)
			comment1 = _from + _to
			print_comment1 = ' '.join(comment1)
			comment2 = _OTCI
			print_comment2 = ' '.join(comment2)
			comment3 = _o
			print_comment3 = ' '.join(comment3)
			comment4 = _m
			print_comment4 = ' '.join(comment4)
			print ""
			print "#     Time        %s          BizRing     Comment" % ( _via )
			print "---------------------------------------------------------------------------"
			print "%-3d %14s %30s       %s" % ( flow_number, pp.flow_time[0], pp.sip_method_arrow, print_comment1 )
			print "                       |                        |         ==> CALL-TYPE : %-s" % ( call_type )
			if call_type == '3G HD, BRBT + RATA':
				print "                       |                        |         ==> RAT 파라미터 : %-s" % ( _rata_para )
			if print_comment2.strip():
				o_tci = print_comment2.split()[1]
				if o_tci == 'C0':
					o_tci = 'MOInternal'
				else:
					o_tci = 'ETC'
				print "                       |                        |       %-s" % ( print_comment2 )
				print "                       |                        |         ==> O-TCI: %-s" % ( o_tci )
			print "                       |                        |       %-s" % ( print_comment3 )
			print "                       |                        |       %-s" % ( print_comment4 )
			for num in _a:
				print "                       |                        |       %-s" % ( num )
		elif pp.sip_method == '200 OK':
			_o = re.findall('o=.*\', p)
			_m = re.findall('m=.*\', p)
			_a = re.findall('a=rtpmap.*\', p)
			comment1 = _o
			print_comment1 = ' '.join(comment1)
			if print_comment1:
				splited_comment1 = print_comment1.split()
				timestamp_sess_version = splited_comment1[2]
				dateformat_sess_version = datetime.datetime.fromtimestamp(int(timestamp_sess_version)).strftime('%Y-%m-%d %H:%M:%S')
			comment2 = _m
			print_comment2 = ' '.join(comment2)
			print "%-3d %14s %30s       %s" % ( flow_number, pp.flow_time[0], pp.sip_method_arrow, print_comment1 )
			if _o:
				print "                       |                        |         ==> Date Format Session Version : %-s" % ( dateformat_sess_version )
			if _m:
				print "                       |                        |       %-s" % ( print_comment2 )
			for num in _a:
				print "                       |                        |       %-s" % ( num )
		elif pp.sip_method == 'INFO':
			print "%-3d %14s %30s" % ( flow_number, pp.flow_time[0], pp.sip_method_arrow )
#				_xml = re.findall('\n\ *<.*>',p,re.M)
			_xml = re.findall('^\s*<.*>',p,re.M)
#				_xml = re.findall('\n\ *<.*>',p)
			for num in _xml:
				item = num.replace("\r\n","")
#					print "                      |                        |       %-s" % ( repr(num) )
				print "                       |                        |       %-s" % ( str(item) )
		else :
			print "%-3d %14s %30s" % ( flow_number, pp.flow_time[0], pp.sip_method_arrow )
#			print "%-2d %14s %45s" % ( flow_number, pp.flow_time[0], pp.sip_method_arrow )
		flow_number += 1
		

def show_calllogs(sipa_data):
	pp = Paragraphs(sipa_data)
	global log_number
	for p in pp:
		print "---- # %-2d %14s -----------------------------------------------------------" % ( log_number, pp.flow_time[0] )
		print p
		log_number += 1	

def main():
	try:
		opts, args = getopt.getopt(sys.argv[1:], 'hl', ['help', 'log'])
	except getopt.error, msg:
		usage(1, msg)

	global flag_log

	for opt, arg in opts:
		if opt in ('-h', '--help'):
			usage(0)
		elif opt in ('-l', '--log'):
			flag_log = 1

#	if len(args) < 2 or len(date) != 4:
#		usage(1)

	HOST, PORT = "localhost", 9999
	server = SocketServer.UDPServer((HOST, PORT), MyUDPHandler)
	try:
		server.serve_forever()
	except KeyboardInterrupt:
		sys.exit(0)

#	show_callflows(mdn, date, fdump_log)

	print "\n"
	if flag_log == 1 :
		for fdump_log in fdump_log_list:	
			show_calllogs(mdn, date, fdump_log)

if __name__ == "__main__":
	sys.exit(main())
