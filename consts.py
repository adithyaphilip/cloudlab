from enum import Enum


class Mode(Enum):
    PROD = 1
    DEBUG = 2


MODE = Mode.PROD

IPERF_BINARY = "iperf3" if MODE == Mode.PROD else "./iperf3_mac"
LOG_FILEPATH_PREFIX = "iperf3_log"
LOG_PARSED_FILEPATH = "iperf3_log_parsed"
PING_TRIES = 600 if MODE == Mode.PROD else 10
PING_TIMEOUT_S = 5 if MODE == Mode.PROD else 1
IPERF_SERVER_BASE_PORT = 6001

# if there are more than these number of connections to be made, we will start a new client
IPERF_MAX_CONN_PER_CLIENT = 100

IP_PREFIX = "192.168.1." if MODE == Mode.PROD else "127.0.0."
N_FLOWS = 2 if MODE == Mode.PROD else 2
TEST_TIME_S = 600
IPERF_LOG_INTERVAL_S = 20
COUNT_PER_SIDE = 15
CONGESTION_ALGO = 'cubic'
