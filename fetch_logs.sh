# WARNING: This file depends on the IP pattern being 192.168.1.* to correctly download files

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]
  then
    echo "Usage: fetch_logs.sh num_flows_per_node time_run congestion_algo num_nodes_used num_trials"
    exit 1
fi

# NOTE: Currently fetching rev mode only
for trial in $(seq 1 $5)
do
  # just to be safe, clear any remaining past temp logs
  rm logs/temp_*
  for node in $(seq 1 $4)
  do
    curl -f https://raw.githubusercontent.com/adithyaphilip/cloudlab/logs_$4_nodes_$1_flows_$2_s_$3_algo_rev_$trial/iperf3_log_parsed_192.168.1.$node > logs/temp_$node
  done
  cat logs/temp_* > logs/$4_nodes_$1_flows_$2_s_$3_algo_rev_$trial
  echo "Downloaded: $4_nodes_$1_flows_$2_s_$3_algo_rev_$trial"
  rm logs/temp_*
done