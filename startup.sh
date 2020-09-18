sudo apt-get update
sudo apt-get install -y iperf3
sudo apt-get install -y python3-pip
sudo apt-get install -y nload
sudo pip3 install netifaces

#if [ -z "$1" ]
#then
#sudo bash setup_ssh.sh
#fi

sudo sysctl -w net.core.rmem_max=2147479552
sudo sysctl -w net.core.wmem_max=2147479552
sudo sysctl -w net.core.rmem_default=2147479552
sudo sysctl -w net.core.wmem_default=2147479552
sudo sysctl -w net.ipv4.tcp_rmem='4096 87380 2147479552'
sudo sysctl -w net.ipv4.tcp_wmem='4096 87380 2147479552'
sudo sysctl -w net.ipv4.tcp_mem='2147479552 2147479552 2147479552'
sudo sysctl -w net.ipv4.route.flush=1

# python3 main.py > main_out 2> main_err