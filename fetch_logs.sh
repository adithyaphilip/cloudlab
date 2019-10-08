if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]
  then
    echo "Usage: fetch_logs.sh num_flows_per_node time_run congestion_algo num_nodes_used"
    exit 1
fi

curl https://raw.githubusercontent.com/adithyaphilip/cloudlab/logs_$4_nodes_$1_flows_$2_s_$3_algo/iperf3_log_parsed_merged > logs/$4_nodes_$1_flows_$2_s_$3_algo_nonetem