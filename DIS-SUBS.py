#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-

#!/nas/HC/PYTHON2.7/bin/python -tt
# -*- coding: utf-8 -*-
import sys
import lib.vms_hc
#import datetime
import argparse
from Crypto.Cipher import AES
import base64

BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 
unpad = lambda s : s[0:-ord(s[-1])]

class CipherAES(object):
	def __init__(self, base64_encoded_key):
		"""
		key is base64_encoded_key
		"""
		self.key = base64.decodestring(base64_encoded_key)

	def PKCS5Padding(self, raw_phoneid):
		"""
		If numberOfBytes(clearText) mod 8 == 7, PM = M + 0x01
		If numberOfBytes(clearText) mod 8 == 6, PM = M + 0x0202
		If numberOfBytes(clearText) mod 8 == 5, PM = M + 0x030303
		...
		If numberOfBytes(clearText) mod 8 == 0, PM = M + 0x0808080808080808
		"""
		padded_phoneid = raw_phoneid + (BS - len(raw_phoneid) % BS) * chr(BS - len(raw_phoneid) % BS)

		return padded_phoneid


	def encrypt_AES(self, raw_phoneid):
#		Cipher cipher = Cipher.getInstance("AES"); ==>  Java "AES" means AES/ECB/PKCS5Padding
#		bs_phoneid = pad(raw_phoneid)
		bs_phoneid = self.PKCS5Padding(raw_phoneid)
		print repr(bs_phoneid)

		cipher = AES.new(self.key)  # Default is MODE_ECB. IV It is ignored for MODE_ECB and MODE_CTR.
		encrypted_phoneid_hex = cipher.encrypt(bs_phoneid).encode("hex")
#		print "enc_phoneid : %s" % ( enc_phoneid)

		return encrypted_phoneid_hex

	def decrypt_AES(self, encrypted_phoneid_hex):
		encrypted_phoneid = encrypted_phoneid_hex.decode("hex")
		cipher = AES.new(self.key)
		plain_phoneid = cipher.decrypt(encrypted_phoneid)
#		print "plain_phoneid : %s" % ( plain_phoneid)

		return plain_phoneid


def main():
	parser = argparse.ArgumentParser(description="POINT-I Health Check Tool. This tool check a alarm.")
	parser.add_argument('-p', '--phoneid', action='store', help="PREFIX, ex) 010-2099-1234, 2099")
	args = parser.parse_args()

	base64_encoded_key='ezRaQz4nPDtZSUM4QysoXw=='
	decryptor = CipherAES(base64_encoded_key)

	encoded_phoneid = decryptor.encrypt_AES(args.phoneid)
	print encoded_phoneid
#	enc_phoneid = '9af1e9600bbe0f988a20b7030a026c50'
	print "=============================="
	dec_phoneid = decryptor.decrypt_AES(encoded_phoneid)
	print unpad(dec_phoneid)

#	DbParameter = []
#	DbParameter.append(args.netid)
#	DbParameter.append(args.prefix)

#	print DbParameter

#	cmd.DisPrefix("DSN=odbc_local", DbParameter)

if __name__ == "__main__":
	sys.exit(main())
