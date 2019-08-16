
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h hosts_file_pssh "for pid in \$(ps aux | grep -e [i]perf3 | awk '{print \$2}'); do kill -9 \$pid; done;"
parallel-ssh -x "-o StrictHostKeyChecking=no -i ~/.ssh/id_rsa" -h hosts_file_pssh 'cd cloudlab; git pull; sudo python3 main.py &'
# 'cd cloudlab && git pull && sudo python3 main.py 2> main_err > main_out'
