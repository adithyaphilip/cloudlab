if [ -z "$1" ]
  then
    echo "Requires 1 argument - number of flows to execute"
    exit 1
fi

# just to ensure the credential store has our password
git checkout -b temp_verify && git push -fu origin temp_verify

parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h hosts_file_pssh "for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do kill -9 \$pid; done;"
parallel-ssh -t 0 -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h hosts_file_pssh "cd cloudlab; git pull; sudo bash startup.sh; sudo python3 main.py $1 2>&1 | sudo tee main_combined.out"
# 'cd cloudlab && git pull && sudo python3 main.py 2> main_err > main_out'

cat iperf3_log_parsed* > iperf3_log_parsed_merged
git checkout -b logs_$1 && git add iperf3_log_parsed* && git commit -m "added logs" && git push -f origin logs_$1 && git checkout master && git branch -D logs_$1