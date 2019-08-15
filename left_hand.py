import netifaces
import sys
import subprocess
import consts


# starts given number of flows targeted at given ip address incrementing port numbers by 1 starting at the given base
def start_iperf(target_ip: str, n_flows: int):
    # NOTE: DON't FORGET TO PUT IN -C cubic!!!
    subprocess.call("%s -c %s -P %d -i 1 --json --logfile %s"
                    % (consts.IPERF_BINARY, target_ip, n_flows, consts.LOG_FILEPATH),
                    shell=True)


# start_iperf("127.0.0.1", 100)
