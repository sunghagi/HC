#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import sys
import lib.vms_hc
#import datetime
import argparse
from Crypto.Cipher import AES
import base64
import re

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s : s[0:-ord(s[-1])]

class CipherAES(object):
   def __init__(self, base64_encoded_key):
      """
      key is base64_encoded_key
      """
      self.key = base64.decodestring(base64_encoded_key)

   def encrypt_AES(self, raw_phoneid):
      """
      Cipher cipher = Cipher.getInstance("AES"); ==>  Java "AES" means AES/ECB/PKCS5Padding
      """ 
      bs_phoneid = pad(raw_phoneid)
      cipher = AES.new(self.key)  # Default is MODE_ECB. IV It is ignored for MODE_ECB and MODE_CTR.
      encrypted_phoneid_hex = cipher.encrypt(bs_phoneid).encode("hex")

      return encrypted_phoneid_hex

   def decrypt_AES(enc_phoneid):
      encrypted_phoneid = encrypted_phoneid_hex.decode("hex")
      cipher = AES.new(self.key)
      raw_phoneid = cipher.decrypt(encrypted_phoneid)

      return raw_phoneid

def dis_subs(DSN, phoneid, raw_phoneid):
   cmd_result = lib.vms_hc.HcResult()  

   column_name = ' BIZ RING SUBSCRIBER INFORMATION '
   db_column_name=['가입자 전화번호','음원송출중지여부','TRING가입','TRING플러스차단','CREATEDDATE']
   db_column_width=['17','22','15','17','15']
   column_width = sum(int(CW) for CW in db_column_width)
   cmd_result_table = lib.vms_hc.HcCmdResultTalbe(column_name, column_width)

   print cmd_result_table.output

   print "   Encrypted phoneid : %s\n" % ( phoneid[0] )

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode

#   if HaStatus == 'ACTIVE':

   db_query = """
   select PHONEID,
   decode(ISPAUSE, 0, '송출유지', 
                   1, '송출중단'),
   decode(ISMEMBEROFTRING, 0, '비회원', 
                           1, '회원'),
   decode(ISMEMBEROFTRPLUSCUTOUT, 0, '비회원', 
                                  1, '회원'),
   to_char(CREATEDDATE,'YYYY-MM-DD')
   from SUBSCRIBER
   where phoneid = ?
   """
   db_param = phoneid
   subs, result = lib.vms_hc.odbc_query_execute_fetchall(DSN, db_query, db_param, db_column_width)

   db_column_name = lib.vms_hc.print_column_name(db_column_name, db_column_width)

   if result.result == "OK":
      output_buf = lib.vms_hc.string_concate(db_column_name, subs)
      raw_phoneid = "   " + raw_phoneid
      output_buf = output_buf.replace(phoneid[0],raw_phoneid)
      print output_buf

   result_templ = "   %-10s %3s %-30s "
   print result_templ % ("RESULT", "=", result.result)
   if result.result == "NOK":
      print result_templ % ("REASON", "=", result.reason)
   print ""

def is_phone_number(phoneid):
#   rule = re.compile('01[0-9]{1}[0-9]{8}')
   rule = re.compile(r'(01[0-9]{1}[0-9]{8})')

   if not rule.search(phoneid):
      msg = "%s is Invalid phone number." % phoneid
      raise argparse.ArgumentTypeError(msg)
   return phoneid

def main():
   parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
   parser.add_argument('-p', '--phoneid', action='store', required=True, type=is_phone_number, help="phoneid, ex) 01090874208")
   args = parser.parse_args()

#   HOST_INFO = lib.vms_hc.HostInfo()  # ['EVMS01','SPS01', 'SPS', '121.134.202.163','ACTIVE','1'],
#   HOST_INFO._host_info()

#   SystemNumber = HOST_INFO.system_name
#   HostName = HOST_INFO.hostname
#   HostClass = HOST_INFO.hostclass
#   HaStatus = HOST_INFO.ha_operating_mode
#   HaInstalled = HOST_INFO.ha_installed
   base64_encoded_key='ezRaQz4nPDtZSUM4QysoXw=='
   encryptor = CipherAES(base64_encoded_key)

   encrypted_phoneid_hex = encryptor.encrypt_AES(args.phoneid)

   db_parameter = []
   db_parameter.append(encrypted_phoneid_hex)

   dis_subs("DSN=odbc_db1", db_parameter, args.phoneid)

if __name__ == "__main__":
   sys.exit(main())
