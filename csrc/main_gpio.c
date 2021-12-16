#include <wiringPi.h>

int main(void)
{
    // Red LED: Physical pin 18, BCM GPIO24, and WiringPi pin 5.
    const int pump1 = 0;
    const int pump2 = 2;
    const int pump3 = 3;

    wiringPiSetup();

    pinMode(pump1, OUTPUT);
    pinMode(pump2, OUTPUT);
    pinMode(pump3, OUTPUT);

    while (1) {
        digitalWrite(pump1, HIGH);
        delay(10000);
        digitalWrite(pump1, LOW);
        digitalWrite(pump2, HIGH);
        delay(10000);
        digitalWrite(pump2, LOW);
        digitalWrite(pump3, HIGH);
        delay(30000);
        digitalWrite(pump3, LOW);
        delay(5000);
    }

    return 0;
}

