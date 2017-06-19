#!/nas/HC/PYTHON2.7/bin/python

for index in range(16000):
   mpa_id, session_id = divmod(index, 1000)
   print mpa_id, session_id
   bd_id, mpa_id = divmod(mpa_id, 8)
   print bd_id, mpa_id
