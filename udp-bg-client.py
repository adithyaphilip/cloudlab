import sys
import time
from socket import *
import random

import netifaces as netifaces

import consts

MEAN_UDP_PACKET_SIZE = 1000
MAX_UDP_PACKET_SIZE = 1400


def blocking_sleep(seconds: float):
    start_time = time.time()
    while (time.time() - start_time) < seconds:
        pass


def start_sending(udp_bw_mbps: float, dest_ip: str, dest_port: int):
    packets_per_sec = udp_bw_mbps * pow(10, 6) / 8 / (MEAN_UDP_PACKET_SIZE + 30)
    data = b'0' * MAX_UDP_PACKET_SIZE
    random.seed()

    # tot_err = 0
    # ctr = 0
    while True:
        client_sock = socket(AF_INET, SOCK_DGRAM)
        addr = (dest_ip, dest_port)
        pkt_size = int(random.expovariate(1 / MEAN_UDP_PACKET_SIZE)) % MAX_UDP_PACKET_SIZE
        client_sock.sendto(data[:pkt_size], addr)
        delay = random.expovariate(packets_per_sec)
        # print(delay)
        # start_time = time.time()
        # time.sleep(delay)
        blocking_sleep(delay)
        # actual_time = time.time() - start_time
        # print("Act:", actual_time)
        # tot_err += actual_time / delay
        # ctr += 1

        # if ctr == 100000:
        #     break
    # print("Avg error:", tot_err / ctr)


def get_own_ip(starts_with):
    for interface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(interface):
            for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                if 'addr' in link and link['addr'].startswith(starts_with):
                    return link['addr']
    return None


def main():
    if len(sys.argv) != 4:
        print("ERROR: Usage: udp-bg-client.py UDP_BW_MBPS NUM_NODES_SIDE DEST_PORT")
        exit(1)

    own_ip = get_own_ip(consts.IP_PREFIX)
    node_num = int(own_ip[own_ip.rfind('.') + 1:])
    print("Own node num: ", node_num)
    target_ip = consts.IP_PREFIX + str(node_num - int(sys.argv[2]))
    start_sending(float(sys.argv[1]), target_ip, int(sys.argv[3]))


if __name__ == '__main__':
    main()
