if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]
  then
    echo "Usage: fetch_logs_set.sh time_run congestion_algo num_trials netem_delay_2 variant"
    exit 1
fi

read -p "Enter total number of flows one after the other : " -a flow_list
read -p "Enter total number of nodes to use one after the other: " -a node_list
read -p "Enter total number of delay 2 nodes one after the other: " -a delay_2_counts
read -p "Enter number of base delays one after the other: " -a delays_list

for delay in ${delays_list[@]}
do
  for count in ${delay_2_counts[@]}
  do
    for flows in ${flow_list[@]}
    do
      for nodes in ${node_list[@]}
      do
        ./fetch_logs.sh $((flows/nodes)) $1 $2 $nodes $3 $delay $4 $count $5
        if [ $? -gt 0 ]
        then
          echo "ERROR reported by fetch_logs.sh, exiting"
          exit 1
        fi
      done
    done
  done
done