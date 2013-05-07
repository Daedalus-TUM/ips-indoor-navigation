//base station v0.5
#define VERSION "v0.5"

long deltat;
byte from;
void setup(){

  Serial.begin(115200);
  Serial.print("IPS ");
  Serial.println(VERSION);
  randomSeed(analogRead(0));
}


void loop(){
  deltat = random(3000,20000);
  from = random(1,7);
  Serial.print("deltat from ");
  Serial.print(from);
  Serial.print(" - ");
  Serial.print(deltat);
  Serial.print(" - ");
  float distance;
  distance = deltat * 0.34;
  Serial.print(distance);
  Serial.print("\n");
  delay(10);
}


