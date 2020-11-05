import sys
import os
import subprocess
import re
import time
import struct

RE_SEQ = re.compile(r'seq ([0-9]+)')


def log_retransmits(own_ip: str):
    port_last_seq_map = {}
    RE_PORT = re.compile(rf'IP {own_ip}\.([0-9]+)')
    cmd = f"sudo tcpdump -n 'host {own_ip} and tcp and tcp[tcpflags] & tcp-syn == 0'"
    print(cmd)
    with open(own_ip + "_retr", "w") as f:
        for line in execute(cmd):
            print(line)
            match_seq = RE_SEQ.search(line)
            match_port = RE_PORT.search(line)
            if match_seq and match_port:
                seq = int(match_seq.group(1))
                port = int(match_port.group(1))

                if port not in port_last_seq_map:
                    port_last_seq_map[port] = 0  # ignore the first packet we see
                elif seq > port_last_seq_map[port]:
                    port_last_seq_map[port] = seq
                else:
                    # we have a retranmission! Log it!
                    print(f"retransmission! {seq} {port_last_seq_map[port]}")


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, shell=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def main():
    if len(sys.argv) != 2:
        print("Usage: tcpdump_parser own_ip", file=sys.stderr)
        exit(1)
    log_retransmits(sys.argv[1])


if __name__ == '__main__':
    main()
