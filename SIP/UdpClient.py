#!/nas/HC/PYTHON2.7/bin/python

import socket
import sys
import time

HOST, PORT = "localhost", 9999
PATH = 'omc_trace'
data = " ".join(sys.argv[1:])

# SOCK_DGRAM is the socket type to use for UDP sockets
#sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#sock.sendto(data + "\n", (HOST, PORT))

# Create a UDS socket
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(PATH)

filename = 'a.log'
fileobj = open(filename, 'rb')
seq = fileobj.readlines()

# As you can see, there is no connect() call; UDP has no connections.
# Instead, data is directly sent to the recipient via sendto().


#seq = "test"

for s in seq:
#	print s,
#	sock.sendto(s, (HOST, PORT))
#	print repr(s)
	sock.sendall(s)

#received = sock.recv(1024)

#print "Sent:     {}".format(data)
#print "Received: {}".format(received)
