import sys
import socket
import consts
from main import get_own_ip


def start_listening(port: int):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(('', port))

    while True:
        _ = server_socket.recvfrom(2000)  # we just want to keep draining the socket


def main():
    if len(sys.argv) != 2:
        print("ERROR: Usage: udp-bg-server.py SERVER_PORT")
        exit(1)

    start_listening(int(sys.argv[1]))


if __name__ == '__main__':
    main()
