import math
import random
import os
import glob
import sys, traceback
import time
import threading 
import serial
import re

import TeamX



DEBUG = 1

def debug(*args):
    if DEBUG:
        print(*args)


#globale Variablen für Position, darauf könnt Ihr zugreifen (lesen); gesetzt werden sie über clib_multilat.
posx = 0.0
posy = 0.0
posz = 1000.0
#poslist[0][n]=x ; poslist[1][n]=y; poslist[2][n]=z;
poslist = [[posx,posy,posz]]
buf = []
zaehlerposlist = 1 #wg poslist = [[posx,posy,posz]]


# bitte kopieren mit dem Namen Team1, Team2 oder Team3
class Blowfish(TeamX.TeamX):
    """ Das ist Eure Funktionsklasse, hier kommt alles rein, was speziell Euer Team betrifft. In den Eventhandler-Funktionen bitte keine komplizierten Berechnungen durchführen, sondern nur flags setzen, da diese von einem anderen Thread berechnet werden müssten und diesen evtl. blockieren würden(=>GUI hängt, etc.). Die run-Funktion wird in Eurem Thread ausgeführt, da kommen die Berechnungen rein. Zugriff auf die gui oder arduino habt Ihr über self.main.gui bzw. self.main.arduino """
    def __init__(self, main):
        threading.Thread.__init__(self) 
        self.main = main
        debug("Team Blowfish")
        self.run_ = True
        self.start_ = 0
        self.kurswinkelflag = False
        self.zaehler = 0
        self.newposflag = False
        self.XBee = 0
        self.XBeeflag = False
        self.compareflag = False
        self.wp_next = 0
        self.XBee_init()
        self.alpha_soll = []
        self.alpha_ist = 0
        self.u = 1
        self.x = 0
        
    def run(self):
        #i=0
        while(self.run_):
            #i=i+1
            #debug("TeamX run:",i)
            self.loop()
    def loop(self):
        if (self.start_):
            #wegpunktnavigation etc.
            #self.main.arduino.send("TeamX fliegt!\n")
            #XBee starten jetzt in onStart()
            #if self.u:
                #self.config()
                #self.u = 0
            
            if self.newposflag:
                #print('Alpha_soll:{}'.format(len(self.alpha_soll)))
                #Noch nötig wenn Start nach Beginn der Simulation gedrückt wird
                if len(self.alpha_soll) == 0:
                    self.course_angle_reference()
                    pass
                #debug('Debug')    
                self.course_angle_pos()
                self.compare()
                self.newposflag = False

                pass
            #Nicht mehr ausgeführt jetzt durch onStart und onStop unterstützt
            if self.kurswinkelflag:
                print('Kurswinkel:')
                self.course_angle_reference()
                print('Ende')
                self.kurswinkelflag = False
                pass
                
        #Konfigurieren und starten des Zeppelins        
    def config(self):
        #Zeppelin konfigurieren nie "\n" vergessen!
        #SCHUB
        ####
        string = "bsc 25\n"
        self.XBee_send(string)
        self.XBee.flushOutput()
        time.sleep(0.1)
        
        #RESET BWI
        string = "bwi 0\n"
        self.XBee_send(string)
        #self.XBee.flushOutput()
        #time.sleep(0.1)
        
        #string = "bwde" watchdog
        # "bdrop" droppen
        # "bwdr" watchdog reset
         
        #Zeppelin starten 
        string = "ben\n"
        self.XBee_send(string)
        print("Zeppelin gestartet")
        #self.XBee.flushOutput()
        time.sleep(0.1)
        
        #string = "bdis\n"
        #self.XBee_send(string)
        #print("Zeppelin gestoppt")
                
    def onStart(self):
        #Start-Button wurde gedrückt
        print('START/RESET...', end = '\n\n')
        #global nicht gut
        # posx,posy,posz wird zu self.main.rawPos[0],self.main.rawPos[1],self.main.rawPos[2]
        global poslist 
        global zaehlerposlist
        self.main.positionslist = [[self.main.rawPos[0],self.main.rawPos[1],self.main.rawPos[2]]]
        self.main.gui.showPositionflag = True 
        #self.XBee_init()
        #poslist = [0.0,0.0,1000.0]
        zaehlerposlist = 1
        self.wp_next = 0
        if self.XBeeflag:
            self.config()
        self.start_ = 1
        pass
        
    def onStop(self):
        #Stop-Button wurde gedrückt
        print("\nSTOP\n")
        if self.XBeeflag:
            self.XBee.flushOutput()
            string = "bdis\n"
            self.XBee_send(string)
            print("Zeppelin gestoppt")
        self.main.gui.showPositionflag = False
        self.main.positionslist = [[self.main.rawPos[0],self.main.rawPos[1],self.main.rawPos[2]]]
        self.alpha_soll = []
        self.start_ = 0
        self.wp_next = 0
        # reset etc.
        pass
        
    def onNewPos(self):
        #TODO TODO TODO: in filterdPos die gefilterten Werte eintragen
        self.newposflag = True
        self.main.filterdPos[0] = self.main.rawPos[0]
        self.main.filterdPos[1] = self.main.rawPos[1]
        self.main.filterdPos[2] = self.main.rawPos[2]
        #debug(self.main.rawPos[0],self.main.rawPos[1],self.main.rawPos[2])
        pass
    def onButtonPressed(self, i):
        #welcher Button welche Nummer hat seht Ihr in der glade Datei oder im Eventhandler oder durch Testen
        #debug("Button ", i)
        pass
    def onWaypointUpdate(self):
        #wegpunkt wurde in der gui geändert
        pass
    def onObstacleUpdate(self):
        pass
        
    def setkurswinkelflag(self):
        self.kurswinkelflag = True
        print('Hallo')
  
    def median(self,alist):

        srtd = sorted(alist) # sortierte Kopie
        mid = math.ceil(len(alist)/2)   

        if len(alist) % 2 == 0:  
            return (srtd[mid-1] + srtd[mid]) / 2.0
        else:
            return srtd[mid]
        
    def course_angle_reference(self):
        x = list()
        y = list()
        #alpha_soll = list()
        n = 0
        if len(self.alpha_soll) == 0 or self.kurswinkelflag:
            self.alpha_soll = []
            self.kurswinkelflag = False
            print("\nWegpunkte:\n")
            for waypoint in self.main.waypointlist:
                x.append(waypoint[1])
                y.append(waypoint[2])
                print("x:",x[n])
                print("y:",y[n])
                n = n+1
            print("\nSollwinkel:")    
            for i in range(len(self.main.waypointlist)-1):
                
                self.alpha_soll.append(math.atan2(y[i+1]-y[i],x[i+1]-x[i]))
                #alpha.append(y[i]/math.sqrt(math.pow((x[i+1]-x[i]),2)+math.pow((y[i+1]-y[i]),2)))
                print("alpha_soll",len(self.alpha_soll),":",self.alpha_soll[i]*180.0/math.pi)
        return self.alpha_soll

   
    def course_angle_pos(self):
        #debug('course_angle_pos')
        
        #globale Istwegpktliste
        global poslist
        global zaehlerposlist
        #Filterbuffer
        global buf
        
        #bufgröße+ Ausreißer verwerfen!->Median, Poslistauswahl in Ringbereich
        b = 3
        
        #print('Multilatposition: x='+str(self.main.rawPos[0])+'y='+str(self.main.rawPos[1])+'z='+str(self.main.rawPos[2]))
        buf.append([self.main.rawPos[0],self.main.rawPos[1],self.main.rawPos[2]])
        
        if len(buf) == b :
            x,y,z = [],[],[]
            for i in range(len(buf)):
            
                 x.append(buf[i][0])
                 y.append(buf[i][1])
                 z.append(buf[i][2])
                 
            #Arithmetisches Mittel- weniger Sprünge bei schlechteren IPS-Werten     
            x = sum(x)/b
            y = sum(y)/b
            z = sum(z)/b
            
            #Median
            #x=self.median(x)
            #y=self.median(y)
            #z=self.median(z)
            
            print("Position: x = {}; y = {}; z = {}".format(x,y,z))
            print('Poslist:'+ str(poslist[-2:]))
            
            #Abstand_pos = math.sqrt(math.pow((poslist[zaehlerposlist-1][1]-poslist[zaehlerposlist-2][1]),2)+math.pow((poslist[zaehlerposlist-1][0]-poslist[zaehlerposlist-2][0]),2))
            
            poslist.append([x,y,z])
            print('Poslist:'+ str(poslist[-2:]))
            #TODO posliste wird sehr groß in kurzer Zeit ->evtl. Werte verringern
            #print(poslist)
            
            #buffer reset
            buf = []
            
            zaehlerposlist += 1
        
        #Winkel an der aktuellen Position + AbstandWP+ AbstandWP_alt+ self.wp_next bestimmen 	
        if (zaehlerposlist >= 2 and len(buf) == 0):
            
            debug('Zaehler:'+str(zaehlerposlist))
            
            #Abstandsberechnung der letzten beiden Positionswerte
            Abstand_pos = math.sqrt(math.pow((poslist[zaehlerposlist-1][1]-poslist[zaehlerposlist-2][1]),2)+math.pow((poslist[zaehlerposlist-1][0]-poslist[zaehlerposlist-2][0]),2))
            print("Abstand geflogen:{}".format(Abstand_pos))
            
            #Falls neue Position nicht im Ringbereich Positionswert verwerfen
            ####
            if Abstand_pos < 240 or Abstand_pos > 1400.0:# !!!optimieren!!!
                del poslist[-1]
                zaehlerposlist -= 1
                self.compareflag = False
            else:
                #Sobald neuer Posititonswert emittelt wurde prüfe Winkel
                #self.compareflag = True
                self.alpha_ist = math.atan2((poslist[zaehlerposlist-1][1]-poslist[zaehlerposlist-2][1]),(poslist[zaehlerposlist-1][0]-poslist[zaehlerposlist-2][0]))
                         
            AbstandWP = math.sqrt(math.pow(self.main.waypointlist[self.wp_next][1]-poslist[zaehlerposlist-1][0],2)+math.pow(self.main.waypointlist[self.wp_next][2]-poslist[zaehlerposlist-1][1],2))
            if self.wp_next >= 1:
                AbstandWP_alt = math.sqrt(math.pow(self.main.waypointlist[self.wp_next-1][1]-poslist[zaehlerposlist-1][0],2)+math.pow(self.main.waypointlist[self.wp_next-1][2]-poslist[zaehlerposlist-1][1],2))
                # Wenn die Hälfte des Weges zurückgelegt wurde Schub zu 0
                print('AbstandWP_alt:{}'.format(AbstandWP_alt))
                
                if AbstandWP < AbstandWP_alt and self.x:
                    string = "bsc 0\n"
                    self.x = 0
                    self.XBee_send(string)

            print('AbstandWP:{}'.format(AbstandWP))
            print('Wegpunkt:{}'.format(self.wp_next))
            
            # Prüft ob der Wegpunkt erreicht wurde, wenn ja dann soll der Abstand zum Nächsten wp berechnet werden.
            ####
            if (AbstandWP < 600):
                self.wp_next = self.wp_next+1
                ####hier neuer Winkel
                self.alpha_soll[self.wp_next] = math.atan2((self.main.waypointlist[self.wp_next+1][2]-poslist[zaehlerposlist-1][1]),(self.main.waypointlist[self.wp_next+1][1]-poslist[zaehlerposlist-1][0]))
                
                Offset = 10.0
                #Neuer Soll mit Offset gesendet wegen Drift
                dat = ''.join(['bwi ',str(round((self.alpha_soll[self.wp_next-1]* 180.0/math.pi),1)+Offset)])
                dat = ''.join([dat,'\n'])
                #print('BWI '+ str(round((self.alpha_soll[self.wp_next-1]* 180.0/math.pi),1)))
                self.XBee_send(dat)
                dat = ''
                #wieder Schub geben sobald neuer Winkel gedreht wird
                string = "bsc 30\n"
                #self.XBee_send(string)
                
                #if self.wp_next == 2.0:
                #  string = "bdrop\n"
                #  self.XBee_send(string)
                #  self.XBee.flushOutput()
                #Achtung wegen compareflag evtl. zu oft mit altem Winkel geregelt!!!!  
            
		    #Abweichung vom Sollwinkel
            #alpha_diff = alpha_ist - alpha_soll
            #if alpha_diff >10 #10Grad erlaubte Maximalabweichung
		        #Neue alpha_soll Berechnung(mit Philipps Funktion
        pass
	
	#Vergleich Soll-und Istwinkel
    def compare(self):
        #self.compareflag = False
        global poslist
        global zaehlerposlist
        if(len(poslist) >= 2 and self.compareflag and len(self.main.waypointlist) >= self.wp_next):
            if len(self.main.waypointlist) == self.wp_next:
                print("Ziel erreicht! =)")
                #TODO Zeppelin Landesequenz initiieren!
                
            self.compareflag = False
            schrittweite_rad = 20.0 * math.pi/180.0
            schrittweite_grad = 5.0
            diff = self.alpha_ist-self.alpha_soll[self.wp_next]
            
            #self.compareflag = False
            if abs(diff) > (40.0 * math.pi/180.0):  #10Grad maximale Abweichung
                
                #print(poslist[zaehlerposlist-1][1])
                ###hier in rad
                self.alpha_soll[self.wp_next] = math.atan2((self.main.waypointlist[self.wp_next+1][2]-poslist[zaehlerposlist-1][1]),(self.main.waypointlist[self.wp_next+1][1]-poslist[zaehlerposlist-1][0]))
                
                #Reihenfolge der Rechnung so dass positives diff links fliegen bedeutet!        
                diff = self.alpha_ist-self.alpha_soll[self.wp_next]
                
                #Aufteilung in Winkelschritte
                #print('Alpha_ist:{}'.format(self.alpha_ist* 180.0/math.pi))
                #print('Alpha_soll:n {}'.format(self.alpha_soll[self.wp_next]* 180.0/math.pi))
                print('Diff:{}'.format(diff* 180.0/math.pi))
                
                if abs(diff) > (schrittweite_rad):
                    
                    data = str(schrittweite_grad)
                    if diff < 0:
                        #Winkel inkrementieren nach rechts
                        data = ''.join(['bwii ',data])
                        data = ''.join([data,'\n'])
                    else:
                        #Winkel inkrementieren nach links
                        schrittweite_grad = 5.0
                        data = str(schrittweite_grad)
                        data = ''.join(['bwii -',data])
                        data = ''.join([data,'\n'])
                    #self.XBee.flushOutput()
                    time.sleep(0.2)
                        
                ################ schrittwinkel in listenform
                    #zehner = abs(math.floor(diff/schrittweite))
                    #Rest = diff%schrittweite
                    #data = str()
                    #for i in range(zehner):
                    #    data = ' '.join([data,str(schrittweite)])
                    #
                    #data = ' '.join([data,str(Rest)])
                    #Negativer Winkel("b0") oder positiver Winkel("b1")
                    #if diff > 0:
                    #    data = ''.join(['b0 {}:'.format(zehner+1),data])
                    #else:
                    #    data = ''.join(['b1{}:'.format(zehner+1),data])
                ##################    
                    
                    self.XBee_send(data)
                    
    def XBee_init(self):
        tty = glob.glob('/dev/ttyUSB*')
        #debug(tty)
        #print(tty)
        
        if(len(tty)<2):
            print("", end = '\n\n')
            print("No XBee connected!!!!!!!!!", end = '\n\n')
            ###sys.exit()
            #self.main.gui.onExit()
        else:
            for i in tty:
                if i != self.main.ttyport:
                    XBeeport = i
                    self.XBee = serial.Serial(XBeeport,19200)
                    self.XBeeflag = True
                    
                    debug("XBee initiiert")		
                    pass
    
    def XBee_send(self,d):
      if self.XBeeflag:
        print('Send: {}'.format(d))
        self.XBee.write(bytes(d,'UTF-8'))
        d =''
        self.XBee.flushOutput()
        time.sleep(0.3)
      else:
        print('\n\"{}\""+"konnte nicht gesendet werden! Bitte XBee anschliessen und Start drücken.'.format(data)) 
        self.start_ = False     
        ###sys.exit()
        
    def onExit(self):
        # Programm beenden
        self.run_=False
        self.start_ = False
        pass



