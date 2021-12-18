./build.sh
sudo kill $(ps aux | grep 'aps' | awk '{print $2}')
./aps
