//tracking station v0.5
#define VERSION "v0.5"
#define DEVICEID 2

#include <SPI.h>
#include <Mirf.h>
#include <nRF24L01.h>
#include <MirfHardwareSpiDriver.h>

// NRF24 settings
#define RFADDR "alex1"
#define RFBASE "alex0"
#define RFCHANNEL 42

//constants
const int MYADDR = DEVICEID;
const int BASEADDR = 1;


// Global Variables
int BatteryVoltage; // in mV
volatile byte State=0;
unsigned long PID=0; // Package identifier
byte Blink = 10; //let the yoellow LED blink
volatile unsigned long USDetectionTime=0, IRDetectionTime=0;
unsigned long Result =0;

// read PID from EEPROM
unsigned long readPID() {
  return long(0);
  /*
    return ( (EEPROM.read(0) << 24) 
                   + (EEPROM.read(1) << 16) 
                   + (EEPROM.read(2) << 8) 
                   + (EEPROM.read(3) ) );
  */
}

// check Battery Voltage
void readBattery() {
  int pwm;
  BatteryVoltage=analogRead(A0);
  BatteryVoltage=BatteryVoltage*4.88;
  pwm=(BatteryVoltage-3000)/5.0;
  if (pwm>255) pwm=255;
  else if (pwm<0) pwm=0;
  analogWrite(5, pwm);
}


void blink () {
  //digitalWrite(4, Blink%2);
  //the following lines are functionally identical to the line above, but much faster
  // Arduino Pin 4 = PortD Bit 4
  if(Blink%2) {
    PORTD |= (1 << 4);    /* setzt Bit 4 an PortD auf 1 ==> HIGH */
  } else {
    PORTD &= ~(1 << 4);   /* loescht Bit 4 an PortD ==> LOW */
  }
}

byte parseMsg() {
  byte data[32];
  Mirf.getData(data);
  if(data[0] == (byte)((MYADDR & 0xFF00) >> 8) && data[1] == (byte)(MYADDR & 0x00FF)) {
    switch(data[7]) {
      case 2:
        State = 5;
        break;
      case 3:
        
        break;
      case 5:
        byte *tmp;
        tmp =(byte *)&Result;
        sendMsg(BASEADDR, (byte)6, tmp);
        break;
      case 99:
        Blink = data[8];
        break;
      case 4:
       //todo
        break;
      default:
        return 0; //kenne Datentyp nicht
    }
  } else {
    return 0; //Nachricht nicht für mich
  }
}

//interrupt service routine pin 2 (PD2)
void ISR_0 () {
  IRDetectionTime = micros();
  State = 10;
}

//interrupt service routine pin 3 (PD3)
void ISR_1 () {
  USDetectionTime = micros();
  State = 20;
  detachInterrupt(1);
}

void sendMsg(int receiver, byte type, byte payload[]) {
  byte data[32];
  Mirf.setTADDR((byte *)RFBASE);
  data[0] = (byte)((receiver & 0xFF00) >> 8 );
  data[1] = (byte)((receiver & 0x00FF));
  data[2] = (byte)((MYADDR & 0xFF00) >> 8 );
  data[3] = (byte)((MYADDR & 0x00FF));
  data[4] = (byte)((PID & 0xFF00000) >> 16 );
  data[5] = (byte)((PID & 0x00FF00) >> 8 );
  data[6] = (byte)((PID & 0x0000FF));
  data[7] = type;
  for(int i = 0; i<24;i++){
    data[i+8] = payload[i];
  }     
  Mirf.send(data);
  PID++;
}

void setup(){
  Serial.begin(9600);
  Serial.print("tracking station ");
  Serial.print(VERSION);
  Serial.print(" - Device ");
  Serial.print(DEVICEID);
  Serial.print("\n");
  
  pinMode(4, OUTPUT); //yellow LED
  pinMode(5, OUTPUT); //red LED
  //pinMode(2, INPUT); 
  //pinMode(3, INPUT);
  //digitalWrite(2, HIGH); //Pullup
  //digitalWrite(3, HIGH); //Pullup
  digitalWrite(4, HIGH);
  digitalWrite(5, HIGH);
  delay(300);
  digitalWrite(4, LOW);
  digitalWrite(5, LOW);

  readBattery();
  Serial.print("Voltage: ");
  Serial.println(BatteryVoltage);

  //init NRF24
  Mirf.spi = &MirfHardwareSpi;
  Mirf.cePin = 9;
  Mirf.csnPin = 10;
  Mirf.init();
  Mirf.setRADDR((byte *)RFADDR);
  Mirf.payload = 32;
  Mirf.channel = RFCHANNEL;
  Mirf.config();
  
  PID = readPID();
  
  Serial.println("Listening..."); 
}

void loop(){
  static unsigned long blinktime=0, batterytime=0;
  unsigned long deltat = 0;
  switch (State) { //Statemachine
    case 0:
      //init
      sendMsg(BASEADDR, (byte)0, (byte*)MYADDR); // Bei der Basisstation melden
      attachInterrupt(0, ISR_0, FALLING); // Interrupt für Infrarot aktivieren
      State = 5;
      Serial.print("init\n");
      break;
    case 2:{
      static unsigned long inittime = 0;
      if( millis() - inittime > 150 )
      {
        byte payload[24] = {0};
        payload[0] = (byte)(((int)MYADDR & 0xFF00) >> 8 );
        payload[1] = (byte)(((int)MYADDR & 0x00FF));
        sendMsg(BASEADDR, (byte)1, payload);
        inittime = millis();
        Serial.print("register\n");
      }
      break;
    }
    case 5:
      //idle
      if(!Mirf.isSending() && Mirf.dataReady()){
        parseMsg();
      }
      if (Blink && millis() - blinktime > 100) {
        blinktime = millis();
        Blink--;
        blink();
      }
      if (millis() - batterytime > 1000) {
        batterytime = millis();
        readBattery();
      }
      //Serial.print(".");
      break;
    case 10:
      //IR detected
      //attachInterrupt(1, ISR_1, FALLING); // US Interrupt aktivieren
      State = 15;
        Serial.print("IR detected\n");
      break;
    case 15:
      //waiting for US
      if (((PIND & 0x08)>>3)^1) {
        USDetectionTime = micros();
        State = 20;
      } else if(micros() - IRDetectionTime > 190000) { // Abbrechen falls nach 100ms kein US detektiert
        Serial.print("US to late ");
        byte tmp[4] = {0,0,0,0};
        Result = 0;
        sendMsg(BASEADDR, (byte)42, tmp);
        State = 5;
        //detachInterrupt(1);
      }
      break;
    case 20:
      //US detected
      deltat = USDetectionTime - IRDetectionTime;
      Result = deltat;
      byte *tmp;
      tmp =(byte *)&deltat;
      sendMsg(BASEADDR, (byte)42, tmp);
      Blink = 2;
      State = 5;
        Serial.print("US detected\n");
        Serial.println(deltat);
      break;
    case 25:
      
      break;
    case 30:
      
      break;
    case 35:
      
      break;
    case 40:
      
      break;
    case 45:
      
      break;
    case 50:
      
      break;
    case 55:
      
      break;
  }
}
