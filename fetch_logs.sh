if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]
  then
    echo "Usage: fetch_logs.sh num_flows time_run congestion_algo"
    exit 1
fi

curl https://github.com/adithyaphilip/cloudlab/raw/logs_$1_flows_$2_s_$3_algo/iperf3_log_parsed_merged > logs/$1_flows_$2_s_$3_algo