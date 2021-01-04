#/bin/bash

sudo rm -rf /home/ubuntu/dojo/myProject/.build
cd /home/ubuntu/dojo/myProject
sudo vapor build
sudo /home/ubuntu/dojo/myProject/.build/release/Run serve