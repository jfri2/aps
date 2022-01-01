ps -aux | grep -i 'main.py'
ps -aux | grep -i 'aps'
sudo kill $(ps aux | grep 'main.py' | awk '{print $2}')
sudo kill $(ps aux | grep 'aps' | awk '{print $2}')
