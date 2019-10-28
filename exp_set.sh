if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ]
  then
    echo "Usage: exp_set.sh test_time congestion_algo num_nodes_total_per_side total_times_repeat"
    exit 1
fi

read -p "Enter total number of flows one after the other : " -a flow_list
read -p "Enter total number of nodes to use one after the other: " -a node_list

for flows in ${flow_list[@]}
do
  for nodes in ${node_list[@]}
  do
    flow_per_node=$((flows / nodes))
    ./rerun_exp.sh $flow_per_node $1 $2 $nodes $3 $4
  done
done
