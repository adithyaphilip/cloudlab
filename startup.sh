sudo apt-get update
sudo apt-get install -y iperf3
sudo apt-get install -y python3-pip
sudo pip3 install netifaces

sudo bash setup_ssh.sh

python3 main.py > main_out 2> main_err