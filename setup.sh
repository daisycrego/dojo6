#!/bin/bash
echo "Installing Swift 5.3.1..."
sudo su -
apt-get update
apt-get upgrade


wget https://swift.org/builds/swift-5.3.1-release/ubuntu1804/swift-5.3.1-RELEASE/swift-5.3.1-RELEASE-ubuntu18.04.tar.gz
tar xzf swift-5.3.1-RELEASE-ubuntu18.04.tar.gz
rm -r swift-5.3.1-RELEASE-ubuntu18.04.tar.gz
sudo mv swift-5.3.1-RELEASE-ubuntu18.04/ /usr/share/swift
echo "export PATH=/usr/share/swift/usr/bin:$PATH" >> ~/.bashrc
source  ~/.bashrc
apt-get install libpython2.7 # dependency for swift
swift --version
echo "Swift 5.3.1 installed."
echo "Installing vapor via vapor toolbox"
git clone https://github.com/vapor/toolbox.git
cd toolbox
git checkout 18.3.0
sudo rm -r .build
swift build -c release --disable-sandbox --enable-test-discovery
vapor --version
