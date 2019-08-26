import netifaces
import sys
import subprocess
import consts
import threading


def iperf3_run(target_ip: str, n_flows: int, port_num: int, part: int):
    subprocess.call("%s -c %s -p %d -P %d -t %d -i %d --json -C %s -w 2G > %s"
                    % (consts.IPERF_BINARY,
                       target_ip,
                       port_num,
                       n_flows,
                       consts.TEST_TIME_S,
                       consts.IPERF_LOG_INTERVAL_S,
                       consts.CONGESTION_ALGO,
                       consts.LOG_FILEPATH_PREFIX + "_%d" % part),
                    shell=True)


# starts given number of flows targeted at given ip address incrementing port numbers by 1 starting at the given base
def start_iperf(target_ip: str):
    threads = []

    for part in range(consts.N_FLOWS // consts.IPERF_MAX_CONN_PER_CLIENT + 1):
        port_num = consts.IPERF_SERVER_BASE_PORT + part
        num_flows = min(consts.N_FLOWS - consts.IPERF_MAX_CONN_PER_CLIENT * part, consts.IPERF_MAX_CONN_PER_CLIENT)

        if num_flows == 0:
            break

        threads.append(threading.Thread(target=iperf3_run, args=(target_ip, num_flows, port_num, part)))
        threads[-1].start()

    for th in threads:
        th.join()
