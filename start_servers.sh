NUM_SERVERS_PER_NODE=100


parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h servers_file_pssh "for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h servers_file_pssh "for i in \$(seq 1 \$NUM_SERVERS_PER_NODE); do iperf3 -sD; iperf3 -s -p \$((6000+i)) -D; done;"
