NUM_SERVERS_PER_NODE=500
SERVER_LIST_FILE=servers_file_pssh
SERVER_DELAY_2_PSSH_FILE=servers_delay2_file_pssh
TOT_SERVER_LIST_FILE=tot_servers_file_pssh
BASE_PORT=6000
BASE_UDP_PORT=2000

if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ]; then
  echo "Usage: start_servers.sh congestion_algo num_nodes_tot_side if_name netem_delay_ms_1 netem_delay_ms_2"
  exit 1
fi
IF_NAME=$3
NETEM_DELAY_MS_1=$4
NETEM_DELAY_MS_2=$5

echo "Servers:"
cat $SERVER_LIST_FILE

readarray -t SERVER_ARR <$SERVER_LIST_FILE

latencies=(10 20 60 80 100 120 140 160 180 200)
echo "Adding netem to servers, since we use forward iPerf now"
for i in $(seq 0 9); do
  LATENCY=${latencies[i]}
  echo "Server: ${SERVER_ARR[$i]}, Latency: $LATENCY"
  ssh -o StrictHostKeyChecking=no -i ~/.ssh/id_rsa ${SERVER_ARR[$i]} \
    "sudo tc qdisc del dev $IF_NAME root; sudo tc qdisc add dev $IF_NAME root netem delay $LATENCY""ms limit 1000000000"
done

echo "Killing existing iperf processes on all servers"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $TOT_SERVER_LIST_FILE \
  "for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"
echo "Killing existing UDP BG traffic clients on all servers (since servers send traffic with reverse iPerf)"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $TOT_SERVER_LIST_FILE \
  "for pid in \$(ps aux | grep -e [u]dp-bg | awk '{print \$2}'); do sudo kill -9 \$pid; done;"

echo "Changing congestion algo to $1 on all servers"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $TOT_SERVER_LIST_FILE \
  "sudo sysctl net.ipv4.tcp_congestion_control=$1"

echo "Updating servers to latest git repo at $(TZ=EST5EDT date)"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $SERVER_LIST_FILE \
  "cd cloudlab; git pull; bash startup.sh stale;"

echo "Waiting 60s just in case"
sleep 60

echo "Starting servers, with port numbers $((BASE_PORT + 1)) through $((BASE_PORT + NUM_SERVERS_PER_NODE))"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $SERVER_LIST_FILE \
  "for i in \$(seq 1 $NUM_SERVERS_PER_NODE); do iperf3 -s -p \$(($BASE_PORT+i)) -D; done;"
#
#echo "Starting UDP BG Traffic clients (on server nodes), with port numbers $((BASE_UDP_PORT))"
#parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $SERVER_LIST_FILE \
#"nohup python3 ~/cloudlab/udp-bg-client.py 102  $2  $BASE_UDP_PORT > udp-client-1.log 2>&1 &"
