if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ] || [ -z "$4" ] || [ -z "$5" ];
  then
    echo "Usage: rerun_exp.sh num_flows_per_node test_time congestion_algo num_nodes_to_use_per_side num_nodes_total_per_side"
    exit 1
fi

IP_PREFIX=192.168.1.
CLIENT_PSSH_FILE=hosts_file_pssh
SERVER_PSSH_FILE=servers_file_pssh

# just to ensure the credential store has our password
git config credential.helper store
git checkout -b temp_verify && git push -fu origin temp_verify && git checkout master && git branch -D temp_verify

echo "Configuring client list"
rm $CLIENT_PSSH_FILE
for i in $(seq 1 $4); do echo $IP_PREFIX$i >> $CLIENT_PSSH_FILE; done

echo "Configuring server list"
rm $SERVER_PSSH_FILE
for i in $(seq $(($5 + 1)) $(($5 + $4)) ); do echo $IP_PREFIX$i >> $SERVER_PSSH_FILE; done

echo "Starting servers"
./start_servers.sh

echo "Using following clients:"
cat $CLIENT_PSSH_FILE

echo "Killing existing iPerf processes on clients"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE "for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"
echo "Running experiments on clients"
parallel-ssh -t 0 -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h $CLIENT_PSSH_FILE "cd cloudlab; git pull; bash startup.sh; sudo python3 main.py $1 $2 $3 2>&1 | sudo tee main_combined.out"
# 'cd cloudlab && git pull && sudo python3 main.py 2> main_err > main_out'
echo "Merging results from clients"
cat iperf3_log_parsed* > iperf3_log_parsed_merged
git checkout -b logs_$1_flows_$2_s_$3_algo && git add iperf3_log_parsed* && git commit -m "added logs" \
&& git push -f origin logs_$1_flows_$2_s_$3_algo && git checkout master && git branch -D logs_$4_nodes_$1_flows_$2_s_$3_algo