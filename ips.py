#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-
# 21.05.2013

VERSION = (0,7,14,0)

# Änderungen bitte im CHANGELOG unten vermerken und Versionsnummer anpassen
#
#p- diese Kommentaren sind von Philipp
#
# Standardeinrückung: 4 Leerzeichen
#
# Zu den Kommentaren:
#   * "TODO" meist steht dabei, was zu tun ist, kein Anspruch auf Vollständigkeit
#   * "???" bedeutet: Besprecht das mit den anderen Teams und mir (Schnittstelle definieren) oder macht einen Vorschlag 
#   * "bitteerklären" könnt Ihr dazuschreiben, dann erkläre ich das etwas genauer.
#   * falls Ihr größere Änderungen im Hauptprogramm macht, schreibt Euren Namen dauzu, falls es Fragen gibt
#
# Zur Versionierung:
#   * Die Versionsnummer ist getrennt in major.minor.micro.revision
#   * major ist erstmal 0 bis der volle Funktionsumfang erreicht ist
#   * minor erhöht sich mit jeder Schnittstellenänderung in der angeschlosssenen Hardware
#   * micro wird bei neuen Funktionen erhöht
#   * revision bei jeder Änderung erhöhen
#   * CHANGELOG unten anfügen
#
# TODO: allgemein
#   * Windowskompatibilität (falls gewünscht)
#       - Problem: Python3 und GTK+3 haben in dieser Verbindung keine direkte Windowsunterstützung, Python2 ist besser
#       - statt multilat.so multilat.dll
#       - statt ttyUSB* COM*
#   * GUI erweitern:
#       - Menü: Speichern, Laden ...
#       - Wegpunktliste in externem Dialog bearbeiten
#       - Init-Fenster: und los soll das Fenster schließen, aktuell besser das init-Fenster schließen statt den Button zu drücken
#   * Globale Variablen durch was sinnvolleres erstzen
#
# Abhängigkeiten:
#   python3-gi python3-gi-cairo python3-all python3-regex python3-serial python3-gobject
#
# Bei Fragen erreicht Ihr mich unter daedalus[at]abak19.de

from gi.repository import Gtk,Gdk, GLib, GObject
import math
import random
import os
import glob
import sys, traceback
import time
from ctypes import * # Nicht schön
import threading 
import serial
import re
##
import cairo
##
import TeamX
import gui
import arduino
import eventhandler
import blowfish
#import drawing

print("DAEDALUS-IPS [Alexander Blum -- Markus Hefele -- Team Blowfish]")

DEBUG = 1

def debug(*args):
    if DEBUG:
        print(*args)

# Einbinden der Dynamik Link Library multilat.so
dir = os.path.dirname(__file__)
multilat=CDLL(os.path.join(dir, 'multilat.so')) #ctypes-doku




#TODO: Team-Klassen in eigene Dateien auslagern, um den Code besser zu trennen
#TODO: Da kommt Euer Programm rein
class Team1(TeamX.TeamX):
    def loop(self):
        #wird immer wieder aufgerufen, äquivalent zur Arduino-loop
        if (self.start_):
            #wegpunktnavigation etc.
            #self.main.arduino.send("TeamX fliegt!\n")
            pass
        time.sleep(0.1) #schlafen ist gut, um die CPU nicht voll auszulasten

class Team2(TeamX.TeamX):
    def loop(self):
        time.sleep(0.1)

class Team3(TeamX.TeamX):
    def loop(self):
        time.sleep(0.1)



# Startfenster zur Auswahl des seriellen Ports und des Teams
# TODO: "und los" Button soll das Fenster zerstören
class Init():
    def __init__(self, main):
        self.main = main
        #debug(self.main.ttyport,self.main.team)
        builder = Gtk.Builder()
        #builder.add_from_file("/home/alex/ips/glade_gui/daedalus.glade")
        builder.add_from_file(os.path.join(dir, 'daedalus.glade'))
        builder.connect_signals(eventhandler.EventHandler(self.main))
        window = builder.get_object("window2")
        self.ttybox = builder.get_object("buttonbox4")
        self.teambox = builder.get_object("buttonbox5")
        reloadbtn = builder.get_object("button12")
        reloadbtn.connect("pressed", self.reloadtty)
        self.reloadtty("")
        #add your team here DONE
        button1 = Gtk.RadioButton(group=None, label="Team Blowfish")
        button1.connect("toggled", self.setteam, "TeamBlowfish")
        self.teambox.pack_start(button1, True, True, 0)
        self.main.team = "TeamBlowfish"
        button = Gtk.RadioButton(group=button1, label="Alex")
        button.connect("toggled", self.setteam, "TeamX")
        self.teambox.pack_start(button, True, True, 0)
        #button = Gtk.RadioButton(group=button1, label="Team1")
        #button.connect("toggled", self.setteam, "Team1")
        #self.teambox.pack_start(button, True, True, 0)
        button = Gtk.RadioButton(group=button1, label="Team2")
        button.connect("toggled", self.setteam, "Team2")
        self.teambox.pack_start(button, True, True, 0)
        button = Gtk.RadioButton(group=button1, label="Team3")
        button.connect("toggled", self.setteam, "Team3")
        self.teambox.pack_start(button, True, True, 0)
        
        # end: add team
        window.show_all()
        #startet das init-Fenster
        Gtk.main()
    def setttydev(self, button, dev):
        if button.get_active():
            self.main.ttyport = dev
            debug("tty=",self.main.ttyport)
    def setteam(self, button, team_):
        if button.get_active():
            self.main.team = team_
            debug("team=",self.main.team)
    def reloadtty(self, button):
        #ladde tty ports
        ttydevs = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')# + glob.glob('/dev/ttyS*')
        for i in self.ttybox.get_children():
            self.ttybox.remove(i)
        if len(ttydevs) == 0:
          debug ("error: no tty Port")
        else:
          button = None
          for item in ttydevs:
            if button == None:
                self.main.ttyport = item
            button = Gtk.RadioButton(group=button, label=item)
            button.connect("toggled", self.setttydev, item)
            self.ttybox.pack_start(button, True, True, 0)
            self.ttybox.show_all()



"""
Hauptprogramm
"""
class Main():
    def __init__(self):
        #Gdk.threads_init()
        self.rawPos = [0,0,0]
        self.filterdPos = [0,0,0]
        self.heading = 0.0
        
        # stations[#stationsnummer]: [0-2] = x,y,z; [3] = radius in mm; [4] = letzte Aktivität
        self.stations = [[0 for col in range(5)] for row in range(11)]
        self.waypoints = [[0 for col in range(5)] for row in range(5)]
        
        #Angabe der Wegpunkte kann über Gui bearbeitet werden
        
        self.waypoints[0][0] = 0
        self.waypoints[0][1] = 0
        self.waypoints[0][2] = 1500
        self.waypoints[0][3] = 0  #Nummer des Wegpunktes
        self.waypoints[1][0] = 620
        self.waypoints[1][1] = 500
        self.waypoints[1][2] = 1500
        self.waypoints[1][3] = 1
        self.waypoints[2][0] = 1500
        self.waypoints[2][1] = 1700
        self.waypoints[2][2] = 1500
        self.waypoints[2][3] = 2
        self.waypoints[3][0] = 2000
        self.waypoints[3][1] = 2700
        self.waypoints[3][2] = 1500
        self.waypoints[3][3] = 3
        self.waypoints[4][0] = 2000
        self.waypoints[4][1] = 3500
        self.waypoints[4][2] = 1500
        self.waypoints[4][3] = 4
        #self.waypoints[5][0] = 1700
        #self.waypoints[5][1] = 4500
        #self.waypoints[5][2] = 1500
        
        
        #Angabe der Positionen der Stationen; TODO: soll in finaler Version wegfallen, da über GUI eingestellt
       
        self.stations[0][0] = 0
        self.stations[0][1] = 0
        self.stations[0][2] = 500
        self.stations[1][0] = 0#1500#0
        self.stations[1][1] = 3000#3000#0
        self.stations[1][2] = 0#0#500#
        self.stations[2][0] = 1000
        self.stations[2][1] = 0
        self.stations[2][2] = 0
        self.stations[3][0] = 2000#1000
        self.stations[3][1] = 6000#3000#1000
        self.stations[3][2] = 0#0#1000
        self.stations[4][0] = 3000#6000#0#0
        self.stations[4][1] = 3000#3000#1000
        self.stations[4][2] = 1000#500#0
        self.stations[5][0] = 0#450#0#-1000
        self.stations[5][1] = 0#2000#1000
        self.stations[5][2] = 0#0#500#1000
        self.stations[6][0] = 1500#2000 #-1000
        self.stations[6][1] = 0#2000#0
        self.stations[6][2] = 0#0
        self.stations[7][0] = 1000#-1000
        self.stations[7][1] = 3000#-1000
        self.stations[7][2] = 0#1000
        self.stations[8][0] = 3000#2000#1000#0
        self.stations[8][1] = 0#6000#0#1000#-1000
        self.stations[8][2] = 0#0
        self.stations[9][0] = 1500#3000#1000#1000
        self.stations[9][1] = 1500#3000#1000#-1000
        self.stations[9][2] = 0#450#1000
        self.stations[10][0] = 0
        self.stations[10][1] = 0
        self.stations[10][2] = 0
        '''
        #Simulationspositionen:
        self.stations[0][0] = 0
        self.stations[0][1] = 0
        self.stations[0][2] = 0
        self.stations[1][0] = 0
        self.stations[1][1] = 0
        self.stations[1][2] = 0
        self.stations[2][0] = 1000
        self.stations[2][1] = 0
        self.stations[2][2] = 0
        self.stations[3][0] = 1000
        self.stations[3][1] = 1000
        self.stations[3][2] = 1000
        self.stations[4][0] = 0
        self.stations[4][1] = 1000
        self.stations[4][2] = 0
        self.stations[5][0] = -1000
        self.stations[5][1] = 1000
        self.stations[5][2] = 1000
        self.stations[6][0] = -1000
        self.stations[6][1] = 0
        self.stations[6][2] = 0
        self.stations[7][0] = -1000
        self.stations[7][1] = -1000
        self.stations[7][2] = 1000
        self.stations[8][0] = 0
        self.stations[8][1] = -1000
        self.stations[8][2] = 0
        self.stations[9][0] = 1000
        self.stations[9][1] = -1000
        self.stations[9][2] = 1000
        self.stations[10][0] = 0
        self.stations[10][1] = 0
        self.stations[10][2] = 0
        '''
        # initialisiere Variablen, werden von initfenster beschrieben
        self.team = 0
        self.ttyport = 0
        # Variablen für GUI und alles andere
        self.waypointlist = 0
        self.obstaclelist = 0
        self.stationlist = 0
        ##
        self.positionslist = [[self.rawPos[0],self.rawPos[1],self.rawPos[2]]]
        ##
        self.builder = Gtk.Builder() #Lade GUI aus glade Datei
        self.builder.add_from_file(os.path.join(dir, 'daedalus.glade'))
        # Initfenster
        Init(self)
        
        if self.team and self.ttyport:
          if self.team == "TeamX":
            self.team = TeamX.TeamX(self)
          if self.team == "TeamBlowfish":
            self.team = blowfish.Blowfish(self)
          if self.team == "Team2":
            self.team = Team2(self)
          if self.team == "Team3":
            self.team = Team3(self)
        else:
            debug("init failed, please specify a tty port and a team")
            debug(self.ttyport,self.team)
            sys.exit() #TODO: dem Benutzer das in der GUI beibringen, anstatt einfach das Programm zu benden
 #TODO: Macht manchmal Probleme
        self.eventhandler = eventhandler.EventHandler(self)
        self.builder.connect_signals(self.eventhandler)

        #TODO: ??? in welcher Form sollen WP etc gespeichert werden?
        self.waypointlist = self.builder.get_object("liststore1")
        #self.waypointlist= [[1, 100, 199, 100,'neu']]
        self.obstaclelist = self.builder.get_object("liststore2")
        self.stationlist = self.builder.get_object("liststore3")
        
        # Stationen syncronisieren mit GUI
        for i in range(len(self.stations)):
            tmp = [i,self.stations[i][0],self.stations[i][1],self.stations[i][2],self.stations[i][3],3.8,1]
            self.stationlist.append(tmp)
        # Wegpunkte synchronisieren mit GUI
        for i in range(len(self.waypoints)):
            tmp = [i,self.waypoints[i][0],self.waypoints[i][1],self.waypoints[i][2],'WP']
            self.waypointlist.append(tmp)
            
        self.arduino = arduino.Arduino(self)
        self.gui = gui.GraphicalUserInterface(self)
        #self.map = drawing.Drawing(self)
        Gdk.threads_init()
        #starte Thread
        self.arduino.start()
        self.team.start()
        self.gui.start()
        #self.map.start()
        #join wartet bis Thread terminiert
        self.arduino.join()
        self.gui.join()
        #self.map.join()
        self.team.join()
    """
    ruft die c-lib zur Mutilateration auf, speichert die werte in posx,posy,posz
    Nimmt die Daten aus dem globalen Array stations
    """
    def clib_multilat(self):
        numstations = 0
        millis = int(round(time.time() * 1000))
        #zählt die aktuell aktiven Stationen in und speichert in numstations
        for station in self.stations:
            if (millis - station[4]) < 1500:
                numstations += 1
        if (numstations > 2):
            i = -1
            #Datentypen setzen, siehe ctypes doku
            #cstationtype = c_double * 3 * numstations
            #cradiustype = c_double * numstations
            cstationtype = c_double * 3 * 10
            cradiustype = c_double * 10
            cstarttype = c_double * 3
            cstations = cstationtype((0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0), (0,0,0))
            cradii = cradiustype(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            cstartpos = cstarttype(self.rawPos[0], self.rawPos[1], self.rawPos[2])
            cnn = c_int (numstations)
            for station in self.stations:
                if (millis - station[4]) < 1500:
                    i += 1
                    cstations[i][0] = c_double(station[0])
                    cstations[i][1] = c_double(station[1])
                    cstations[i][2] = c_double(station[2])
                    cradii[i] = c_double(station[3])
            x = c_double()
            y = c_double()
            z = c_double()
            deltar = c_double()
            multilat.wrapper.restype=c_double
            
            #ruft die wrapperfunktion in multilat.so auf
            deltar = multilat.wrapper(cstations, cstartpos, cradii, cnn, byref(x), byref(y), byref(z))
            
            #Positionen in Millimetern =)
            self.rawPos[0] = x.value
            self.rawPos[1] = y.value
            self.rawPos[2] = z.value


# siehe Python-Tutorial
# Fall dies das Hauptprogramm ist:
if __name__ == "__main__":
    Main()



"""
CHANGELOG
2013/05/17  0.7.0.2     Kommentare eingefügt - Alexander
2013/05/21  0.7.0.3     Kommentare eingefügt, Karte erweitert - Alexander
2013/05/21  0.7.0.4     Kommentare eingefügt - Alexander + Philipp
2013/06/25  0.7.2.5     Kommentare eingefügt; Funktionen: course_angle_reference()/kurswinkelflag() zur Sollwinkelberechnung und course_angle_pos() zur Istwinkelberechnung hinzugefügt und onNewPos im Teamthread erweitert -Philipp -Thomas 
2013/06/26  0.7.5.6				compare-,XBee_init- und XBee_send Funktionen hinzugefügt -Thomas
2013/06/28  0.7.10.7          Button 15,18,19 initialisiert; median-Funktion hinzugefügt -Philipp -Thomas
2013/07/02  0.7.11.8			  config-Funktion
2013/07/04  0.7.12.0    Geschwindigkeitsproblem gelöst - Alexander Reflexionen gefiltert- Thomas 
2013/07/06  0.7.12.1    Karte überarbeitet, neue Events, neue glade-Datei - Alexander

2013/07/07  0.7.13.10    ...
Code gemerged: ips_1_7_13_Alex.py mit ips_5_7_13.py+ ändern der Wegpunktnummer in Main möglich gemacht (Jetzt kein Warning mehr vor Start des Hauptfensters?!)+ initialisieren der Wegpunkte in der Main nun möglich+ team.onStart() und team.onStop() für Reset der Kurswinkelberechnung erweitert+ Init_Fenster schließen bewirkt jetzt Abbruch des Programms+ Paket manuell abwerfbar+ Kurswinkelbutton hinzugefügt+ Wegpunktanzeige ergänzt + Flugweg bei Start/Stop reseten nun möglich+ Hindernisse in der Gui entfernt um Größe des Fensters zu verkleinern-Thomas    
2013/07/08  0.7.14.0    Klassen ausgelagert. 
2014/03/17  0.7.14.1    Code funktioniert wieder: Experimentelle Trennung von Karte und Interface rückgängig gemacht.
"""

