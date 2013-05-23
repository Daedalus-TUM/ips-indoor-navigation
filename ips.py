#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-
# 21.05.2013

VERSION = (0,7,0,4)

# Änderungen bitte im CHANGELOG unten vermerken und Versionsnummer anpassen
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

DEBUG = 1

def debug(*args):
    if DEBUG:
        print(*args)

dir = os.path.dirname(__file__)
multilat=CDLL(os.path.join(dir, 'multilat.so')) #ctypes-doku

# stations[#stationsnummer]: [0-2] = x,y,z; [3] = radius in mm; [4] = letzte Aktivität
stations = [[0 for col in range(5)] for row in range(11)]

#Angabe der Positionen der Stationen; TODO: soll in finaler Version wegfallen, da über GUI eingestellt
stations[0][0] = 0
stations[0][1] = 0
stations[0][2] = 0
stations[1][0] = 0
stations[1][1] = 0
stations[1][2] = 0
stations[2][0] = 1000
stations[2][1] = 0
stations[2][2] = 0
stations[3][0] = 1000
stations[3][1] = 1000
stations[3][2] = 1000
stations[4][0] = 0
stations[4][1] = 1000
stations[4][2] = 0
stations[5][0] = -1000
stations[5][1] = 1000
stations[5][2] = 1000
stations[6][0] = -1000
stations[6][1] = 0
stations[6][2] = 0
stations[7][0] = -1000
stations[7][1] = -1000
stations[7][2] = 1000
stations[8][0] = 0
stations[8][1] = -1000
stations[8][2] = 0
stations[9][0] = 1000
stations[9][1] = -1000
stations[9][2] = 1000
stations[10][0] = 0
stations[10][1] = 0
stations[10][2] = 0

#globale Variablen für Position, darauf könnt Ihr zugreifen (lesen); gesetzt werden sie über clib_multilat.
posx = 0.0
posy = 0.0
posz = 1000.0

"""
ruft die c-lib zur Mutilateration auf, speichert die werte in posx,posy,posz
Nimmt die Daten aus dem globalen Array stations
"""
def clib_multilat():
    global posx
    global posy
    global posz
    numstations = 0
    millis = int(round(time.time() * 1000))
    #zählt die aktuell aktiven Stationen in und speichert in numstations
    for station in stations:
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
        cstartpos = cstarttype(posx, posy, posz)
        cnn = c_int (numstations)
        for station in stations:
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

        posx = x.value
        posy = y.value
        posz = z.value

"""
Diese Klasse kümmert sich um die Kommunikation mit dem Arduino (Basis-Bodenstation)
Wichtig für Euch ist die Methode send(self, txt)
zu Thread allgemein siehe threading-doku
"""
class Arduino(threading.Thread):
  global stations
  #initialisierung, wird genau einmal ausgeführt
  def __init__(self,main):
    debug("Arduino init")
    threading.Thread.__init__(self) 
    self.ttylock = threading.Lock()
    self.main = main
    self.s = serial.Serial(self.main.ttyport, 115200, 8, 'N', 1, 0.005)
    self.s.flush()
    #self.pattern = re.compile(b"deltat from (\d+) - (\d+) - (\d+\.\d+)") seit Version 0.7 veraltet
    # RegEx für Laufzeitmessungsdaten TODO: allgemeiner formulieren und speziellere Auswertung in recv_packet
    self.pattern = re.compile(b"t([0-9]{2})([0-9]{10})")
    self.run_ = True
  #Dauerschleife, Beendet falls self.run_ == False; siehe threading-doku
  def run(self):
    #debug ("Arduino start running")
    while(self.run_):
      #debug (self.s.inWaiting())
      if (self.s.inWaiting() > 0):
        self.recv_packet()
      time.sleep(0.0005) # je nach dem wie viele Pakete verschickt werden
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
    self.ttylock.acquire() #vor jedem Zugriff aus die serialle Verbindung lock setzen
    while (self.s.inWaiting() > 0):
      res = self.s.readline()
      #debug (res)
      #TODO: andere Pattern, falls noch andere Daten vom Arduino (nrf24) kommen
      tmp = self.pattern.search(res)
      if tmp is not None:
        deltat = float(tmp.group(2))
        distance = deltat * 0.345 #TODO: Temperaturanpassung, aktuell: 22°C
        if distance > 1:
            stationnr = int(tmp.group(1))
            millis = int(round(time.time() * 1000))
            stations[stationnr][3] = distance
            stations[stationnr][4] = millis
            clib_multilat()
            self.main.eventhandler.onNewPos()
      else:
        #debug (res)
        pass
    self.ttylock.release() # lock lösen
  #den Arduino neustarten
  def reset(self):
    self.s.setDTR(False)
    time.sleep(0.00001)
    self.s.setDTR(True)
  #terminiert den Thread
  def onExit(self):
    self.run_=0


# bitte kopieren mit dem Namen Team1, Team2 oder Team3
class TeamX(threading.Thread):
    """ Das ist Eure Funktionsklasse, hier kommt alles rein, was speziell Euer Team betrifft. In den Eventhandler-Funktionen bitte keine komplizierten Berechnungen durchführen, sondern nur flags setzen, da diese von einem anderen Thread berechnet werden müssten und diesen evtl. blockieren würden(=>GUI hängt, etc.). Die run-Funktion wird in Eurem Thread ausgeführt, da kommen die Berechnungen rein. Zugriff auf die gui oder arduino habt Ihr über self.main.gui bzw. self.main.arduino """
    def __init__(self, main):
        threading.Thread.__init__(self) 
        self.main = main
        debug("TeamX")
        self.run_ = True
        self.start_ = 0
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
            if self.newposflag:
                self.newposflag = False
                #hier steht code !!!!!!!!
                pass
            pass
        time.sleep(0.005) #schlafen ist gut, um die CPU nicht voll auszulasten
    def onStart(self):
        #Start-Button wurde gedrückt
        self.start_ = 1
        pass
    def onStop(self):
        #Stop-Button wurde gedrückt
        self.start_ = 0
        # reset etc.
        pass
    def onNewPos(self):
        self.newposflag = True
        #globale Variablen
        #posx
        #posy
        #posz
        #debug(posx,posy,posz)
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
    def onExit(self):
        # Programm beenden
        self.run_=False
        pass


#TODO: Team-Klassen in eigene Dateien auslagern, um den Code besser zu trennen
#TODO: Da kommt Euer Programm rein
class Team1(TeamX):
    def loop(self):
        #wird immer wieder aufgerufen, äquivalent zur Arduino-loop
        if (self.start_):
            #wegpunktnavigation etc.
            #self.main.arduino.send("TeamX fliegt!\n")
            pass
        time.sleep(0.1) #schlafen ist gut, um die CPU nicht voll auszulasten

class Team2(TeamX):
    def loop(self):
        time.sleep(0.1)

class Team3(TeamX):
    def loop(self):
        time.sleep(0.1)

"""
wie der Name schon sagt geht es hier um die GUI
Die GUI selbst ist in daedalus.glade beschrieben (Buttons,Menü etc).
Wichtig für Euch ist die Methode draw: hier wird die Karte gezeichnet
Fall jedes Team seine eigene Karte will, in draw eine main.team.METHODE aufrufen (besprecht das mit mir)
"""
class GraphicalUserInterface(threading.Thread):
    def __init__(self, main):
        threading.Thread.__init__(self)
        self.main = main
        #self.main.builder.connect_signals(EventHandler(self.main))
        window = self.main.builder.get_object("window1")
        self.drawingarea = self.main.builder.get_object("drawingarea1")
        #self.drawingarea.queue_draw()
        GObject.timeout_add(99, self.onRedraw)
        window.show_all()
        self.roti = 1 #debug
        pass
    def run(self):
        #Gdk.threads_enter()
        Gtk.main()
        #Gdk.threads_leave()
        pass
    def draw(self, widget, cr):
        #Zeichnet die Karte
        #global posx, posy, posz
        rect = self.drawingarea.get_allocation()
        self.screenx = rect.width
        self.screeny = rect.height
        a,b,c,d,e,f = self.maxdim()
        self.ppmm = min(self.screenx/(b-a),self.screeny/(d-c)) * 0.9
        self.mmdx = (a+b)/2
        self.mmdy = (c+d)/2
        #self.drawStations(widget, cr)
        self.drawStationsDebug(widget, cr) #Debug: Radien mit einzeichnen
        self.drawObstacles(widget, cr)
        self.drawPositions(widget, cr)
        self.drawLegend(widget, cr)
        self.drawWaypoints(widget, cr)
        self.drawBlimp(widget, cr)
        pass
    def mm2p(self,mmx,mmy):
        x = (mmx - self.mmdx) * self.ppmm + self.screenx/2
        y = (self.mmdy - mmy) * self.ppmm + self.screeny/2
        return x,y
    def mm2px(self,mmx):
        x = (mmx - self.mmdx) * self.ppmm + self.screenx/2
        return x
    def mm2py(self,mmy):
        y = (self.mmdy - mmy) * self.ppmm + self.screeny/2
        return y
    def maxdim(self):
        a,b,c,d,e,f = -3000,3000,-3000,3000,0,3000 #TODO: Maximalwerte bestimmen
        return a,b,c,d,e,f
    def drawBlimp(self, widget, cr):
        self.roti = self.roti + 1 #debug
        angle = self.roti/360.0 * math.pi*2 #TODO: Kompasswert oder Bewegungsrichtung aus letzten Messungen
        rotx = self.rotx
        roty = self.roty
        cr.set_line_width(2)
        cr.set_source_rgb(1, 0, 0)
        cr.move_to(self.mm2px(posx)+rotx(-9,9,angle), self.mm2py(posy)+roty(-9,9,angle))
        cr.line_to(self.mm2px(posx)+rotx(0,-12,angle), self.mm2py(posy)+roty(0,-12,angle))
        cr.line_to(self.mm2px(posx)+rotx(9,9,angle), self.mm2py(posy)+roty(9,9,angle))
        cr.line_to(self.mm2px(posx)+rotx(0,3,angle), self.mm2py(posy)+roty(0,3,angle))
        cr.close_path()
        #cr.arc(self.mm2px(posx), self.mm2py(posy), 6, 0, 2 * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 0.5, 0.5)
        cr.fill()
        pass
    def rotx(self,x,y,angle): #Hilfsfunktion für drawBlimp
        return x*math.cos(angle)+y*math.sin(angle)
    def roty(self,x,y,angle):
        return -x*math.sin(angle)+y*math.cos(angle)
    def drawWaypoints(self, widget, cr):
        #TODO: Wegpunkte, Spline (B-Spline) oder Bézierkurve
        pass
    def drawStations(self, widget, cr):
        millis = int(round(time.time() * 1000))
        cr.set_line_width(1)
        for station in stations:
            if (millis - station[4]) < 1500:
                cr.set_source_rgb(0, 1, 0)
                cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), 2, 0, 2 * math.pi)
                cr.stroke()
                #TODO: Stationsnummer dazu
        pass
    def drawStationsDebug(self, widget, cr):
        millis = int(round(time.time() * 1000))
        cr.set_line_width(1)
        for station in stations:
            if (millis - station[4]) < 1500:
                cr.set_source_rgb(0, 1, 0)
                cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), 2, 0, 2 * math.pi)
                cr.stroke()
                cr.set_source_rgb(0.6, 0.9, 0.6)
                cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), station[3]*self.ppmm, 0, 2 * math.pi)
                cr.stroke()
                if station[3]**2 > (posz-station[2])**2:
                    cr.set_source_rgb(0, 0, 0.7)
                    cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), (math.sqrt(station[3]**2 - (posz-station[2])**2 ))*self.ppmm, 0, 2 * math.pi)
                    cr.stroke()
        pass
    def drawObstacles(self, widget, cr):
        #TODO
        pass
    def drawPositions(self, widget, cr):
        #TODO: geflogene Route einzeichnen
        pass
    def drawLegend(self, widget, cr):
        #TODO
        pass
    def onNewPos(self):
        #threading.Thread(target=self.drawingarea.queue_draw).start()
        #self.drawingarea.queue_draw()
        #GObject.idle_add(self.drawingarea.queue_draw)
        pass
    def onRedraw(self):
        self.drawingarea.queue_draw()
        return True


"""
Der EventHandler kümmert sich um auftretende Ereignisse, wie z.B. "es gibt eine neue Position", "Button 5 gedrückt", etc.
zu den Events habe ich in die erste Zeile jeweils die Funktion geschrieben, ich hoffe das ist klar, sonst einfach fragen.
Hier muss noch einiges ergänzt werden, siehe TODO
Es sollten hier keine langwierigen Geschichten geschrieben werden ;) am Besten nur Flags setzen
"""
class EventHandler:
    def __init__(self, main):
        self.main = main
    #menu
    def on_imagemenuitem5_activate(self, *args):
        #beenden
        Gtk.main_quit(*args)
    def on_imagemenuitem1_activate(self, *args):
        #neu TODO
        pass
    def on_imagemenuitem2_activate(self, *args):
        #öffnen TODO
        pass
    def on_imagemenuitem3_activate(self, *args):
        #speichern TODO
        pass
    def on_imagemenuitem4_activate(self, *args):
        #speichern unter TODO
        pass
    def on_imagemenuitem10_activate(self, *args):
        #hilfe info about TODO
        pass
    #window
    def onDeleteWindow(self, *args):
        Gtk.main_quit(*args)
        self.main.team.onExit()
        self.main.arduino.onExit()
    def on_window1_destroy(self, *args):
        Gtk.main_quit(*args)
        self.main.team.onExit()
        self.main.arduino.onExit()
    def on_window2_destroy(self, *args):
        Gtk.main_quit(*args)
    def on_window2_delete_event(self, *args):
        Gtk.main_quit(*args)
    #drawingarea
    def on_drawingarea1_draw(self, *args):
        #do_expose_event(*args)
        self.main.gui.draw(*args)
    #TODO
    #buttons
    #zum Testen kann in der Methode TeamX.onButtonPressed die print Zeile einkommentiert werden
    def on_button1_pressed(self, *args):
        #wp add TODO: Nummer anpassen
        #wp = WegPunkt
        self.main.team.onButtonPressed(1)
        self.main.waypointlist.append((11, 111, 222, 333, "neu")) #fügt den neuen WP hinzu, nicht 0 setzen, da BUG
        self.main.team.onWaypointUpdate()
    def on_button2_pressed(self, *args):
        #wp remove TODO: Nummern der verbliebenen anpassen
        self.main.team.onButtonPressed(2)
        model, treeiter = self.main.builder.get_object("treeview-selection").get_selected()
        model.iter_next(treeiter)
        model.remove(treeiter)
        self.main.team.onWaypointUpdate()
    def on_button3_pressed(self, *args):
        #wp rauf  TODO: Nummern anpassen
        self.main.team.onButtonPressed(3)
        model, treeiter = self.main.builder.get_object("treeview-selection").get_selected()
        prev = model.iter_previous(treeiter)
        if prev:
            model.swap(treeiter, prev)
        self.main.team.onWaypointUpdate()
    def on_button4_pressed(self, *args):
        #wp runter TODO: Nummern anpassen
        self.main.team.onButtonPressed(4)
        model, treeiter = self.main.builder.get_object("treeview-selection").get_selected()
        next = model.iter_next(treeiter)
        if next:
            model.swap(treeiter, next)
        
        self.main.team.onWaypointUpdate()
    def on_button5_pressed(self, *args):
        #wp springe zu TODO: Fliege WP an (gehört eher in die Team Klasse ??? Wie soll WP-Liste organiesiet sein)
        self.main.team.onButtonPressed(5)
    def on_button11_pressed(self, *args):
        #hindernis add TODO
        self.main.team.onButtonPressed(11)
    def on_button14_pressed(self, *args):
        #hindernis remove TODO
        self.main.team.onButtonPressed(14)
    def on_button6_pressed(self, *args):
        #start
        self.main.team.onStart()
        self.main.team.onButtonPressed(6)
    def on_button7_pressed(self, *args):
        #stop
        self.main.team.onStop()
        self.main.team.onButtonPressed(7)
    def on_button8_pressed(self, *args):
        #abstürzen
        self.main.team.onButtonPressed(8)
    def on_button9_pressed(self, *args):
        #bombe
        self.main.team.onButtonPressed(9)
    def on_button10_pressed(self, *args):
        #kreis
        self.main.team.onButtonPressed(10)
    def on_button12_pressed(self, *args):
        #init-Fenster reload 
        pass
    def on_button13_pressed(self, *args):
        #init-Fenster und los
        self.on_window2_destroy()
        self.main.builder.get_object("window2").destroy()
        #init go
        pass
    def on_button15_pressed(self, *args):
        #edit wp TODO: neues Fenster soll geöffnet werden um Daten in Textfelden zu bearbeiten, zweitrangig
        self.main.team.onButtonPressed(15)
    def on_button16_pressed(self, *args):
        #edit obstacle TODO
        self.main.team.onButtonPressed(16)
    def on_button17_pressed(self, *args):
        #edit station TODO
        self.main.team.onButtonPressed(17)

    #edited: text wurde geändert
    def on_cellrenderertext2_edited(self, widget, path, text):
        #wp x
        self.main.waypointlist[path][1] = int(text)
        self.main.team.onWaypointUpdate()
        pass
    def on_cellrenderertext3_edited(self, widget, path, text):
        #wp y
        self.main.waypointlist[path][2] = int(text)
        self.main.team.onWaypointUpdate()
        pass
    def on_cellrenderertext4_edited(self, widget, path, text):
        #wp z
        self.main.waypointlist[path][3] = int(text)
        self.main.team.onWaypointUpdate()
        pass
    def on_cellrenderertext16_edited(self, widget, path, text):
        #wp typ
        self.main.waypointlist[path][4] = text
        self.main.team.onWaypointUpdate()
        pass
    def on_cellrenderertext5_edited(self, widget, path, text):
        #hindernis x
        self.main.obstaclelist[path][0] = int(text)
        self.main.team.onObstacleUpdate()
        pass
    def on_cellrenderertext6_edited(self, widget, path, text):
        #hindernis y
        self.main.obstaclelist[path][1] = int(text)
        self.main.team.onObstacleUpdate()
        pass
    def on_cellrenderertext7_edited(self, widget, path, text):
        #hindernis z
        self.main.obstaclelist[path][2] = int(text)
        self.main.team.onObstacleUpdate()
        pass
    def on_cellrenderertext8_edited(self, widget, path, text):
        #hindernis r
        self.main.obstaclelist[path][3] = int(text)
        self.main.team.onObstacleUpdate()
        pass
    def on_cellrenderertext10_edited(self, widget, path, text):
        #station x
        debug (path)
        stations[int(path)][0]=int(text)
        self.main.stationlist[path][1] = int(text)
        pass
    def on_cellrenderertext11_edited(self, widget, path, text):
        #station y
        self.main.stationlist[path][2] = int(text)
        pass
    def on_cellrenderertext12_edited(self, widget, path, text):
        #station z
        self.main.stationlist[path][3] = int(text)
        pass
    #neue Position
    def onNewPos(self, *args):
        self.main.team.onNewPos()
        self.main.builder.get_object("label14").set_text('%.0f' % posx)
        self.main.builder.get_object("label15").set_text('%.0f' % posy)
        self.main.builder.get_object("label16").set_text('%.0f' % posz)
        #self.main.gui.onNewPos()
        pass

# Startfenster zur Auswahl des seriellen Ports und des Teams
# TODO: "und los" Button soll das Fenster zerstören
class Init():
    def __init__(self, main):
        self.main = main
        debug(self.main.ttyport,self.main.team)
        builder = Gtk.Builder()
        #builder.add_from_file("/home/alex/ips/glade_gui/daedalus.glade")
        builder.add_from_file(os.path.join(dir, 'daedalus.glade'))
        builder.connect_signals(EventHandler(self.main))
        window = builder.get_object("window2")
        self.ttybox = builder.get_object("buttonbox4")
        self.teambox = builder.get_object("buttonbox5")
        reloadbtn = builder.get_object("button12")
        reloadbtn.connect("pressed", self.reloadtty)
        self.reloadtty("")
        #add your team here DONE
        button1 = Gtk.RadioButton(group=None, label="Alex")
        button1.connect("toggled", self.setteam, "TeamX")
        self.teambox.pack_start(button1, True, True, 0)
        self.main.team = "TeamX"
        button = Gtk.RadioButton(group=button1, label="Team1")
        button.connect("toggled", self.setteam, "Team1")
        self.teambox.pack_start(button, True, True, 0)
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
        # initialisiere Variablen, werden von initfenster beschrieben
        self.team = 0
        self.ttyport = 0
        # Variablen für GUI und alles andere
        self.waypointlist = 0
        self.obstaclelist = 0
        self.stationlist = 0
        self.builder = 0
        # Initfenster
        Init(self)
        
        if self.team and self.ttyport:
          if self.team == "TeamX":
            self.team = TeamX(self)
          if self.team == "Team1":
            self.team = Team1(self)
          if self.team == "Team2":
            self.team = Team2(self)
          if self.team == "Team3":
            self.team = Team3(self)
        else:
            debug("init failed, please specify a tty port and a team")
            debug(self.ttyport,self.team)
            sys.exit() #TODO: dem Benutzer das in der GUI beibringen, anstatt einfach das Programm zu benden
        self.builder = Gtk.Builder() #Lade GUI aus glade Datei
        self.builder.add_from_file(os.path.join(dir, 'daedalus.glade')) #TODO: Macht manchmal Probleme
        self.eventhandler = EventHandler(self)
        self.builder.connect_signals(self.eventhandler)

        #TODO: ??? in welcher Form sollen WP etc gespeichert werden?
        self.waypointlist = self.builder.get_object("liststore1")
        self.obstaclelist = self.builder.get_object("liststore2")
        self.stationlist = self.builder.get_object("liststore3")
        # Stationen syncronisieren mit GUI
        for i in range(len(stations)):
            tmp = [i,stations[i][0],stations[i][1],stations[i][2],stations[i][3],3.8,1]
            self.stationlist.append(tmp)
            
        self.arduino = Arduino(self)
        self.gui = GraphicalUserInterface(self)
        #starte Thread
        self.arduino.start()
        self.team.start()
        self.gui.start()
        #join wartet bis Thread terminiert
        self.arduino.join()
        self.gui.join()
        self.team.join()

# siehe Python-Tutorial
# Fall dies das Hauptprogramm ist:
if __name__ == "__main__":
    Main()



"""
CHANGELOG
2013/05/17  0.7.0.2     Kommentare eingefügt - Alexander
2013/05/21  0.7.0.3     Kommentare eingefügt, Karte erweitert - Alexander
2013/05/21  0.7.0.4     Kommentare eingefügt - Alexander + Philipp

"""
