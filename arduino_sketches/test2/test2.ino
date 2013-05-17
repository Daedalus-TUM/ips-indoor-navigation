//base station v0.7 2013 05 14
//test dummy data
//Achtung, das ist ein Simulationsprogramm und hat mit echten Werten nichts zu tun!
#define VERSION "v0.7"

long deltat;
byte from;
unsigned long time = 0;
void setup(){

  Serial.begin(115200);
  Serial.print("V");
  Serial.print(" IPS ");
  Serial.println(VERSION);
  randomSeed(analogRead(0));
  Serial.println("Achtung, das ist ein Simulationsprogramm und hat mit echten Werten nichts zu tun!");
  time = millis() - 200;
}

float posx=0,posy=0,posz=500;
float vx=0,vy=0,vz=0;
long randi=0;
int k=0;
// Position der Bodenstationen
int pos[9][3] = { {0,0,0},
                   {1000,0,0},
                   {1000,1000,1000},
                   {0,1000,0},
                   {-1000,1000,1000},
                   {-1000,0,0},
                   {-1000,-1000,1000},
                   {0,-1000,0},
                   {1000,-1000,1000} };


void loop(){
  time += 200;
  k++;
  int i=0;
  for (i=0;i<9;i++){ // für jede Station die Entfernung berechnen + Rauschen
    float distance;
    byte from;
    from = i+1;
    unsigned long deltat;
    distance = sqrt((pos[i][0]-posx)*(pos[i][0]-posx)+(pos[i][1]-posy)*(pos[i][1]-posy)+(pos[i][2]-posz)*(pos[i][2]-posz));
    randi = random(-100,500);
    deltat = long(distance * 2.94);
    deltat = deltat + long(float(deltat) * float(randi) / 10000.0);
    if (randi > 460) deltat = deltat + 2000;
    if (randi > 490) deltat = deltat + 2000;
    if (randi < -50) deltat = 0;
    distance = deltat * 0.34;
    //Serial.print("deltat from ");
    //Serial.print(from);
    //Serial.print(" - ");
    //Serial.print(deltat);
    //Serial.print(" - ");
    //Serial.print(distance);
    Serial.print("t");
    if(from<10) Serial.print('0');
    Serial.print(from);
    if(deltat<10) Serial.print('0');
    if(deltat<100) Serial.print('0');
    if(deltat<1000) Serial.print('0');
    if(deltat<10000) Serial.print('0');
    if(deltat<100000) Serial.print('0');
    if(deltat<1000000) Serial.print('0');
    if(deltat<10000000) Serial.print('0');
    if(deltat<100000000) Serial.print('0');
    if(deltat<1000000000) Serial.print('0');
    Serial.print(deltat);
    Serial.print("\n");
  }
  Serial.print("sync ");
  Serial.println(k);
  Serial.print("pos: ");
  Serial.print(posx);
  Serial.print(" - ");
  Serial.print(posy);
  Serial.print(" - ");
  Serial.println(posz);
   
  randi = random(-1000,1000);
  vx = vx + randi/100.0; 
  if(abs(posx) > 2000) vx = vx - 10.0*posx/abs(posx);
  if(abs(vx) > 200) vx = 170 * vx/abs(vx);
  randi = random(-1000,1000);
  vy = vy + randi/100.0; 
  if(abs(posy) > 2000) vy = vy - 10.0*posy/abs(posy);
  if(abs(vy) > 200) vy = 170 * vy/abs(vy);
  randi = random(-1000,1000);
  vz = vz + randi/300.0; 
  if(posz > 2000) vz = vz - 4.0;
  if(posz < 500) vz = vz + 4.0;
  //if(posz < 20) posz = 20;
  if(abs(vz) > 80) vz = 80 * vz/abs(vz);
  
  posx = posx + vx;
  posy = posy + vy;
  posz = posz + vz;
  
  
  if(k%53 == 0) Serial.println("Bodenstation 4 meldet schwachen Akku!");
  
  //delay(200);
  while(millis() - time < 200) __asm__("nop\n\t");
}


