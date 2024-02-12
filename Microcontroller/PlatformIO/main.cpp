#include <Arduino.h>
#include <Stepper.h>
#include "DebugUtils.h"

// timing doesnt need to be exact here
// use digitalRead/Write and delay
// allow one second per frame total for motor stepping & camera operation

#define DEBUG           0

#define STEP1_PIN       2   // MOTOR A1
#define STEP2_PIN       3   // MOTOR A2
#define STEP3_PIN       4   // MOTOR B1
#define STEP4_PIN       5   // MOTOR B2
// #define STEP_FWD_PIN    6   // SWITCH - STEP MOTOR FORWARD
// #define STEP_REV_PIN    7   // SWITCH - STEP MOTOR BACK
#define STEP_RUN_PIN    8   // SWITCH - MOTOR CONTINUOUS RUN
#define STEP_HALT_PIN   9   // SWITCH - STOP MOTOR
#define BUFFR_ON_PIN    10  // ACTIVE HIGH - TRIGGERS CAMERA BY ENABLING 74LS126
#define STEP_ENABLE     11  // ENABLE MOTOR - use one pin for both enables
#define LED_INT_PIN     13  // INTERNAL LED for indication

#define SHORT_DELAY     250
#define LONG_DELAY      500

// constants
const uint8_t STEPS_PER_REV = 48; // steps per motor revolution
const uint32_t DEBOUNCE_TIME = 250; // debounce timing for buttons (ms)

// timers for switches
// uint32_t timerFwdSwitch = 0;
// uint32_t timerRevSwitch = 0;
uint32_t timerRunSwitch = 0;
uint32_t timerHaltSwitch = 0;
bool systemRunning = false; // control system for halt / run modes

// set up stepper motor control
Stepper motorStepper(STEPS_PER_REV, STEP1_PIN, STEP2_PIN, STEP3_PIN, STEP4_PIN);

void stepMotor(int stepAmount) {
    digitalWrite(STEP_ENABLE, HIGH);    // enable motor
    delay(10);                          // wait for signal to propagate

    motorStepper.step(stepAmount);      // step motor
    DEBUG_PRINT("Motor stepped", NULL);
    delay(SHORT_DELAY);                 // wait for stabilisation

    digitalWrite(BUFFR_ON_PIN, HIGH);   // camera trigger & LED on
    digitalWrite(LED_INT_PIN, HIGH);

    delay(LONG_DELAY);                 // wait to allow shutter to operate

    digitalWrite(BUFFR_ON_PIN, LOW);    // camera trigger & LED off
    digitalWrite(LED_INT_PIN, LOW);
    
    digitalWrite(STEP_ENABLE, LOW);     // disable motor when not in use to reduce power (and heat)
    delay(LONG_DELAY);                  // wait to allow camera to process
}

void setup() {
    if (DEBUG) {
        Serial.begin(9600);
    }

    // pin setups
    // pinMode(STEP_FWD_PIN, INPUT);
    // pinMode(STEP_REV_PIN, INPUT);
    pinMode(STEP_RUN_PIN, INPUT);
    pinMode(STEP_HALT_PIN, INPUT);
    pinMode(BUFFR_ON_PIN, OUTPUT);
    pinMode(STEP_ENABLE, OUTPUT);
    pinMode(LED_INT_PIN, OUTPUT);

    digitalWrite(BUFFR_ON_PIN, LOW); // initial state with trigger off
    digitalWrite(STEP_ENABLE, LOW); // initial state with motor off
    digitalWrite(LED_INT_PIN, LOW); // initial state with LED off
}

void loop() {
    // read switch states
    // uint8_t fwdPinState = digitalRead(STEP_FWD_PIN);
    // uint8_t revPinState = digitalRead(STEP_REV_PIN);
    uint8_t runPinState = digitalRead(STEP_RUN_PIN);
    uint8_t haltPinState = digitalRead(STEP_HALT_PIN);

    // DEBUG_PRINT("fwdPinState", fwdPinState);
    // DEBUG_PRINT("revPinState", revPinState);
    DEBUG_PRINT("runPinState", runPinState);
    DEBUG_PRINT("haltPinState", haltPinState);
    DEBUG_PRINT("systemRunning", systemRunning);

    // if ((timerFwdSwitch == 0) & (fwdPinState == HIGH)) {
    //     timerFwdSwitch = millis();
    // }
    // if ((timerRevSwitch == 0) & (revPinState == HIGH)) {
    //     timerRevSwitch = millis();
    // }
    if ((timerRunSwitch == 0) & (runPinState == HIGH)) {
        timerRunSwitch = millis();
    }
    if ((timerHaltSwitch == 0) & (haltPinState == HIGH)) {
        timerHaltSwitch = millis();
    }

    if (!systemRunning) {
        // system in standby mode waiting for input
        // if ((timerFwdSwitch > 0) && ((millis() - timerFwdSwitch) > DEBOUNCE_TIME)) {
        //     stepMotor(1); // step motor forward once
        //     timerFwdSwitch = 0; // reset
        // }
        // if ((timerRevSwitch > 0) && ((millis() - timerRevSwitch) > DEBOUNCE_TIME)) {
        //     stepMotor(-1); // step motor backwards once
        //     timerRevSwitch = 0; // reset
        // }
        if ((timerRunSwitch > 0) && ((millis() - timerRunSwitch) > DEBOUNCE_TIME)) {
            // set autorun mode
            systemRunning = true;
            timerRunSwitch = 0; // reset
        }
    } else {
        // system is in run mode
        if ((timerHaltSwitch > 0) && ((millis() - timerHaltSwitch) > DEBOUNCE_TIME)) {
            // halt system
            systemRunning = false;
            timerHaltSwitch = 0; // reset
        }
    }

    // step motor if system is in run mode
    // run this code outside of the above statement because the above can change the state
    // this will be called continuously until halted by the user
    // the delay built into stepMotor() will stop this from occuring too fast
    if (systemRunning) {
        stepMotor(1);
    }

    if (DEBUG) {
        delay(1000);
    }

}
