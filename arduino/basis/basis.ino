//base station v0.5
#define VERSION "v0.5"


#include <SPI.h>
#include <Mirf.h>
#include <nRF24L01.h>
#include <MirfHardwareSpiDriver.h>

#define RFADDR "alex0"
#define RFBASE "alex1"
#define RFCHANNEL 42

const int MYADDR = 1;
const int BASEADDR = 1;


// Global Variables
byte State=0;
unsigned long PID=0;
byte Blink = 10;
byte station[10] = {0};
unsigned long station_last[10] = {0};
unsigned long station_last_req[10] = {0};

unsigned long readPID() {
  return long(0);
  /*
    return ( (EEPROM.read(0) << 24) 
                   + (EEPROM.read(1) << 16) 
                   + (EEPROM.read(2) << 8) 
                   + (EEPROM.read(3) ) );
  */
}


void blink () {
  digitalWrite(4, Blink%2);
}

byte parseMsg() {
  byte data[32];
  byte payload[24] = {0};
  Mirf.getData(data);
  if(data[0] == (byte)((MYADDR & 0xFF00) >> 8) && data[1] == (byte)(MYADDR & 0x00FF)) {
    int from;
    from = (int)data[2]<<8;
    from += (int)data[3];
    switch(data[7]) {
      case 1:
        byte id;
        id = data[8];
        if (from == id && id < 10) station[id] = 1;
        sendMsg(from, (byte) 2, payload);
        break;
      case 4:
        
        break;
      case 6:
        unsigned long deltat;
        deltat = (unsigned long)data[8];
        deltat += (unsigned long)data[9]<<8;
        deltat += (unsigned long)data[10]<<16;
        deltat += (unsigned long)data[11]<<24;
        float distance;
        distance = deltat * 0.34;
        
        Serial.print("deltat from ");
        Serial.print(from);
        Serial.print(" - ");
        Serial.print(deltat);
        Serial.print(" - ");
        Serial.print(distance);
        Serial.print("\n");
        station_last[from] = millis();
        break;
      
      
      case 99:
        Blink = data[8];
        break;
      case 42:{
        Serial.print("deltat from ");
        Serial.print(from);
        Serial.print(" - ");
        unsigned long deltat;
        deltat = (unsigned long)data[8];
        deltat += (unsigned long)data[9]<<8;
        deltat += (unsigned long)data[10]<<16;
        deltat += (unsigned long)data[11]<<24;
        Serial.print(deltat);
        Serial.print(" - ");
        float distance;
        distance = deltat * 0.34;
        Serial.print(distance);
        Serial.print("\n");
        break;}
      default:
        return 0; //kenne Datentyp nicht
    }
  } else {
    return 0; //Nachricht nicht für mich
  }
}

void sendMsg(int receiver, byte type, byte * payload) {
  byte data[32];
  Mirf.setTADDR((byte *)RFBASE);
  data[0] = (byte)((receiver & 0xFF00) >> 8 );
  data[1] = (byte)((receiver & 0x00FF));
  data[2] = (byte)((MYADDR & 0xFF00) >> 8 );
  data[3] = (byte)((MYADDR & 0x00FF));
  data[4] = (byte)((PID & 0xFF0000) >> 16 );
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
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);
  pinMode(2, INPUT); 
  pinMode(3, INPUT);
  digitalWrite(2, HIGH);
  digitalWrite(3, HIGH);
  
  digitalWrite(4, HIGH);
  digitalWrite(5, HIGH);
  delay(300);
  digitalWrite(4, LOW);
  digitalWrite(5, LOW);

  Serial.begin(115200);
  Serial.print("IPS ");
  Serial.println(VERSION);


  Mirf.spi = &MirfHardwareSpi;
  Mirf.cePin = 9;
  Mirf.csnPin = 10;
  Mirf.init();
  Mirf.setRADDR((byte *)RFADDR);
  Mirf.payload = 32;
  Mirf.channel = RFCHANNEL;
  Mirf.config();
  
  PID = readPID();
  
}

void request_data(int i) {
  byte payload[24];
  sendMsg(i, (byte) 5, payload);
}

void loop(){
  static unsigned long last_request = 0;
  if(!Mirf.isSending() && Mirf.dataReady()){
    parseMsg();
  }
  int i=0;
  for (i=0;i<10;i++) {
    if(station[i]==1 && station_last[i] < millis() + 180 && last_request < millis() + 4 && station_last_req[i] < millis() + 30){
      last_request = millis();
      station_last_req[i] = millis();
      request_data(i);
    }
  }
}


