#!/usr/bin/env python
# ----------------------------------------------------------------------------------
# Utility for testing udp packet loss.  Invoke the server on one machine and 
# use the client on the other to send data.  Results are printed on the server side.
# ----------------------------------------------------------------------------------
import socket
from optparse import OptionParser
from time import sleep, time
from IN import SO_RCVBUF

DEFAULT_BUFSIZE = 1000
DEFAULT_DELAY = 0
DEFAULT_NUM_BUFFERS = 10
DEFAULT_PROTOCOL = "udp"
DEFAULT_BURST_SIZE = 100
t = ""

DEFAULT_HOST = 'localhost'    # The remote host
DEFAULT_PORT = 5077              # The same port as used by the server

#========== arguments
parser = OptionParser()
parser.add_option("-c", "--command", dest="command",
                  help="where COMMAND is one of 'client','server'", metavar="COMMAND")
parser.add_option("--hostname", dest="hostname",
                  help="hostname to connect to", metavar="")
parser.add_option("--port", type="int", dest="port",
                  help="port to connect to", metavar="")
parser.add_option("-n", "--count", type="int", dest="count",
                  help="number of buffers to send", metavar="")
parser.add_option("--bufsize", type="int", dest="bufsize",
                  help="buffer size to send", metavar="")
parser.add_option("--delay", type="int", dest="delay",
                  help="delay per buffer in msec", metavar="")
parser.add_option("--protocol", dest="protocol",
                  help="where PROTOCOL is either 'udp' or 'tcp'", metavar="PROTOCOL")
(options, args) = parser.parse_args()

#========== setup
def client(hostname=DEFAULT_HOST, port=DEFAULT_PORT, count=DEFAULT_NUM_BUFFERS, bufsize=DEFAULT_BUFSIZE, delay=DEFAULT_DELAY, protocol=DEFAULT_PROTOCOL):
    if (hostname == None):
        hostname = DEFAULT_HOST
    if (port == None):
        port = DEFAULT_PORT
    if (count == None):
        count = DEFAULT_NUM_BUFFERS
    if (bufsize == None):
        bufsize = DEFAULT_BUFSIZE
    if (delay == None):
        delay = DEFAULT_DELAY
    if (protocol == None):
        delay = DEFAULT_PROTOCOL
    buf = t.join(["x"] * bufsize)
    print "Starting, delay is " + str(float(delay)/1000) + " sec"
    
    if (protocol == "udp"):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect((hostname, port))
    elif (protocol == "tcp"):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((hostname, port))

    start = time()
    s.send("start\n")
    s.send(str(bufsize) + "\n")
    s.send(str(count) + "\n")
    for i in range(count):
        s.send(buf + "\n")
        #only sleep every 'n' buffers.  It makes the traffic "bursty"
        if (i % DEFAULT_BURST_SIZE == 0):
            sleep(float(delay)/1000)
    sleep(1)
    s.send("end\n")
    print "sent, " + str(time() - start) + " sec"

class Reciever:
    def __init__(self, protocol, hostname, port):
        self.protocol = protocol
        self.port = port
        if (protocol == "udp"):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            #UDP socket buffer size
            self.sock.setsockopt(socket.SOL_SOCKET, SO_RCVBUF, 1073741824)
            self.sock.bind((hostname, port))
        elif (protocol == "tcp"):
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.bind((hostname, port))
                   
    def recv(self, bufsize):
        if (self.protocol == "udp"):
            data, addr = self.sock.recvfrom(bufsize)
            #strip off trailing newlines
            data = data.rstrip()
        elif (self.protocol == "tcp"):
            count = 0
            data = ""
            while (count < bufsize):
                count += 1
                c = self.conn.recv(1)
                if (c != "\n"):
                    data += c
                else:
                    return data
        return data

    def close(self):
        self.sock.close()
    
    def listen(self):
        if (self.protocol == "tcp"):
            self.sock.listen(1)
            self.conn, addr = self.sock.accept()
    
def server(hostname=DEFAULT_HOST, port=DEFAULT_PORT, protocol=DEFAULT_PROTOCOL):
    if (hostname == None):
        hostname = DEFAULT_HOST
    if (port == None):
        port = DEFAULT_PORT
    print "listening on host " + hostname + ", port " + str(port)
    reciever = Reciever(protocol, hostname, port)
    reciever.listen()
    count = 0
    while (True):
        data  = reciever.recv(100000)
        if (data == "start"):
            start = time()
            count = 0
            data = reciever.recv(1024)
            bufsize = int(data)
            data = reciever.recv(1024)
            expected_count = int(data)
            print "starting, bufsize = " + str(bufsize) 
        elif (data == "end"):
            print "finished, count: " + str(count) + ", " + str(time() - start) + " sec"
            if (expected_count != count):
                print "Expected " + str(expected_count) + ", got " + str(count) + ", error rate " + str(1 - float(count)/float(expected_count))
            reciever.listen()
        else:
            count += 1
            length = len(data)
            if (length != bufsize):
                print "buffer error, buf len is " + str(length) + ", should be " + str(bufsize)

#========== command line processing
if (options.command == "client"):
    client(options.hostname, options.port, options.count, options.bufsize, options.delay, options.protocol)
elif (options.command == "server"):
    server(options.hostname, options.port, options.protocol)
else:
    parser.print_help()
