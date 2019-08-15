from enum import Enum


class Mode(Enum):
    PROD = 1
    DEBUG = 2


MODE = Mode.DEBUG

IPERF_BINARY = "iperf3" if MODE == Mode.PROD else "./iperf3_mac"
LOG_FILEPATH = "iperf3_log"

IP_PREFIX = "192.168.1." if MODE == Mode.PROD else "127.0.0."
N_FLOWS = 100 if MODE == Mode.PROD else 2
COUNT_PER_SIDE = 5
