for flows in 30000 6000 1200 600
do
  for nodes in 5 10 15
  do
    ./fetch_logs.sh $((flows/nodes)) 600 reno $nodes
  done
done