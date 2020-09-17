if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ]
  then
    echo "Usage: exp_set.sh test_time congestion_algo num_nodes_total_per_side total_times_repeat type_2_netem_delay_ms variant"
    exit 1
fi

read -p "Enter total number of flows one after the other : " -a flow_list
read -p "Enter total number of nodes to use one after the other: " -a node_list
read -p "Enter number of nodes using delay type 2 one after the other: " -a delayed_node_count_list
read -p "Enter number of base delays one after the other: " -a delays_list

for base_delay in ${delays_list[@]}
do
  for delayed_count in ${delayed_node_count_list[@]}
  do
    for flows in ${flow_list[@]}
    do
      for nodes in ${node_list[@]}
      do
        flow_per_node=$((flows / nodes))
        ./rerun_exp.sh $flow_per_node $1 $2 $nodes $3 $4 $base_delay $5 $delayed_count $6
      done
    done
  done
done
