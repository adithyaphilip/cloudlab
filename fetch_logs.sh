if [ -z "$1" ]
  then
    echo "Requires 1 argument - number of flows executed to generate the log being fetched"
    exit 1
fi

curl https://github.com/adithyaphilip/cloudlab/raw/logs_$1_flows_$2_s_$3_algo/iperf3_log_parsed_merged > logs/$1_flows_$2_s_$3_algo