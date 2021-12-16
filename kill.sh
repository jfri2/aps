sudo kill $(ps aux | grep 'CamMonitor.py' | awk '{print $2}')
sudo kill $(ps aux | grep 'aps' | awk '{print $2}')
