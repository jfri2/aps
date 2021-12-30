#!/bin/sh
while :
do
	nohup python3 -u /share/aps/site/main.py >> /share/aps/site/main.out 2>&1
	sleep 3600
	kill $(ps aux | grep 'main.py' | awk '{print $2}')
done
#nohup python3 /share/aps/site/main.py &
