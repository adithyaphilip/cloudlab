parallel-ssh -h setup_cl_clients -t 0 'sudo rm -Rf cloudlab && git clone https://github.com/adithyaphilip/cloudlab --single-branch /users/aphilip/cloudlab && cd /users/aphilip/cloudlab && bash startup.sh'

# 2. Install iperf3 onto the nodes
# NOTE: lib32cz1 is required because of this bug (personally observed on Ubuntu 18.04): https://github.com/esnet/iperf/issues/168
parallel-ssh $PSSH_OPTIONS -h setup_cl_clients "sudo apt remove iperf3; git clone https://github.com/adithyaphilip/iperf.git && cd iperf && ./bootstrap.sh && ./configure && make && sudo make install && sudo apt get update && sudo apt install lib32cz1"

parallel-ssh -h setup_cl_clients -t 0 'sudo tc qdisc del dev ens1f1 root'