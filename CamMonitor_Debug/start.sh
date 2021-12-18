#!/bin/sh
while :
do
	nohup python3 /share/aps/CamMonitor_Debug/CamMonitor.py > /share/aps/CamMonitor_Debug/nohup.out &
	sleep 3600
	kill $(ps aux | grep 'CamMonitor.py' | awk '{print $2}')
done
#nohup python3 /share/aps/CamMonitor_Debug/CamMonitor.py &
