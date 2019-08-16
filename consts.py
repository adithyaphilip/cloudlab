from enum import Enum


class Mode(Enum):
    PROD = 1
    DEBUG = 2


MODE = Mode.PROD

IPERF_BINARY = "iperf3" if MODE == Mode.PROD else "./iperf3_mac"
LOG_FILEPATH = "iperf3_log"
LOG_PARSED_FILEPATH = "iperf3_log_parsed"
PING_TRIES = 600 if MODE == Mode.PROD else 10
PING_TIMEOUT_S = 5 if MODE == Mode.PROD else 1

IP_PREFIX = "192.168.1." if MODE == Mode.PROD else "127.0.0."
N_FLOWS = 200 if MODE == Mode.PROD else 2
TEST_TIME_S = 600
IPERF_LOG_INTERVAL_S = 5
COUNT_PER_SIDE = 5
