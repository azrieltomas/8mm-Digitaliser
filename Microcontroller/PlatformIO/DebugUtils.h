/*
 * Utility functions to help debugging running code.
 */

#ifndef DEBUGUTILS_H
#define DEBUGUTILS_H

#ifdef DEBUG
    #define DEBUG_PRINT(variable, value)        \
        Serial.print(millis()); \
        Serial.print(": "); \
        Serial.print(variable); \
        Serial.print(" "); \
        Serial.println(value);
#else
    #define DEBUG_PRINT(variable, value)
#endif

#endif