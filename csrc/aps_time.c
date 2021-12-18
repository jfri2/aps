// Includes
#include "aps_time.h"

// Variables

// Function Definitions
void get_time(uint8_t *time_string, uint8_t len)
{
    time_t rawtime;
    struct tm *timeinfo;
    time(&rawtime);
    timeinfo = localtime(&rawtime);    
    strftime(time_string, len, "%Y-%m-%d %H:%M:%S", timeinfo);
}