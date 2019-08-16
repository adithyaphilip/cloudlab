import json
import csv


# returns a list of log entries as tuples - OwnIp, SockNum, EndTime, DataSizeMB, Interval, Bandwidth
def parse_iperf_json(filepath: str, own_ip: str, op_filepath: str):
    with open(filepath, 'r') as f:
        logs = json.load(f)
    start_time = logs["start"]["timestamp"]["timesecs"]

    rows = []

    for interval in logs["intervals"]:
        for stream in interval["streams"]:
            sock_num = stream["socket"]
            data_mb = stream["bytes"] / (1024 ** 2)
            end_time = stream["end"] + start_time
            interval_s = stream["seconds"]
            bw = data_mb / interval_s
            rows.append((own_ip, sock_num, end_time, data_mb, interval_s, bw))

    with open(op_filepath, 'w') as f:
        csv_out = csv.writer(f)
        for row in rows:
            csv_out.writerow(row)

    return rows
