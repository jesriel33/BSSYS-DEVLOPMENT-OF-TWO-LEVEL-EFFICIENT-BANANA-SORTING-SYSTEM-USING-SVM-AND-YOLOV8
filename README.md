# guid for installation for defendencies

# python Installation verison 3.12.7
```
sudo apt update
```
```
sudo apt install build-essential zlib1g-dev libncurses5-dev libgdbm-dev libnss3-dev libssl-dev libreadline-dev libffi-dev wget
```
```
cd /tmp

wget https://www.python.org/ftp/python/3.12.7/Python-3.12.7.tgz

tar -xf Python-3.12.7.tgz

cd Python-3.12.7

./configure --enable-optimizations

sudo make install

python3 --version
```
# how to enable ssh 
```
sudo apt update
```
```
sudo apt install openssh-server -y
```
```
sudo systemctl status ssh
```
```
sudo systemctl start ssh
```
```
sudo systemctl enable ssh
```
```
sudo ufw allow 22/tcp
```
```
sudo ufw status
```
# Install script libraries
```
sudo apt install python3 python3-pip python3-venv -y
python3.12 -m venv env_lib-env
source env_lib-env/bin/activate
pip3 install wheel
pip3 install -r requirements.txt
deactivate
exit
```

