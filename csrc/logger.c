/*
 * logger.c
 *
 * Copyright (c) 2022 John Fritz
 * MIT License, see license.md for full license text
 */

// Includes
#include "logger.h"

// Variables
FILE *logfile;

// Function Definintions
void log_header(uint8_t *header)
{
    uint8_t time_string[20] = {};
    get_time2(time_string, 20);
    sprintf(logfilepath, "./data/%s-sensor_data.csv", time_string);
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