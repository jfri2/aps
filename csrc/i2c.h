#ifndef I2C_H
#define I2C_H

// Includes
#include <unistd.h>				//Needed for I2C port
#include <fcntl.h>				//Needed for I2C port
#include <sys/ioctl.h>			//Needed for I2C port
#include <linux/i2c-dev.h>		//Needed for I2C port
#include <stdio.h>
#include <errno.h>
#include <wiringPi.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <math.h>
#include <errno.h>

// Function Declarations
void i2c_init(void);
void i2c_get_bus(int32_t addr);
void i2c_write(uint8_t *buffer, int32_t length);
void i2c_read(uint8_t *buffer, int32_t length);

#endif // I2C_H