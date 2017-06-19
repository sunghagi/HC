#!/nas/HC/PYTHON2.7/bin/python

import SocketServer
import threading
import time
import os

class MyUDPHandler(SocketServer.BaseRequestHandler):
    """
    This class works similar to the TCP handler class, except that
    self.request consists of a pair of data and client socket, and since
    there is no connection the client address must be given explicitly
    when sending data back via sendto().
    """

    def handle(self):
#        data = self.request[0].strip()
#        data = self.request[0]o
         while 1 :
             data = self.request.recv(1024)
             cur_thread = threading.current_thread()
             print data
             if data == '':
                 break
#        socket = self.request[1]
#        print "{} wrote:".format(self.client_address[0])
#        socket.sendto(data.upper(), self.client_address)

#class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.UnixStreamServer):
#    pass

if __name__ == "__main__":
    HOST, PORT = "localhost", 9999
    PATH = '/home/brbt/ipc/udp/comm2oma'
#    PATH = 'omc_trace'
    try:
        os.unlink(PATH)
    except OSError:
        if os.path.exists(PATH):
            raise
#    server = SocketServer.UDPServer((HOST, PORT), MyUDPHandler)
    server = SocketServer.UnixStreamServer(PATH, MyUDPHandler)
#    server = ThreadedTCPServer(PATH, MyUDPHandler)
#    server_thread = threading.Thread(target=server.serve_forever)
#    server_thread.daemon = True
#    server_thread.start()
    
    server.serve_forever()
#    print "Server loop running in thread:", server_thread.name

#    server.shutdown()
#    server.server_close()
