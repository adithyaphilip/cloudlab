if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ] || [ -z "$7" ] || [ -z "$8" ] || [ -z "$9" ] || [ -z "${10}" ] || [ -z "${11}" ];
  then
    echo "Usage: rerun_exp.sh num_flows_per_node test_time congestion_algo num_nodes_to_use_per_side num_nodes_total_per_side total_times_repeat netem_delay_ms_1 netem_delay_ms_2 delay_2_nodes variant if_name"
    exit 1
fi

IP_PREFIX=192.168.1.
CLIENT_PSSH_FILE=hosts_file_pssh
CLIENT_TOT_PSSH_FILE=tot_hosts_file_pssh
CLIENT_DELAY_2_PSSH_FILE=delay_2_hosts_file_pssh
SERVER_PSSH_FILE=servers_file_pssh
TOT_SERVER_PSSH_FILE=tot_servers_file_pssh
NETEM_DELAY_MS_1=$7
NETEM_DELAY_MS_2=$8
NETEM_DELAY_2_NODES=$9
BASE_UDP_PORT=2000
VARIANT=${10}
IF_NAME=${11}

# just to ensure the credential store has our password
git config credential.helper store
git checkout -b temp_verify && git push -fu origin temp_verify && git checkout master && git branch -D temp_verify

for trial in $(seq 1 $6)
do
GIT_BRANCH_NAME="$VARIANT"_logs_$4_nodes_$1_flows_$2_s_$3_algo_rev_"$NETEM_DELAY_MS_1"_nm1_"$NETEM_DELAY_MS_2"_nm2_"$NETEM_DELAY_2_NODES"_delayed_$trial

echo Running with $1 flows per node for $2 seconds with $3 CCA using $4 out of $5 nodes per side, trial $trial
echo Using Git Branch $GIT_BRANCH_NAME

# By default only 10 nodes can simultaneously wait for authentication, so sometimes logs were not copied.
if [ -z "$(cat /etc/ssh/sshd_config | grep 'MaxStartups 1024')" ]
then
  echo "Setting MaxStartups to 1024 for SSH"
  echo 'MaxStartups 1024' | sudo tee -a /etc/ssh/sshd_config > /dev/null
  sudo service sshd restart
fi

echo "Configuring client list"
rm $CLIENT_PSSH_FILE
rm $CLIENT_TOT_PSSH_FILE
rm $CLIENT_DELAY_2_PSSH_FILE
for i in $(seq 1 $4); do echo $IP_PREFIX$i >> $CLIENT_PSSH_FILE; done
for i in $(seq 1 $5); do echo $IP_PREFIX$i >> $CLIENT_TOT_PSSH_FILE; done
for i in $(seq 1 $NETEM_DELAY_2_NODES); do echo $IP_PREFIX$i >> $CLIENT_DELAY_2_PSSH_FILE; done

echo "Using following clients:"
cat $CLIENT_PSSH_FILE

echo "Adding netem to clients, since we use reverse iPerf now"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
"sudo tc qdisc del dev $IF_NAME root; sudo tc qdisc add dev $IF_NAME root netem delay $NETEM_DELAY_MS_1""ms limit 1000000000"

echo "Setting specified number clients ($9) to delay type 2 with $NETEM_DELAY_MS_2 delay"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_DELAY_2_PSSH_FILE \
"sudo tc qdisc del dev $IF_NAME root; sudo tc qdisc add dev $IF_NAME root netem delay $NETEM_DELAY_MS_2""ms limit 1000000000"

echo "Killing existing iPerf processes on clients"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_TOT_PSSH_FILE \
"for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"

echo "Killing existing UDP BG traffic servers on all clients (since servers send traffic with reverse iPerf)"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_TOT_PSSH_FILE \
"for pid in \$(ps aux | grep -e [u]dp-bg | awk '{print \$2}'); do sudo kill -9 \$pid; done;"

echo "Setting congestion algo to $3 on client nodes"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_TOT_PSSH_FILE \
"sudo sysctl net.ipv4.tcp_congestion_control=$3"

echo "Updating clients to latest git repo at $(TZ=EST5EDT date)"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
"cd cloudlab; git pull; bash startup.sh stale;"
#
#echo "Starting UDP BG Traffic servers (on client nodes), with port numbers $((BASE_UDP_PORT))"
#parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
#"nohup python3 ~/cloudlab/udp-bg-server.py $BASE_UDP_PORT > udp-server-1.log 2>&1 &"

echo "Configuring server list"
rm $SERVER_PSSH_FILE
rm $TOT_SERVER_PSSH_FILE
for i in $(seq $(($5 + 1)) $(($5 + $4)) ); do echo $IP_PREFIX$i >> $SERVER_PSSH_FILE; done
for i in $(seq $(($5 + 1)) $(($5 + $5)) ); do echo $IP_PREFIX$i >> $TOT_SERVER_PSSH_FILE; done

echo "Starting servers"
./start_servers.sh $3 $5 $IF_NAME

echo "Running experiments on clients at $(TZ=EST5EDT date)"
parallel-ssh -t $(($2 + 600)) -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
"cd cloudlab; sudo python3 main.py $1 $2 $3 $5 2>&1 | sudo tee main_combined.out"
# 'cd cloudlab && git pull && sudo python3 main.py 2> main_err > main_out'

echo "Uploading results from clients"
git checkout -b $GIT_BRANCH_NAME && git add iperf3_log_parsed* && git commit -m "added logs" \
&& git push -f origin $GIT_BRANCH_NAME && git checkout master && git branch -D $GIT_BRANCH_NAME

done