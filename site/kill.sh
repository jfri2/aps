kill $(ps aux | grep '[p]ython3 main.py' | awk '{print $2}')
