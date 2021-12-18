rm sensor_data.csv
rm *.o
rm aps
gcc -c i2c.c
gcc -c aps_time.c
gcc -c logger.c
gcc -c main.c
gcc i2c.o aps_time.o logger.o main.o -o aps -l wiringPi
