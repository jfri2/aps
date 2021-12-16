#!/bin/sh
while :
do
	nohup python3 /share/aps/CamMonitor_Debug/CamMonitor.py &
	sleep 900
	kill $(ps aux | grep 'CamMonitor.py' | awk '{print $2}')
done
