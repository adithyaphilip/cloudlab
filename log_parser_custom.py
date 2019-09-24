import json
import csv
import os
import consts


# returns a list of log entries as tuples - OwnIp, SockNum, EndTime, DataSizeMB, Interval, Bandwidth
def parse_iperf_json(op_filepath: str):
    rows = []

    for vas in [('192.168.1.1', 1, 'logs/btl_tests/1_100_1')]:
        with open(vas[2]) as f:
            logs = json.load(f)
        start_time = logs["start"]["timestamp"]["timesecs"]

        for interval in logs["intervals"]:
            for stream in interval["streams"]:
                sock_num = ("%d_" + str(stream["socket"])) % vas[1]
                data_mb = stream["bytes"] / (1024 ** 2)
                end_time = stream["end"] + start_time
                interval_s = stream["seconds"]
                bw = data_mb / interval_s
                rows.append((vas[0], sock_num, end_time, data_mb, interval_s, bw))

    with open(op_filepath, 'w') as f:
        csv_out = csv.writer(f)
        for row in rows:
            csv_out.writerow(row)

    return rows


parse_iperf_json('btl_test_1_100')
