#include "i2c.h"
#include "aps_time.h"
#include "logger.h"
#include <stdio.h>
#include <errno.h>
#include <wiringPi.h>
#include <stdint.h>
#include <stdlib.h>
#include <time.h>
#include <string.h>
#include <math.h>

// Macros
#define COUNT_OF(x) ((sizeof(x)/sizeof(0[x])) / ((size_t)(!(sizeof(x) % sizeof(0[x])))))

// Defines
#define NUM_SAMPLES 100

// Function declarations
void get_data(void);
void apply_fta(void);
void resetManualWateringPump1(void);
void resetManualWateringPump2(void);
void resetManualWateringPump3(void);
void resetPumps(void);
void testPumps(void);
void waterPlants(int32_t pump, int32_t wateringTime);
void shtc3_init(void);
void shtc3_getData(float *temperature, float *humidity);
void soilsensor_init(int32_t addr);
uint16_t soilsensor_getData(int32_t addr);
int32_t comp(const void* elem1, const void *elem2);
int32_t compf(const void* elem1, const void *elem2);
float fta(int32_t* samples, uint32_t len, uint32_t k);
float ftaf(float* samples, uint32_t len, uint32_t k);

// Global Variables
//extern int errno;
uint8_t *pump1path = "./pumps/pump1.txt";
uint8_t *pump2path = "./pumps/pump2.txt";
uint8_t *pump3path = "./pumps/pump3.txt";
uint8_t *killSwitchPath = "./pumps/killswitch.txt";
uint8_t *testPumpPath = "./pumps/testpumps.txt";
const int32_t pump1_pin = 0;
const int32_t pump2_pin = 2;
const int32_t pump3_pin = 3;
FILE *pump1File;
FILE *pump2File;
FILE *pump3File;
FILE *killSwitchFile;
FILE *testPumpFile;
uint8_t killSwitch = 0;
uint8_t testPump = 0;

int32_t soilsensor1_addr = 0x37;
int32_t soilsensor2_addr = 0x38;
int32_t soilsensor3_addr = 0x36;
//int32_t soilsensor4_addr = 0x39;
uint16_t moisture1Threshold = 550;      // Threshold to water plants
uint16_t moisture2Threshold = 550;      // Threshold to water plants
uint16_t moisture3Threshold = 550;      // Threshold to water plants
float temperature[NUM_SAMPLES];
float humidity[NUM_SAMPLES];
int32_t moisture1[NUM_SAMPLES];
int32_t moisture2[NUM_SAMPLES];
int32_t moisture3[NUM_SAMPLES];
float temperatureFiltered = 0;
float temperatureFilteredF = 0;
float humidityFiltered = 0;
float moisture1Filtered = 0;
float moisture2Filtered = 0;
float moisture3Filtered = 0;
int8_t wateringEvent1 = 0;
int8_t wateringEvent2 = 0;
int8_t wateringEvent3 = 0;    
int32_t wateringDelay = 120 * 60;   // Seconds
int32_t wateringTime1 = 20000;      // Milliseconds
int32_t wateringTime2 = 20000;      // Milliseconds
int32_t wateringTime3 = 20000;      // Milliseconds
uint8_t pump1ManualOn = 0;
uint8_t pump2ManualOn = 0;
uint8_t pump3ManualOn = 0;       

// Main
int main(void)
{   
    int32_t lastMeasurementTime = 0;
    uint32_t measurementDelayMs = 1000 * 60;    // 60 seconds  
    int32_t currentTime = 0;    
    int32_t lastWateringTime1 = time(NULL);
    int32_t lastWateringTime2 = time(NULL);
    int32_t lastWateringTime3 = time(NULL);   

    printf("I2C Comms Start\n");       
    i2c_init();
    shtc3_init();
    wiringPiSetup();
    soilsensor_init(soilsensor1_addr);
    soilsensor_init(soilsensor2_addr);
    soilsensor_init(soilsensor3_addr);
    resetPumps();
    
    delay(1000);
    
    log_header("Timestamp,Temp_degC,Temp_degF,RH_percent,Moisture_1,Moisture_2,Moisture_3,WateringEventPump1,WateringEventPump2,WateringEventPump3");
    
	while(1)
    {   
        // Update current time
        currentTime = time(NULL);

        // Check to see if we need to perform a measurement
        if (currentTime > (lastMeasurementTime + measurementDelayMs))
        {   
            // Sample sensors NUM_SAMPLES times
            get_data();

            // Apply Fault Tolerant Averaging to samples
            apply_fta();

            // Convert degrees C to degrees F
            temperatureFilteredF = temperatureFiltered * 1.8 + 32;   

            // Log sensor data                 
            sprintf(log_message, "%.1f,%.1f,%.2f,%.0f,%.0f,%.0f,0,0,0", temperatureFiltered, temperatureFilteredF, humidityFiltered, moisture1Filtered, moisture2Filtered, moisture3Filtered);
            log_event(log_message); 
        }
       
        // Check pump files to determine if anything needs watering
        pump1File = fopen(pump1path, "r");
        if (pump1File)
        {
            pump1ManualOn = getc(pump1File) - 48;
            if (pump1ManualOn)
            {
                printf("Pump1 reads: %d\n", pump1ManualOn);
                printf("Manual watering of Pump1 plants commanded\n");
            }
        }
        fclose(pump1File);       

        pump2File = fopen(pump2path, "r");
        if (pump2File)
        {
            pump2ManualOn = getc(pump2File) - 48;
            if (pump2ManualOn)
            {
                printf("Pump2 reads: %d\n", pump2ManualOn);
                printf("Manual watering of Pump2 plants commanded\n");
            }            
        }
        fclose(pump2File);          

        pump3File = fopen(pump3path, "r");
        if (pump3File)
        {
            pump3ManualOn = getc(pump3File) - 48;
            if (pump3ManualOn)
            {
                printf("Pump3 reads: %d\n", pump3ManualOn);

            }              
        }
        fclose(pump3File);         

        // Check kill switch file, if it reads 1 do not allow watering to happen
        killSwitchFile = fopen(killSwitchPath, "r");
        if (killSwitchFile)
        {
            killSwitch = getc(killSwitchFile) - 48;
            if (killSwitch)
            {
                resetPumps();
                printf("Kill switch engaged, all pumps stopped\n");
            }            
        }
        fclose(killSwitchFile);           
        
        // Check which plant groups need watering
        if (killSwitch == 0)
        {
            // Test Pumps
            testPumpFile = fopen(testPumpPath, "r");
            if (testPumpFile)
            {
                testPump = getc(testPumpFile) - 48;
                if (testPump == 1)
                {
                    printf("Testing Pumps\n");
                    testPumps();
                }
                else
                {
                    fclose(testPumpFile);
                }
            }
            else
            {
                fclose(testPumpFile);
            }            
            
            // Normal Watering
            if (((currentTime > (lastWateringTime1 + wateringDelay)) && ((moisture1Filtered < moisture1Threshold)) || (pump1ManualOn == 1)))
            {
                wateringEvent1 = 1;
                if (pump1ManualOn == 1)
                {
                    printf("Manual watering of Pump1 plants commanded\n");   
                }                 
            }  
            if (((currentTime > (lastWateringTime2 + wateringDelay)) && ((moisture2Filtered < moisture2Threshold)) || (pump2ManualOn == 1)))
            {
                wateringEvent2 = 1;
                if (pump2ManualOn == 1)
                {
                    printf("Manual watering of Pump2 plants commanded\n");   
                }                 
            }      
            if (((currentTime > (lastWateringTime3 + wateringDelay)) && ((moisture3Filtered < moisture3Threshold)) || (pump3ManualOn == 1)))
            {
                wateringEvent3 = 1;
                if (pump3ManualOn == 1)
                {
                    printf("Manual watering of Pump3 plants commanded\n");   
                }                
            }            
            
            // Water plant groups that need watering
            if (wateringEvent1)
            {
                sprintf(log_message, "%.1f,%.1f,%.2f,%.0f,%.0f,%.0f,0,0,0", temperatureFiltered, temperatureFilteredF, humidityFiltered, moisture1Filtered, moisture2Filtered, moisture3Filtered);
                log_event(log_message);  
                waterPlants(pump1_pin, wateringTime1);
                lastWateringTime1 = time(NULL);
                // Clear flag for manual watering if enabled
                resetManualWateringPump1();
                wateringEvent1 = 0;
            }

            if (wateringEvent2)
            {
                sprintf(log_message, "%.1f,%.1f,%.2f,%.0f,%.0f,%.0f,0,0,0", temperatureFiltered, temperatureFilteredF, humidityFiltered, moisture1Filtered, moisture2Filtered, moisture3Filtered);
                log_event(log_message);  
                waterPlants(pump2_pin, wateringTime2);
                lastWateringTime1 = time(NULL);
                // Clear flag for manual watering if enabled
                resetManualWateringPump2();
                wateringEvent2 = 0;
            }
            
            if (wateringEvent3)
            {
                sprintf(log_message, "%.1f,%.1f,%.2f,%.0f,%.0f,%.0f,0,0,0", temperatureFiltered, temperatureFilteredF, humidityFiltered, moisture1Filtered, moisture2Filtered, moisture3Filtered);
                log_event(log_message);  
                waterPlants(pump3_pin, wateringTime3);
                lastWateringTime3 = time(NULL);
                // Clear flag for manual watering if enabled
                resetManualWateringPump3();
                wateringEvent3 = 0;
            }
        }
    }
    return (0);
}

void get_data(void)
{
    for (uint32_t i = 0; i < NUM_SAMPLES; i++)
    {
        shtc3_getData(&temperature[i], &humidity[i]); 
        moisture1[i] = (int32_t)soilsensor_getData(soilsensor1_addr);
        moisture2[i] = (int32_t)soilsensor_getData(soilsensor2_addr);
        moisture3[i] = (int32_t)soilsensor_getData(soilsensor3_addr);             

        // Uncomment to enable debug for individual measurements
        // sprintf(log_message, "TEST %.1f,%.1f,%.2f,%d,%d,%d,0,0,0", temperature[i], 0, humidity[i], moisture1[i], moisture2[i], moisture3[i]);
        // log_event(log_message);            
    }
}

void apply_fta(void)
{
    uint32_t k = (NUM_SAMPLES / 10) + 1;      // Approx 20% of data gets filtered out of average
    temperatureFiltered = ftaf(temperature, COUNT_OF(temperature), k);
    humidityFiltered = ftaf(humidity, COUNT_OF(humidity), k);
    moisture1Filtered = fta((int32_t*)moisture1, COUNT_OF(moisture1), k);
    moisture2Filtered = fta((int32_t*)moisture2, COUNT_OF(moisture2), k);
    moisture3Filtered = fta((int32_t*)moisture3, COUNT_OF(moisture3), k);
}

void resetManualWateringPump1(void)
{
    pump1File = fopen(pump1path, "w");
    if (pump1File)
    {
        fputs("0", pump1File);
        printf("Reset Manual Watering Flag for Pump1\n");        
    }
    else
    {
        delay(100);
        pump1File = fopen(pump1path, "w");
        if (pump1File)
        {
            fputs("0", pump1File);
            printf("Reset Manual Watering Flag for Pump1\n");      
        }
    }       
    fclose(pump1File); 
}

void resetManualWateringPump2(void)
{
    pump2File = fopen(pump2path, "w");
    if (pump1File)
    {
        fputs("0", pump2File);
        printf("Reset Manual Watering Flag for Pump2\n");        
    }
    else
    {
        delay(100);
        pump2File = fopen(pump2path, "w");
        if (pump1File)
        {
            fputs("0", pump2File);
            printf("Reset Manual Watering Flag for Pump2\n");      
        }
    }       
    fclose(pump2File);     
}

void resetManualWateringPump3(void)
{
    pump3File = fopen(pump3path, "w");
    if (pump3File)
    {
        fputs("0", pump3File);
        printf("Reset Manual Watering Flag for Pump3\n");        
    }
    else
    {
        delay(100);
        pump3File = fopen(pump3path, "w");
        if (pump3File)
        {
            fputs("0", pump3File);
            printf("Reset Manual Watering Flag for Pump3\n");      
        }
    }       
    fclose(pump3File);         
}

void resetPumps(void)
{
    pinMode(pump1_pin, OUTPUT);
    pinMode(pump2_pin, OUTPUT);
    pinMode(pump3_pin, OUTPUT);
    digitalWrite(pump1_pin, LOW);
    digitalWrite(pump2_pin, LOW);
    digitalWrite(pump3_pin, LOW);    
    printf("Pumps Reset\n");
}

void testPumps(void)
{
    int32_t testWateringTime = 3000;
    delay(3000);
    waterPlants(pump1_pin, testWateringTime);
    waterPlants(pump2_pin, testWateringTime);
    waterPlants(pump3_pin, testWateringTime);
    
    testPumpFile = fopen(testPumpPath, "w");
    if (testPumpFile)
    {
        fputs("0", testPumpFile);
        printf("Reset Test Pump File\n");        
    }
    else
    {
        delay(100);
        testPumpFile = testPumpFile = fopen(testPumpPath, "w");
        if (testPumpFile)
        {
            fputs("0", testPumpFile);
            printf("Reset Test Pump File\n");        
        }
    }       
    fclose(testPumpFile);     
}

void waterPlants(int32_t pump, int32_t wateringTime)
{
    char pumpStr[6];
    switch (pump)
    {
        case 0:
            strcpy(pumpStr, "Pump1");
            break;
        case 2: 
            strcpy(pumpStr, "Pump2");
            break;
        case 3:
            strcpy(pumpStr, "Pump3");
            break;
    }
    const int32_t maxWateringTime = 30000;      // milliseconds
    if (wateringTime > maxWateringTime)
    {
        printf("Watering Time of %d seconds exceeds max watering time of %d seconds\n", wateringTime / 1000, maxWateringTime / 1000);
        printf("Setting watering time to %d seconds\n", maxWateringTime / 1000); 
        wateringTime = maxWateringTime;
    }
    printf("Watering Plants: %s, ON for %d seconds\n", pumpStr, wateringTime / 1000);
    digitalWrite(pump, HIGH);
    delay(wateringTime);
    digitalWrite(pump, LOW);
    resetPumps();
}

void shtc3_init(void)
{
    int32_t shtc3_addr = 0x70;
    int32_t length;
    uint16_t device_id = 0;
    uint16_t device_id_mask = 0b0000100000111111;
    uint16_t expected_device_id = 0b0000100000000111;
    uint8_t buffer[16] = {0};
    int32_t fp;
    
    i2c_get_bus(shtc3_addr);    

    // Write command to read ID register
    buffer[0] = 0xEF;
    buffer[1] = 0xC8;
    length = 2;        
    i2c_write(buffer, length);
    
    // Now read 3 bytes from device and print them
    length = 3;
    i2c_read(buffer, length);        
    
    // Extract device ID and check it
    device_id = (((uint16_t)buffer[0] << 8) | ((uint16_t)buffer[1]));
    if ((device_id & device_id_mask) != expected_device_id)
    {
        printf("SHTC3 Device ID reported is %d, expected %d\n", device_id, expected_device_id);
    }
    else
    {
        printf("SHTC3 Connected\n", device_id);
    }
}

void shtc3_getData(float *temperature, float *humidity)
{
    int32_t shtc3_addr = 0x70;
    uint8_t measurementStart[2] = {0x7C, 0xA2};
    //uint8_t measurementStart[2] = {0x78, 0x66};
    uint8_t measurementRead[6] = {0};
    int16_t intTemp = 0;
    int16_t intHumidity = 0;
    
    i2c_get_bus(shtc3_addr);   // Grab the I2C Bus
    
    // Start the measurement
    i2c_write(measurementStart, 2);
    // Delay for 10ms for the measurement
    delay(10);
    // Read the results, 3 bytes temperature followed by 3 bytes humidity
    i2c_read(measurementRead, 6);
    intTemp = ((uint16_t)measurementRead[0] << 8) | measurementRead[1];
    intHumidity = ((uint16_t)measurementRead[3] << 8) | measurementRead[4];
    // Convert units to degrees C and % relative humidity
    temperature[0] = ((-45.0) + ((175.0 * intTemp) / 65536.0));    
    humidity[0] = 100.0 * (intHumidity / 65536.0);
}

void soilsensor_init(int32_t addr)
{      
    uint8_t txbuf[2] = {0x00, 0x01};      
    uint8_t rxbuf = 0;
    uint8_t ret_addr = 0;
    int32_t fp;
    
    i2c_get_bus(addr);         
        
    // Get HW version info    
    i2c_write(txbuf, 2);
    delay(1);
    i2c_read(&rxbuf, 1);
    
    if (rxbuf = 0x55)
    {
        printf("Soil Sensor 0x%x Connected\n", addr);
    }
    else
    {
        printf("Soil Sensor 0x%x Not Connected, received HW ID of 0x%x instead\n", addr, rxbuf);
    }    
}

uint16_t soilsensor_getData(int32_t addr)
{
    i2c_get_bus(addr);
    uint8_t txbuf[2] = {0x0F, 0x10};
    uint8_t moisture[2] = {0};
    
    i2c_write(txbuf, 2);
    delay(10);
    i2c_read(moisture, 2);
    
    return (((uint16_t)moisture[0] << 8) | moisture[1]);
}

int32_t comp(const void* elem1, const void *elem2)
{
    int32_t f = *((int32_t*) elem1);
    int32_t s = *((int32_t*) elem2);
    if (f > s) 
    {
        return 1;
    }
    else if (f < s)
    {
        return -1;
    }
    else
    {
        return 0;
    }
}

int32_t compf(const void* elem1, const void *elem2)
{
    float f = *((float*) elem1);
    float s = *((float*) elem2);
    if (f > s) 
    {
        return 1;
    }
    else if (f < s)
    {
        return -1;
    }
    else
    {
        return 0;
    }
}

float fta(int32_t* samples, uint32_t len, uint32_t k)
{
    // Sort elements of samples in ascending order
    qsort(samples, len, sizeof(*samples), comp);

    // Average all elements except k elements from top and bottom of array
    float avg = 0;
    for (uint32_t i = k; i < (len - k); i++)
    {
        avg += (float)samples[i];
    }
    avg = avg / (len - (2 * k));
    return (avg);
}

float ftaf(float* samples, uint32_t len, uint32_t k)
{
    // Sort elements of samples in ascending order
    qsort(samples, len, sizeof(*samples), compf);

    // Average all elements except k elements from top and bottom of array
    float avg = 0;
    for (uint32_t i = k; i < (len - k); i++)
    {
        avg += samples[i];
    }
    avg = avg / (len - (2 * k));
    return (avg);
}
