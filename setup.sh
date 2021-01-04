#!/bin/bash
echo "Installing Swift 5.3.1..."

# Update and upgrade anything you can
sudo apt-get update
sudo apt-get upgrade

# Install swift, this was the latest release at the time
wget https://swift.org/builds/swift-5.3.1-release/ubuntu1804/swift-5.3.1-RELEASE/swift-5.3.1-RELEASE-ubuntu18.04.tar.gz
tar xzf swift-5.3.1-RELEASE-ubuntu18.04.tar.gz

# Remove the tar file
sudo rm -rf swift-5.3.1-RELEASE-ubuntu18.04.tar.gz

# Remove an existing swift folder if it exists, and replace it with the new swift folder
sudo rm -rf /usr/share/swift
sudo mv swift-5.3.1-RELEASE-ubuntu18.04/ /usr/share/swift

# Add swift to the PATH
sudo echo "export PATH=/usr/share/swift/usr/bin:$PATH" >> ~/.bashrc
source  ~/.bashrc

# Install this dependency (MUST)
sudo apt-get install libpython2.7 

echo "Swift 5.3.1 installed..."

echo "Installing vapor via vapor toolbox"
# dependencies
sudo apt-get install clang libicu-dev libatomic1 build-essential pkg-config libcurl3 
sudo apt-get install openssl libssl-dev zlib1g-dev libsqlite3-dev 
sudo apt-get install libcurl4-openssl-dev 

git clone https://github.com/vapor/toolbox.git
cd toolbox
#git checkout 18.3.0
sudo rm -rf .build
make install 

#swift build -c release --disable-sandbox --enable-test-discovery
#sudo mv .build/release/vapor /usr/local/bin
swift package update

# allow http traffic through the firewall on this instance (may not need to)
sudo ufw allow http

# note, the vapor project must already be built for the supervisor to work. it doesn't handle the build currently
cd myProject
sudo rm -rf .build
sudo vapor build 

# set up flask, enable virtual environment, and install flask in the venv
cd dojo_scraper
sudo apt-get install python3-venv
python3 -m venv venv
. venv/bin/activate
pip install Flask

# set up supervisor 
cd ..
sudo apt-get install supervisor
# sudo nano /etc/supervisor/conf.d/dojo-ubuntu.conf
echo "" > /etc/supervisor/conf.d/dojo-ubuntu.conf # clear any existing services
echo "[program:dojo-vapor]\n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf
echo "command=sudo ./deploy.sh \n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf
#echo "command=sudo /home/ubuntu/dojo/myProject/.build/release/Run serve\n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf
echo "directory=/home/ubuntu/dojo/myProject\n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf
echo "user=ubuntu\n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf
echo "stdout_logfile=/var/log/supervisor/%(program_name)-stdout.log\n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf
echo "stderr_logfile=/var/log/supervisor/%(program_name)-stderr.log\n" >> /etc/supervisor/conf.d/dojo-ubuntu.conf



sudo supervisorctl reread
sudo supervisorctl add dojo-vapor
sudo supervisorctl status

