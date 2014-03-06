import math
import random
import os
import glob
import sys, traceback
import time
import threading 
import serial
import re

DEBUG = 1

def debug(*args):
    if DEBUG:
        print(*args)

"""
Diese Klasse kümmert sich um die Kommunikation mit dem Arduino (Basis-Bodenstation)
Wichtig für Euch ist die Methode send(self, txt)
zu Thread allgemein siehe threading-doku
"""
class Arduino(threading.Thread):
  #self.main.stations
  #initialisierung, wird genau einmal ausgeführt
  def __init__(self,main):
    debug("Arduino init")
    threading.Thread.__init__(self) #p-initialisierung der vererbten Fähigkeit threading der Klasse Thread.
    self.ttylock = threading.Lock()
    self.main = main
    self.s = serial.Serial(self.main.ttyport, 115200, 8, 'N', 1, 0.0001)#0.005
    self.s.flush()
    #self.pattern = re.compile(b"deltat from (\d+) - (\d+) - (\d+\.\d+)") seit Version 0.7 veraltet
    # RegEx für Laufzeitmessungsdaten TODO: allgemeiner formulieren und speziellere Auswertung in recv_packet
    self.pattern = re.compile(b"t([0-9]{2})([0-9]{10})")
    self.run_ = True
    self.strbuffer = b''
  #Dauerschleife, Beendet falls self.run_ == False; siehe threading-doku
  def run(self):
    #i = 0  
    #debug ("Arduino start running")
    while(self.run_):
      #i=i+1
      #debug("Arduino run:",i)
      #debug (self.s.inWaiting())
      while (self.s.inWaiting() > 0):#if beim Alex
        self.recv_packet()
      time.sleep(0.00005) # vorher 0.0005 je nach dem wie viele Pakete verschickt werden
  #deprecated, dient(e) zu Testzwecken
  def setled(self, led, state):
    self.ttylock.acquire()
    self.s.write("\x02" + led + chr(state) + "\x03")
    self.s.flush()
    self.recv_packet()
    self.ttylock.release()
  #verschickt txt ans Arduino
  def send(self, txt):
    self.ttylock.acquire()
    self.s.write(bytes(txt, 'UTF-8'))
    self.s.flush()
    self.ttylock.release()
  #empfängt und verarbeitet Daten vom Arduino, löst eventhandler.onNewPos aus
  def recv_packet(self):
    while (self.s.inWaiting() > 0):
      #res = self.s.readline(14)
      #res = self.s.read(self.s.inWaiting())
      self.strbuffer = self.strbuffer + self.s.read(self.s.inWaiting())
      if b'sync' in self.strbuffer:
        #debug('Buffer: '+str(self.strbuffer))
        blocks = self.strbuffer.split(b'sync')
        #debug('Bloecke: '+ str(blocks))
        self.strbuffer = blocks[-1]
        lines = blocks[-2].split(b'\n')#blocks.split(b'\n')
        ##
        newdeltat = False
        ##
        for line in lines:
          tmp = self.pattern.search(line)
          #debug('Line: '+ str(line))
          if tmp is not None:
            deltat = float(tmp.group(2))
            distance = deltat * 0.345 #TODO: Temperaturanpassung, aktuell: 22°C
            if distance > 1:
                stationnr = int(tmp.group(1))
                millis = int(round(time.time() * 1000))
                #debug(distance)
                #debug('Stationnr'+str(self.main.stations[stationnr][3]))
                #Abfrage filtert Fehler durch Reflektionen; muss umso größer sein umso schneller der Zeppelin fliegt!!
                if ((abs(distance - self.main.stations[stationnr][3]) < 800) or  (self.main.stations[stationnr][3] == 0)):
                  self.main.stations[stationnr][3] = distance
                  self.main.stations[stationnr][4] = millis
                  ##
                  newdeltat = True
                  #self.main.clib_multilat()
                  #pylib_multilat(self.main)
                  #self.main.eventhandler.onNewPos()
                  #debug("NewPos")
                  ##
          else:
            #debug (res)
            pass
        ##    
        if newdeltat:
          self.main.clib_multilat()
          self.main.eventhandler.onNewPos()
          #debug("NewPos")
        ##
        
  def recv_packet_alt(self):
    #self.ttylock.acquire() #vor jedem Zugriff aus die serialle Verbindung lock setzen
    while (self.s.inWaiting() > 0):
      res = self.s.readline()
      debug (res)
      """#TODO: andere2013/07/04  0.7.12.0    Geschwindigkeitsproblem gelöst - Alexander Pattern, falls noch andere Daten vom Arduino (nrf24) kommen
      tmp = self.pattern.search(res)
      if tmp is not None:
        deltat = float(tmp.group(2))
        distance = deltat * 0.345 #TODO: Temperaturanpassung, aktuell: 22°C
        if distance > 1:
            stationnr = int(tmp.group(1))
            millis = int(round(time.time() * 1000))
            self.main.stations[stationnr][3] = distance
            self.main.stations[stationnr][4] = millis
            #self.main.clib_multilat()
            #self.main.pylib_multilat(self.main)
            self.main.eventhandler.onNewPos()
            #debug("NewPos")
      else:
        #debug (res)
        pass"""            
    #self.ttylock.release() # lock lösen
  #den Arduino neustarten
  def reset(self):
    self.s.setDTR(False)
    time.sleep(0.00001)
    self.s.setDTR(True)
  #terminiert den Thread
  def onExit(self):
    self.run_=0

