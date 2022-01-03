/*
 * logger.h
 *
 * Copyright (c) 2022 John Fritz
 * MIT License, see license.md for full license text
 */

#ifndef LOGGER_H
#define LOGGER_H

// Includes
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "aps_time.h"

// Variables
uint8_t log_message[100];
uint8_t logfilepath[100];

// Function Declarations
void log_header(uint8_t *header);
void log_event(uint8_t *event);

#endif // LOGGER_H