import subprocess
import consts


def start_iperf3_server():
    print("Starting iPerf3 server on default port")
    subprocess.call("%s -sD" % consts.IPERF_BINARY, shell=True)

# start_iperf3_servers()
