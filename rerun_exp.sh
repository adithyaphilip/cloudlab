if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ] || [ -z "$6" ] || [ -z "$7" ] || [ -z "$8" ] || [ -z "$9" ];
  then
    echo "Usage: rerun_exp.sh num_flows_per_node test_time congestion_algo num_nodes_to_use_per_side num_nodes_total_per_side total_times_repeat netem_delay_ms_1 netem_delay_ms_2 delay_2_nodes"
    exit 1
fi

IP_PREFIX=192.168.1.
CLIENT_PSSH_FILE=hosts_file_pssh
CLIENT_TOT_PSSH_FILE=tot_hosts_file_pssh
CLIENT_DELAY_2_PSSH_FILE=hosts_file_pssh
SERVER_PSSH_FILE=servers_file_pssh
TOT_SERVER_PSSH_FILE=tot_servers_file_pssh
NETEM_DELAY_MS_1=$7
NETEM_DELAY_MS_2=$8
NETEM_DELAY_2_NODES=$9

# just to ensure the credential store has our password
git config credential.helper store
git checkout -b temp_verify && git push -fu origin temp_verify && git checkout master && git branch -D temp_verify

for trial in $(seq 1 $6)
do
GIT_BRANCH_NAME=logs_$4_nodes_$1_flows_$2_s_$3_algo_rev_$trial

echo Running with $1 flows per node for $2 seconds with $3 CCA using $4 out of $5 nodes per side, trial $trial
echo Using Git Branch $GIT_BRANCH_NAME

# By default only 10 nodes can simultaneously wait for authentication, so sometimes logs were not copied.
if [ -z "$(cat /etc/ssh/sshd_config | grep 'MaxStartups 100')" ]
then
  echo "Setting MaxStartups to 100 for SSH"
  echo 'MaxStartups 100' >> /etc/ssh/sshd_config
fi

echo "Configuring client list"
rm $CLIENT_PSSH_FILE
rm $CLIENT_TOT_PSSH_FILE
rm $CLIENT_DELAY_2_PSSH_FILE
for i in $(seq 1 $4); do echo $IP_PREFIX$i >> $CLIENT_PSSH_FILE; done
for i in $(seq 1 $5); do echo $IP_PREFIX$i >> $CLIENT_TOT_PSSH_FILE; done
for i in $(seq 1 $9); do echo $IP_PREFIX$i >> $CLIENT_DELAY_2_PSSH_FILE; done

echo "Using following clients:"
cat $CLIENT_PSSH_FILE

echo "Adding netem to clients, since we use reverse iPerf now"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
"sudo tc qdisc del dev eno50 root; sudo tc qdisc add dev eno50 root netem delay $NETEM_DELAY_MS_1""ms limit 1000000000"

echo "Setting specified number clients to delay type 2 with $NETEM_DELAY_MS_2 delay"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_DELAY_2_PSSH_FILE \
"sudo tc qdisc del dev eno50 root; sudo tc qdisc add dev eno50 root netem delay $NETEM_DELAY_MS_2""ms limit 1000000000"

echo "Killing existing iPerf processes on clients"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_TOT_PSSH_FILE \
"for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"

echo "Waiting 30s just because"
sleep 30

echo "Configuring server list"
rm $SERVER_PSSH_FILE
rm $TOT_SERVER_PSSH_FILE
for i in $(seq $(($5 + 1)) $(($5 + $4)) ); do echo $IP_PREFIX$i >> $SERVER_PSSH_FILE; done
for i in $(seq $(($5 + 1)) $(($5 + $5)) ); do echo $IP_PREFIX$i >> $TOT_SERVER_PSSH_FILE; done

echo "Starting servers"
./start_servers.sh

echo "Updating clients to latest git repo at $(TZ=EST5EDT date)"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
"cd cloudlab; git pull; bash startup.sh;"

echo "Running experiments on clients at $(TZ=EST5EDT date)"
parallel-ssh -t 0 -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE \
"cd cloudlab; sudo python3 main.py $1 $2 $3 $5 2>&1 | sudo tee main_combined.out"
# 'cd cloudlab && git pull && sudo python3 main.py 2> main_err > main_out'

echo "Uploading results from clients"
git checkout -b $GIT_BRANCH_NAME && git add iperf3_log_parsed* && git commit -m "added logs" \
&& git push -f origin $GIT_BRANCH_NAME && git checkout master && git branch -D $GIT_BRANCH_NAME

done