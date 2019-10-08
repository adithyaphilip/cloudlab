NUM_SERVERS_PER_NODE=100
NETEM_DELAY_MS=20
SERVER_LIST_FILE=servers_file_pssh

echo "Servers:"
cat $SERVER_LIST_FILE

echo "Setting Netem delay on servers to $NETEM_DELAY_MS ms"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h  $SERVER_LIST_FILE \
"sudo tc qdisc del dev eno50 root; sudo tc qdisc add dev eno50 root netem delay $NETEM_DELAY_MS""ms;"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $SERVER_LIST_FILE \
"for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $SERVER_LIST_FILE \
"for i in \$(seq 1 $NUM_SERVERS_PER_NODE); do iperf3 -s -p \$((6000+i)) -D; done;"
