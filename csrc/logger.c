// Includes
#include "logger.h"

// Variables
FILE *logfile;
uint8_t *logfilepath = "./sensor_data.csv";

// Function Definintions
void log_header(uint8_t *header)
{
    printf("%s\n", header);
    logfile = fopen(logfilepath, "a");
    fprintf(logfile, "%s\n", header);
    fclose(logfile);
}    

void log_event(uint8_t *event)
{    
    uint8_t time_string[20] = {};
    get_time(time_string, 20);
    printf("%s,%s\n", time_string, event);
    logfile = fopen(logfilepath, "a");
    fprintf(logfile, "%s,%s\n", time_string, event);
    fclose(logfile);
}