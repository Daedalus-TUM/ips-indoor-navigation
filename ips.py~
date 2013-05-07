#!/usr/bin/env python3
# -*- coding: iso-8859-1 -*-
# Version 0.6
# 24.04.2013
from gi.repository import Gtk,Gdk, GLib, GObject
import math
import random
import os
import glob
import sys, traceback
import time
from ctypes import *
import threading 
import serial
import re


dir = os.path.dirname(__file__)
multilat=CDLL(os.path.join(dir, 'multilat.so'))

stations = [[0 for col in range(5)] for row in range(11)]

"""stations[0][0] = 0
stations[0][1] = 0
stations[0][2] = 0
stations[1][0] = 0
stations[1][1] = 0
stations[1][2] = 0
stations[2][0] = 1665
stations[2][1] = 0
stations[2][2] = 0
stations[3][0] = 0
stations[3][1] = 0
stations[3][2] = 0
stations[4][0] = 0
stations[4][1] = 3020
stations[4][2] = 470
stations[5][0] = 1665
stations[5][1] = 3020
stations[5][2] = 0"""
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

posx = 0.0
posy = 0.0
posz = 1000.0

""" democode - kann ignoriert werden """
# The number of circles and the window size.
num = 6
size = 512
red = 1
green = 0
blue = 0
# Initialize circle coordinates and velocities.
x = []
y = []
xv = []
yv = []
for i in range(num):
    x.append(random.randint(0, size))
    y.append(random.randint(0, size))
    if i < 5:
        xv.append(0)
        yv.append(0)
    if i > 4:
        xv.append(random.randint(-4, 4))
        yv.append(random.randint(-4, 4))
    
def do_expose_event(widget, cr):
    global red
    global green
    global blue
    #cr = self.window.cairo_create()

    # Restrict Cairo to the exposed area; avoid extra work


    cr.set_line_width(4)
    for i in range(num):
        cr.set_source_rgb(red, green, blue)
        cr.arc(x[i], y[i], 8, 0, 2 * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()
        x[i] += xv[i]
        y[i] += yv[i]
        if x[i] > size or x[i] < 0:
            xv[i] = -xv[i]
        if y[i] > size or y[i] < 0:
            yv[i] = -yv[i]
    widget.queue_draw()

""" democode Ende """

# ruft die c-lib zur Mutilateration auf, speichert die werte in posx,posy,posz
def clib_multilat():
    global posx
    global posy
    global posz
    numstations = 0
    millis = int(round(time.time() * 1000))
    for station in stations:
        if (millis - station[4]) < 1500:
            numstations += 1
    if (numstations > 2):
        i = -1
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
        

        deltar = multilat.wrapper(cstations, cstartpos, cradii, cnn, byref(x), byref(y), byref(z))

        posx = x.value
        posy = y.value
        posz = z.value
        #print (posx, posy, posz)


class Arduino(threading.Thread):
  global stations
  def __init__(self,main):
    threading.Thread.__init__(self) 
    self.ttylock = threading.Lock()
    self.main = main
    self.s = serial.Serial(self.main.ttyport, 115200, 8, 'N', 1, 0.05)
    self.s.flush()
    self.pattern = re.compile(b"deltat from (\d+) - (\d+) - (\d+\.\d+)")
    self.run_ = True
  def run(self):
    while(self.run_):
      if (self.s.inWaiting() > 0):
        self.recv_packet()
      time.sleep(0.0005) # je nach dem wie viele Pakete verschickt werden
  def setled(self, led, state):
    self.ttylock.acquire()
    self.s.write("\x02" + led + chr(state) + "\x03")
    self.s.flush()
    self.recv_packet()
    self.ttylock.release()
  def send(self, txt):
    self.ttylock.acquire()
    self.s.write(bytes(txt, 'UTF-8'))
    self.s.flush()
    self.ttylock.release()
  def recv_packet(self):
    self.ttylock.acquire()
    if (self.s.inWaiting() > 0):
      res = self.s.readline()
      #print (res)
      tmp = self.pattern.search(res)
      if tmp is not None:
        deltat = float(tmp.group(2))
        deltat = deltat * 0.34
        if deltat > 1:
            stationnr = int(tmp.group(1))
            millis = int(round(time.time() * 1000))
            stations[stationnr][3] = deltat
            stations[stationnr][4] = millis
            clib_multilat()
            self.main.eventhandler.onNewPos()
      else:
        print (res)
    self.ttylock.release()
  def reset(self):
    self.s.setDTR(False)
    time.sleep(0.00001)
    self.s.setDTR(True)
  def onExit(self):
    self.run_=0

# Startfenster zur Auswahl des seriellen Ports und des Teams
class init():
    def __init__(self, main):
        self.main = main
        print(self.main.ttyport,self.main.team)
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
        # TODO add your team here
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
        Gtk.main()
    def setttydev(self, button, dev):
        if button.get_active():
            self.main.ttyport = dev
            print("tty=",self.main.ttyport)
    def setteam(self, button, team_):
        if button.get_active():
            self.main.team = team_
            print("team=",self.main.team)
    def reloadtty(self, button):
        #ladde tty ports
        ttydevs = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')# + glob.glob('/dev/ttyS*')
        for i in self.ttybox.get_children():
            self.ttybox.remove(i)
        if len(ttydevs) == 0:
          print ("error: no tty Port")
        else:
          button = None
          for item in ttydevs:
            if button == None:
                self.main.ttyport = item
            button = Gtk.RadioButton(group=button, label=item)
            button.connect("toggled", self.setttydev, item)
            self.ttybox.pack_start(button, True, True, 0)
            self.ttybox.show_all()


# bitte kopieren mit dem Namen Team1, Team2 oder Team3
class TeamX(threading.Thread):
    """ Das ist Eure Funktionsklasse, hier kommt alles rein, was speziell Euer Team betrifft. In den Eventhandler-Funktionen bitte keine komplizierten Berechnungen durchführen, sondern nur flags setzen, da diese von einem anderen Thread berechnet werden müssten und diesen evtl. blockieren würden(=>GUI hängt, etc.). Die run-Funktion wird in Eurem Thread ausgeführt, da kommen die Berechnungen rein. Zugriff auf die gui oder arduino habt Ihr über self.main.gui bzw. self.main.arduino """
    def __init__(self, main):
        threading.Thread.__init__(self) 
        self.main = main
        print("TeamX")
        self.run_ = True
        self.start_ = 0
    def run(self):
        i=0
        while(self.run_):
            i=i+1
            #print("TeamX run:",i)
            if (self.start_):
                #wegpunktnavigation etc.
                self.main.arduino.send("TeamX fliegt!\n")
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
        #globale Variablen
        #posx
        #posy
        #posz
        #print(posx,posy,posz)
        pass
    def onButtonPressed(self, i):
        #welcher Button welche Nummer hat seht Ihr in der glade Datei oder im Eventhandler
        print(i)
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
        pass
    def run(self):
        #Gdk.threads_enter()
        Gtk.main()
        #Gdk.threads_leave()
        pass
    def draw(self, widget, cr):
        #global posx, posy, posz
        millis = int(round(time.time() * 1000))
        cr.set_line_width(1)
        for station in stations:
            if (millis - station[4]) < 1500:
                cr.set_source_rgb(0, 1, 0)
                cr.arc(station[0]/16 + 256, station[1]/16 + 256, 2, 0, 2 * math.pi)
                cr.stroke()
                cr.set_source_rgb(0.6, 0.9, 0.6)
                cr.arc(station[0]/16 + 256, station[1]/16 + 256, station[3]/16, 0, 2 * math.pi)
                cr.stroke()
                if station[3]**2 > (posz-station[2])**2:
                    cr.set_source_rgb(0, 0, 0.7)
                    cr.arc(station[0]/16 + 256, station[1]/16 + 256, (math.sqrt(station[3]**2 - (posz-station[2])**2 ))/16, 0, 2 * math.pi)
                    cr.stroke()
        cr.set_source_rgb(1, 0, 0)
        cr.arc(posx/16 + 256, posy/16 + 256, 6, 0, 2 * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 0.5, 0.5)
        #cr.fill()
        #time.sleep(0.02)
        #widget.queue_draw()
        #GObject.idle_add(self.draw, widget, cr)
        pass
    def drawWaypoints(self):
        pass
    def drawStations(self):
        pass
    def drawObstacles(self):
        pass
    def drawPositions(self):
        pass
    def drawStations(self):
        pass
    def drawLegend(self):
        pass
    def onNewPos(self):
        #threading.Thread(target=self.drawingarea.queue_draw).start()
        #self.drawingarea.queue_draw()
        #GObject.idle_add(self.drawingarea.queue_draw)
        pass
    def onRedraw(self):
        self.drawingarea.queue_draw()
        return True

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
    def on_button1_pressed(self, *args):
        #wp add TODO: Nummern anpassen
        self.main.team.onButtonPressed(1)
        self.main.waypointlist.append((11, 111, 222, 333, "neu"))
        self.main.team.onWaypointUpdate()
    def on_button2_pressed(self, *args):
        #wp remove TODO: Nummern anpassen
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
        #wp springe zu TODO
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
        #init reload 
        pass
    def on_button13_pressed(self, *args):
        self.on_window2_destroy()
        self.main.builder.get_object("window2").destroy()
        #init go
        pass
    def on_button15_pressed(self, *args):
        #edit wp TODO
        self.main.team.onButtonPressed(15)
    def on_button16_pressed(self, *args):
        #edit obstacle TODO
        self.main.team.onButtonPressed(16)
    def on_button17_pressed(self, *args):
        #edit station TODO
        self.main.team.onButtonPressed(17)

    #edited
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
        #hindernis zto
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

    def onNewPos(self, *args):
        self.main.team.onNewPos()
        self.main.builder.get_object("label14").set_text('%.0f' % posx)
        self.main.builder.get_object("label15").set_text('%.0f' % posy)
        self.main.builder.get_object("label16").set_text('%.0f' % posz)
        #self.main.gui.onNewPos()
        pass


class main():
    def __init__(self):
        #Gdk.threads_init()
        self.team = ""
        self.ttyport = ""
        self.waypointlist = ""
        self.obstaclelist = ""
        self.stationlist = ""
        self.builder = ""
        init(self)
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
            print("init failed, please specify a tty port and a team")
            print(self.ttyport,self.team)
            sys.exit() 
        self.builder = Gtk.Builder()
        #builder.add_from_file("/home/alex/ips/glade_gui/daedalus.glade")
        self.builder.add_from_file(os.path.join(dir, 'daedalus.glade'))
        self.eventhandler = EventHandler(self)
        self.builder.connect_signals(self.eventhandler)
        window = self.builder.get_object("window1")
        drawingarea = self.builder.get_object("drawingarea1")
        self.waypointlist = self.builder.get_object("liststore1")
        self.obstaclelist = self.builder.get_object("liststore2")
        self.stationlist = self.builder.get_object("liststore3")
        
        self.arduino = Arduino(self)
        self.gui = GraphicalUserInterface(self)
        self.arduino.start()
        self.team.start()
        self.gui.start()
        
        self.arduino.join()
        self.gui.join()
        self.team.join()


if __name__ == "__main__":
    main()
