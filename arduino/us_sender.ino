/*
 * Ultraschall-Sende-Routine
 * 40kHz PWM an Arduino-Pin 11 für 200us (8 Zyklen) alle 200ms
 */

void startTransducer()
{
  TCCR2A = _BV(COM2A0) | _BV(WGM21) | _BV(WGM20);
  TCCR2B = _BV(WGM22) | _BV(CS20);
  OCR2A = B11000111; // 199, so timer2 counts from 0 to 199 (200 cycles at 16 MHz)
}
void stopTransducer()
{
  TCCR2A = 0;
  TCCR2B = 0; // I think this is all that is needed since setting the CS bits to zero stops the timer.
  TCNT2 = 0;
}
unsigned long Time = 0; 
void setup()
{
  pinMode(11, OUTPUT);
}

void loop()
{
  if(micros() - Time > 200000) {
    Time = micros();
    startTransducer();
    delayMicroseconds(199);
    stopTransducer();
  }
}
