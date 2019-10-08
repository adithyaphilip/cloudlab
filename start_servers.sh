NUM_SERVERS_PER_NODE=100
NETEM_DELAY_MS=20
SERVER_LIST_FILE=servers_file_pssh
TOT_SERVER_LIST_FILE=tot_servers_file_pssh
BASE_PORT=6000

echo "Servers:"
cat $SERVER_LIST_FILE

echo "Setting Netem delay on servers to $NETEM_DELAY_MS ms"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h  $SERVER_LIST_FILE \
"sudo tc qdisc del dev eno50 root;sudo tc qdisc add dev eno50 root netem delay $NETEM_DELAY_MS""ms limit 100000000";
echo "Killing existing iperf processes on all servers"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $TOT_SERVER_LIST_FILE \
"for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"
echo "Starting servers, with port numbers $((BASE_PORT + 1)) through $((BASE_PORT + NUM_SERVERS_PER_NODE))"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $SERVER_LIST_FILE \
"for i in \$(seq 1 $NUM_SERVERS_PER_NODE); do iperf3 -s -p \$(($BASE_PORT+i)) -D; done;"
