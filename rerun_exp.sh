if [ -z "$1" ] || [ -z "$2" ] || [ -z "$3" ];
  then
    echo "Usage: rerun_exp.sh num_flows test_time congestion_algo"
    exit 1
fi

# just to ensure the credential store has our password
git config credential.helper store
git checkout -b temp_verify && git push -fu origin temp_verify && git checkout master && git branch -D temp_verify

parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h hosts_file_pssh "for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do sudo kill -9 \$pid; done;"
parallel-ssh -t 0 -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h hosts_file_pssh "cd cloudlab; git pull; bash startup.sh; sudo python3 main.py $1 $2 $3 2>&1 | sudo tee main_combined.out"
# 'cd cloudlab && git pull && sudo python3 main.py 2> main_err > main_out'

cat iperf3_log_parsed* > iperf3_log_parsed_merged
git checkout -b logs_$1_flows_$2_s_$3_algo && git add iperf3_log_parsed* && git commit -m "added logs" \
&& git push -f origin logs_$1_flows_$2_s_$3_algo && git checkout master && git branch -D logs_$1_flows_$2_s_$3_algo