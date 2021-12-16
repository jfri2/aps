kill $(ps aux | grep '[p]ython3 CamMonitor.py' | awk '{print $2}')
