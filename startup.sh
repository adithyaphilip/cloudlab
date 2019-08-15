sudo apt-get update
sudo apt-get install -y iperf3
sudo apt-get install -y python3-pip
pip3 install netifaces

python3 main.py > main_out 2> main_err