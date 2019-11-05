# WARNING: This file depends on the IP pattern being 192.168.1.* to correctly download files

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ] || [ -z "$7" ]|| [ -z "$8" ]
  then
    echo "Usage: fetch_logs.sh num_flows_per_node time_run congestion_algo num_nodes_used num_trials netem_delay_1_ms netem_delay_2_ms delay_2_node_count"
    exit 1
fi

# NOTE: Currently fetching rev mode only
for trial in $(seq 1 $5)
do
  # just to be safe, clear any remaining past temp logs
  rm logs/temp_*
  GIT_BRANCH_SUFFIX=$4_nodes_$1_flows_$2_s_$3_algo_rev_$6_nm1_$7_nm2_$8_delayed_$trial
  for node in $(seq 1 $4)
  do
    curl -f https://raw.githubusercontent.com/adithyaphilip/cloudlab/logs_$GIT_BRANCH_SUFFIX/iperf3_log_parsed_192.168.1.$node > logs/temp_$node
    if [ $? -gt 0 ]
      then
        echo "ERROR: Could not fetch $GIT_BRANCH_SUFFIX node $node";
        exit 1;
    fi
  done
  cat logs/temp_* > logs/$GIT_BRANCH_SUFFIX
  echo "Downloaded: $GIT_BRANCH_SUFFIX"
  rm logs/temp_*
done