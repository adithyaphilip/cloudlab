import json
import csv
import os
import consts


# returns a list of log entries as tuples - OwnIp, SockNum, EndTime, DataSizeMB, Interval, Bandwidth
def parse_iperf_json(own_ip: str, op_filepath: str):
    rows = []
    part = 0

    while os.path.exists(consts.LOG_FILEPATH_PREFIX + '_%d' % part):
        with open(consts.LOG_FILEPATH_PREFIX + '_%d' % part) as f:
            logs = json.load(f)
        start_time = logs["start"]["timestamp"]["timesecs"]

        for interval in logs["intervals"]:
            for stream in interval["streams"]:
                sock_num = ("%d_" + str(stream["socket"])) % part
                data_mb = stream["bytes"] / (1024 ** 2)
                end_time = stream["end"] + start_time
                interval_s = stream["seconds"]
                retransmits = "n/a"
                bw = data_mb / interval_s
                rows.append((own_ip, sock_num, end_time, data_mb, interval_s, bw, retransmits))

        part += 1

    with open(op_filepath, 'w') as f:
        csv_out = csv.writer(f)
        for row in rows:
            csv_out.writerow(row)

    return rows
