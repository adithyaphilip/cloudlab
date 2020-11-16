import sys
import os
import subprocess
import re
import time
import datetime
import struct

RE_SEQ = re.compile(r'seq ([0-9]+)')
RE_TIME = re.compile(r'([0-9][0-9]):([0-9][0-9]):([0-9][0-9])\.([0-9]+)')
MIN_SEQ_WRAP = 2 ** 30
MAX_SEQ_NUM = 2 ** 32


def caught_retransmission(op_file, seq: int, hours: int, minutes: int, sec: int, ms: int):
    print(f"retransmission! {seq} {hours}::{minutes}:{sec}.{ms}")
    timeval = int(round(datetime.datetime(1970, 1, 2, hour=hours, minute=minutes, second=sec, microsecond=ms,
                                          tzinfo=None).timestamp() * 1000))

    op_file.write(struct.pack('<Q', seq))
    op_file.write(struct.pack('<I', timeval))


def log_retransmits(own_ip: str, interface: str):
    port_last_seq_map = {}
    port_padding_map = {}
    RE_PORT = re.compile(rf'IP {own_ip}\.([0-9]+)')
    cmd = f"sudo tcpdump -r temp.pcap -i {interface} -n 'host {own_ip} and tcp and tcp[tcpflags] & tcp-syn == 0'"
    print(cmd)
    with open(own_ip + "_retr", "wb") as f:
        for line in execute(cmd):
            # print(line)
            match_seq = RE_SEQ.search(line)
            match_port = RE_PORT.search(line)
            match_time = RE_TIME.match(line)
            if match_seq and match_port:
                seq = int(match_seq.group(1))
                port = int(match_port.group(1))

                if port not in port_padding_map:
                    port_padding_map[port] = 0

                if port not in port_last_seq_map:
                    port_last_seq_map[port] = 0  # ignore the first packet we see
                elif seq > port_last_seq_map[port]:
                    # if you are too far ahead of the current seq, you are part of the before-wraparound
                    if seq - port_last_seq_map[port] > MIN_SEQ_WRAP:
                        caught_retransmission(f, seq + port_padding_map[port] - MAX_SEQ_NUM,
                                              int(match_time.group(1)),
                                              int(match_time.group(2)),
                                              int(match_time.group(3)),
                                              int(match_time.group(4)))
                    else:
                        port_last_seq_map[port] = seq
                else:
                    # if you are too far behind the current seq, you have wrapped around
                    if port_last_seq_map[port] - seq > MIN_SEQ_WRAP:
                        port_last_seq_map[port] = seq
                        port_padding_map[port] += MAX_SEQ_NUM
                    else:
                        # print(seq, port_last_seq_map[port])
                        caught_retransmission(f, seq + port_padding_map[port],
                                              int(match_time.group(1)),
                                              int(match_time.group(2)),
                                              int(match_time.group(3)),
                                              int(match_time.group(4))
                                              )


def read_log(own_ip: str):
    ctr = 0
    with open(own_ip + "_retr", "rb") as f:
        while True:
            buf = f.read(12)
            if buf != b'':
                seq, timeval = struct.unpack('<QI', buf)
                print("Read: ", seq, datetime.datetime.fromtimestamp(timeval / 1000).strftime('%Y-%m-%d %H:%M:%S'))
            else:
                break
            ctr += 1
    print(ctr)


def execute(cmd):
    popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True, shell=True)
    for stdout_line in iter(popen.stdout.readline, ""):
        yield stdout_line
    popen.stdout.close()
    return_code = popen.wait()
    if return_code:
        raise subprocess.CalledProcessError(return_code, cmd)


def main():
    if len(sys.argv) != 3:
        print("Usage: tcpdump_parser own_ip if_name", file=sys.stderr)
        exit(1)
    log_retransmits(sys.argv[1], sys.argv[2])
    read_log(sys.argv[1])


if __name__ == '__main__':
    main()
