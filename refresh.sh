parallel-ssh -h setup_cl_clients -t 0 'sudo rm -Rf cloudlab && git clone https://github.com/adithyaphilip/cloudlab --single-branch /users/aphilip/cloudlab && cd /users/aphilip/cloudlab && bash startup.sh'

parallel-ssh -h setup_cl_clients -t 0 'sudo tc qdisc del dev ens1f1 root'