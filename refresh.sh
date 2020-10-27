parallel-ssh -h setup_cl_clients -t 0 'sudo rm -Rf cloudlab && git clone https://github.com/adithyaphilip/cloudlab --single-branch /users/aphilip/cloudlab && cd /users/aphilip/cloudlab && bash startup.sh'

# 2. Install iperf3 onto the nodes
# WARNING: This is just intended to work with UBUNTU 18.04 on the xl170 nodes
parallel-ssh $PSSH_OPTIONS -h setup_cl_clients "sudo apt remove -y iperf3;  cd ~; rm -rf iperf; git clone https://github.com/adithyaphilip/iperf.git && cd iperf && ./bootstrap.sh && ./configure && make && cd .. && sudo rm -f /usr/local/bin/iperf3 /usr/bin/iperf3 && sudo ln -s ~/iperf/src/iperf3 /usr/local/bin/iperf3 && sudo ln -s ~/iperf/src/iperf3 /usr/bin/iperf3"

# 3. If iperf3 runs without this package, no worries if it fails
# NOTE: lib32cz1 is required because of this bug (personally observed on Ubuntu 18.04): https://github.com/esnet/iperf/issues/168
parallel-ssh $PSSH_OPTIONS -h setup_cl_clients "sudo apt update; sudo apt install -y lib32cz1"

parallel-ssh -h setup_cl_clients -t 0 'sudo tc qdisc del dev ens1f1 root'