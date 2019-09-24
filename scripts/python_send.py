import socket
import sys

# create an INET, STREAMing socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((sys.argv[1], int(sys.argv[2])))

pat = ("0"*10**4).encode()

while True:
    s.sendall(pat)
