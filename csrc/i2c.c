// Includes
#include "i2c.h"

// Variables
int32_t file_i2c;

int32_t errnum;

// Function Definitions
void i2c_init(void)
{
    uint8_t *filename = (uint8_t*)"/dev/i2c-1";
    if ((file_i2c = open(filename, O_RDWR)) < 0)
    {
        printf("Failed to open the i2c bus\n");
        errnum = errno;
        fprintf(stderr, "Value of errno: %d\n", errno);
        perror("Error printed by perror");
        fprintf(stderr, "Error opening file: %s\n", strerror(errnum));
    }
}

void i2c_get_bus(int32_t addr)
{
    if (ioctl(file_i2c, I2C_SLAVE, addr) < 0)
    {
        printf("Failed to acquire bus access and/or talk to slave.\n");
    }
}

void i2c_write(uint8_t *buffer, int32_t length)
{
    if (write(file_i2c, buffer, length) != length)
    {
        printf("Failed to write to i2c device\n");
    }
}

void i2c_read(uint8_t *buffer, int32_t length)
{
    int32_t bytes_read = read(file_i2c, buffer, length);
    if (bytes_read != length)
    {
        printf("Failed to read from i2c device, expected %d bytes, got %d bytes\n", length, bytes_read);
    }
}