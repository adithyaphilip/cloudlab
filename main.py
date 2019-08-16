import netifaces
import right_hand
import left_hand
import os
import subprocess
import consts
import time
import log_parser


# NOTE: This code has an upper limit on the RTT it can handle because of the ping timeout in consts.py

def get_own_ip(starts_with):
    for interface in netifaces.interfaces():
        if netifaces.AF_INET in netifaces.ifaddresses(interface):
            for link in netifaces.ifaddresses(interface)[netifaces.AF_INET]:
                if 'addr' in link and link['addr'].startswith(starts_with):
                    return link['addr']
    return None


def wait_till_target_live(target_ip: str, ping_timeout_s: int, max_intervals: int):
    ctr = 0

    while subprocess.call("ping -c 1 -w %d %s" % (ping_timeout_s * 1000, target_ip), shell=True) != 0:
        print("Host is not live yet! Continue waiting.")
        ctr += 1
        if ctr >= max_intervals:
            raise Exception("Waited %d intervals, host still down!" % max_intervals)

    print("Host is live! Finished waiting.")
    return None


def main():
    if os.path.exists(consts.LOG_FILEPATH):
        print("Deleting old log file")
        os.remove(consts.LOG_FILEPATH)

    print("IMP: Running in MODE", str(consts.MODE))
    own_ip = get_own_ip(consts.IP_PREFIX)
    node_num = int(own_ip[own_ip.rfind('.') + 1:])
    print("Own node num: ", node_num)

    if node_num > consts.COUNT_PER_SIDE:
        right_hand.start_iperf3_server()
    else:
        target_ip = consts.IP_PREFIX + str(consts.COUNT_PER_SIDE + node_num)
        if consts.MODE == consts.Mode.DEBUG:
            target_ip = "127.0.0.1"
            right_hand.start_iperf3_server()
        print("Target IP:", target_ip)
        wait_till_target_live(target_ip, consts.PING_TIMEOUT_S, consts.PING_TRIES)
        left_hand.start_iperf(target_ip, consts.N_FLOWS, consts.TEST_TIME_S)

        log_parser.parse_iperf_json(consts.LOG_FILEPATH, own_ip, consts.LOG_PARSED_FILEPATH + "_" + own_ip)
        subprocess.call('scp -i /users/aphilip/.ssh/id_rsa %s aphilip@192.168.1.1:/users/aphilip/'
                        % (consts.LOG_PARSED_FILEPATH + "_" + own_ip), shell=True)


main()
