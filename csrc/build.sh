rm *.o
rm aps
gcc -c i2c.c
gcc -c main.c
gcc i2c.o main.o -o aps -l wiringPi
