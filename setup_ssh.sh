#!/bin/sh

HOME=/users/aphilip
# Create the user SSH directory, just in case.
mkdir $HOME/.ssh && chmod 700 $HOME/.ssh

# Retrieve the server-generated RSA private key.
geni-get key > $HOME/.ssh/id_rsa
chmod 600 $HOME/.ssh/id_rsa

# Derive the corresponding public key portion.
ssh-keygen -y -f $HOME/.ssh/id_rsa > $HOME/.ssh/id_rsa.pub

# By default only 10 nodes can simultaneously wait for authentication, so sometimes logs were not copied.
if [ -z "$(cat /etc/ssh/sshd_config | grep 'MaxStartups 1024')" ]
then
  echo "Setting MaxStartups to 1024 for SSH"
  echo 'MaxStartups 1024' | sudo tee -a /etc/ssh/sshd_config > /dev/null
  sudo service sshd restart
fi

# If you want to permit login authenticated by the auto-generated key,
# then append the public half to the authorized_keys file:s
grep -q -f $HOME/.ssh/id_rsa.pub $HOME/.ssh/authorized_keys || cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys

chown aphilip -R $HOME