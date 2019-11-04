if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ]
  then
    echo "Usage: fetch_logs_set.sh time_run congestion_algo num_trials"
    exit 1
fi

read -p "Enter total number of flows one after the other : " -a flow_list
read -p "Enter total number of nodes to use one after the other: " -a node_list

for flows in ${flow_list[@]}
do
  for nodes in ${node_list[@]}
  do
    ./fetch_logs.sh $((flows/nodes)) $1 $2 $nodes $3
  done
done