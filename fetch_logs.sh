if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]
  then
    echo "Usage: fetch_logs.sh num_flows_per_node time_run congestion_algo num_nodes_used num_trials"
    exit 1
fi

# NOTE: Currently fetching rev mode only
for trial in $(seq 1 $5)
do
curl https://raw.githubusercontent.com/adithyaphilip/cloudlab/logs_$4_nodes_$1_flows_$2_s_$3_algo_rev_$trial/iperf3_log_parsed_merged > logs/$4_nodes_$1_flows_$2_s_$3_algo_rev_$trial
done