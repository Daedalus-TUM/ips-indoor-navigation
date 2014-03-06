//tracking station v0.9.1  20130704 1300
#define VERSION "v0.9"
#define DEVICEID 9  //Bitte entsprechend ändern. Auf Quirins Wunsch bitte unbelegte Nummern (3,4) statt 10 und 11

#define VERSIONMAJOR 0
#define VERSIONMINOR 9

#include <SPI.h>
#include <Mirf.h>
#include <nRF24L01.h>
#include <MirfHardwareSpiDriver.h>

// NRF24 settings
#define RFADDR "alex1"
#define RFBASE "alex0"
#define RFCHANNEL 3

//besser als digitalWrite
#define CLR(x,y) (x&=(~(1<<y)))
#define SET(x,y) (x|=(1<<y))


//constants
byte MYID = DEVICEID;
byte Version[2] = {VERSIONMAJOR,VERSIONMINOR};

// Global Variables
int PID = 5;
// Global Variables
int BatteryVoltage; // in mV
volatile byte State=0;
byte Blink = 10; //let the yoellow LED blink
volatile unsigned long USDetectionTime=0, IRDetectionTime=0;
unsigned long Result =0;
byte rotfreq = 0;
byte sync = 0;

// check Battery Voltage
void readBattery() {
  int pwm;
  BatteryVoltage=analogRead(A0);
  BatteryVoltage=BatteryVoltage*4.88;
  pwm=(BatteryVoltage-3300)/5.0;
  if (pwm>255) pwm=255;
  else if (pwm<0) pwm=0;
  rotfreq = byte(pwm);
  //analogWrite(5, pwm);
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


void blinkrot () {
  static byte state = 0;
  static unsigned long blinkredtime = 0;
  if (state == 1 && millis() - blinkredtime > 10 * rotfreq) {
    SET(PORTD, 5);
    state = 0;
  }
  if (state == 0 && millis() - blinkredtime > 1000) {
    blinkredtime = millis();
    CLR(PORTD, 5);
    state = 1;
  }
}



class Packet {
  //byte time;
  unsigned long time;
  byte sent;
  byte data[12]={0};
  
  public:
    Packet (byte dest, byte type, byte *payload) {
      sent = 0;
      //time = millis() % 128;
      time = millis();
      data[0] = dest;
      data[1] = MYID;
      data[2] = type;
      data[3] = (byte)((PID & 0xFF00) >> 8);
      data[4] = (byte)(PID & 0x00FF);
      PID++;
      for (int i = 0; i<7;i++){
        data[i+5] = payload[i];
      }
    }
    ~Packet () {
    }
    byte send (void){
      if(millis() - time < data[2]) {
        if (millis()-time >= sent*5){
          data[11] = sent;
          Mirf.setTADDR((byte *)RFBASE);
          Mirf.send(data);
          sent++;
        }
        if(data[2] == 192) return 1;
        return 0;
      } else {
        return 1;
      }
    }
    
    int getPID() {
      return (int)((int)data[3]<< 8 + (int)data[4]);
    }
};
Packet *Packages[5];
byte busy=0;

void sendPackages(void) {
    if ((busy&1)) {
      if (Packages[0]->send()) {
        busy &= 0b11111110;
        delete Packages[0];
      }
    } else if ((busy&2)) {
      if (Packages[1]->send()) {
        busy &= 0b11111101;
        delete Packages[1];
      }
    } else if ((busy&4)) {
      if (Packages[2]->send()) {
        busy &= 0b11111011;
        delete Packages[2];
      }
    } else if ((busy&8)) {
      if (Packages[3]->send()) {
        busy &= 0b11110111;
        delete Packages[3];
      }
    } else if ((busy&16)) {
      if (Packages[4]->send()) {
        busy &= 0b11101111;
        delete Packages[4];
      }
    }
}
boolean newPacket (byte dest, byte type, byte *payload) {
  if (busy<31){
    if (!(busy&1)) {
      Packages[0] = new Packet (dest, type,payload);
      busy |= 1;
    } else if (!(busy&2)) {
      Packages[1] = new Packet (dest, type,payload);
      busy |= 2;
    } else if (!(busy&4)) {
      Packages[2] = new Packet (dest, type,payload);
      busy |= 4;
    } else if (!(busy&8)) {
      Packages[3] = new Packet (dest, type,payload);
      busy |= 8;
    } else if (!(busy&16)) {
      Packages[4] = new Packet (dest, type,payload);
      busy |= 16;
    }
    return true;
  } else return false;
}

void deletePID (int pid) {
    if ((busy&1)) {
      if (Packages[0]->getPID() == pid) {
        busy &= 0b11111110;
        delete Packages[0];
      }
    } else if ((busy&2)) {
      if (Packages[1]->getPID() == pid) {
        busy &= 0b11111101;
        delete Packages[1];
      }
    } else if ((busy&4)) {
      if (Packages[2]->getPID() == pid) {
        busy &= 0b11111011;
        delete Packages[2];
      }
    } else if ((busy&8)) {
      if (Packages[3]->getPID() == pid) {
        busy &= 0b11110111;
        delete Packages[3];
      }
    } else if ((busy&16)) {
      if (Packages[4]->getPID() == pid) {
        busy &= 0b11101111;
        delete Packages[4];
      }
    }
}
byte parseMsg() {
  byte data[12];
  Mirf.getData(data);
  /*
         Serial.print(data[1]);
        Serial.print("\t");
        Serial.print(data[3]);
        Serial.print("\t");
        Serial.print(data[4]);
        Serial.print("\t");
        Serial.println(data[11]);
        Serial.println("---");
        */
  if(data[0] == MYID) {
    switch(data[2]) {
      case 192: //ACK
        unsigned int pid;
        pid = ((unsigned int)data[5]<< 8 + (unsigned int)data[6]);
        deletePID(pid);
        break;
      default:
        return 0; //kenne Datentyp nicht
    }
  } else {
    return 0; //Nachricht nicht für mich
  }
}


void setup() {
  //Serial.begin(115200);
  //init NRF24
  Mirf.spi = &MirfHardwareSpi;
  Mirf.cePin = 9;
  Mirf.csnPin = 10;
  Mirf.init();
  Mirf.setRADDR((byte *)RFADDR);
  Mirf.payload = 12;
  Mirf.channel = RFCHANNEL;
  Mirf.config();
  
  //PID = readPID();
  
  newPacket((byte)0, (byte)193, Version);
  
  //SET(PORTD, 4);
  //pinMode(4, OUTPUT); //yellow LED
  SET(DDRD, 4);
  //pinMode(5, OUTPUT); //red LED
  SET(DDRD, 5);
  
  //pinMode(2, INPUT); 
  //pinMode(3, INPUT);
  //digitalWrite(2, HIGH); //Pullup
  //digitalWrite(3, HIGH); //Pullup
  
  
  //digitalWrite(4, HIGH);
  SET(PORTD, 4);
  //digitalWrite(5, HIGH);
  SET(PORTD, 5);
  delay(300);
  //digitalWrite(4, LOW);
  CLR(PORTD, 4);
  //digitalWrite(5, LOW);
  CLR(PORTD, 5);
  
  
  
  
}
long interval = 300;
int ledState = LOW;
long previousMillis = 0;
const int ledPin =  6;
const int rot =  5;
const int gruen =  3;

/*
void loop(){
  
  static unsigned long blinktime=0;
  if(Mirf.dataReady()){
    parseMsg();
  }
  sendPackages();
  while(Mirf.isSending());
  if(Mirf.dataReady()){
    parseMsg();
  }
  if (millis() - blinktime > 30) {
        blinktime = millis();
        newPacket((byte)0, (byte)193, Version);
  }
  delay(3);
  
  unsigned long currentMillis = millis();
 
  if(currentMillis - previousMillis > interval) {
    // save the last time you blinked the LED 
    previousMillis = currentMillis;   

    // if the LED is off turn it on and vice-versa:
    if (ledState == LOW)
      ledState = HIGH;
    else
      ledState = LOW;

    // set the LED with the ledState of the variable:
    digitalWrite(ledPin, ledState);
  }
  if(busy == 31) {
    digitalWrite(rot, HIGH);
  } else {
    digitalWrite(rot, LOW);
  }
}
*/
void loop(){
  static unsigned long blinktime=0, batterytime=0;
  unsigned long deltat = 0;
  switch (State) { //Statemachine
    case 0:
      //init
      newPacket((byte)0, (byte)193, Version); // Bei der Basisstation melden
      attachInterrupt(0, ISR_0, FALLING); // Interrupt für Infrarot aktivieren
      State = 5;
      //Serial.print("init\n");
      break;
    case 2: State=5;
      
    /*case 2:{
      static unsigned long inittime = 0;
      if( millis() - inittime > 150 )
      {
        byte payload[24] = {0};
        payload[0] = (byte)(((int)MYADDR & 0xFF00) >> 8 );
        payload[1] = (byte)(((int)MYADDR & 0x00FF));
        newPacket((byte)0, (byte)193, Version)
        inittime = millis();
        Serial.print("register\n");
      }
      break;
    }*/
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
      sync++;
        //Serial.print("IR detected\n");
      break;
    case 15:
      //waiting for US
      if (((PIND & 0x08)>>3)^1) {
        USDetectionTime = micros();
        State = 20;
      } else if(micros() - IRDetectionTime > 100000) { // Abbrechen falls nach 100ms kein US detektiert
        //Serial.print("US to late ");
        //byte tmp[4] = {0,0,0,0};
        //Result = 0;
        //#######################!!!######(BASEADDR, (byte)42, tmp);
        State = 5;
        //detachInterrupt(1);
      }
      break;
    case 20:
      //US detected
      deltat = USDetectionTime - IRDetectionTime;
      Result = deltat;
      byte tmp[7];
      tmp[0] = (byte)((deltat & 0xFF000000) >> 24);
      tmp[1] = (byte)((deltat & 0x00FF0000) >> 16);
      tmp[2] = (byte)((deltat & 0x0000FF00) >>  8);
      tmp[3] = (byte)((deltat & 0x000000FF));
      tmp[4] = sync;
      newPacket((byte)0, (byte)64, tmp);
      Blink = 2;
      State = 5;
        //Serial.print("US detected\n");
        //Serial.println(deltat);
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
  
  sendPackages();
  while(Mirf.isSending()) {};
  if(Mirf.dataReady()){
    parseMsg();
  }
}


