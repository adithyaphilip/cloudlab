import sys
import time
from socket import *
import random

MEAN_UDP_PACKET_SIZE = 240
MAX_UDP_PACKET_SIZE = 1400


def blocking_sleep(seconds: float):
    start_time = time.time()
    while (time.time() - start_time) < seconds:
        pass


def start_sending(udp_bw_mbps: float, dest_ip: str, dest_port: int):
    packets_per_sec = udp_bw_mbps * pow(10, 6) / 8 / (MEAN_UDP_PACKET_SIZE + 30)
    data = b'0' * MAX_UDP_PACKET_SIZE
    random.seed()

    tot_err = 0
    ctr = 0
    while True:
        client_sock = socket(AF_INET, SOCK_DGRAM)
        addr = (dest_ip, dest_port)
        client_sock.sendto(data, addr)
        delay = random.expovariate(packets_per_sec)
        # print(delay)
        start_time = time.time()
        time.sleep(delay)
        # blocking_sleep(delay)
        actual_time = time.time() - start_time
        # print("Act:", actual_time)
        tot_err += actual_time / delay
        ctr += 1

        if ctr == 10000:
            break
    print("Avg error:", tot_err / ctr)



def main():
    if len(sys.argv) != 4:
        print("ERROR: Usage: udp-bg-client.py UDP_BW_MBPS DEST_IP DEST_PORT")
        exit(1)

    start_sending(float(sys.argv[1]), sys.argv[2], int(sys.argv[3]))


if __name__ == '__main__':
    main()
