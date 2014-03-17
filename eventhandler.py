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
try:    
    import thread 
except ImportError:
    import _thread as thread #Py3K changed it.

"""
Der EventHandler kümmert sich um auftretende Ereignisse, wie z.B. "es gibt eine neue Position", "Button 5 gedrückt", etc.
zu den Events habe ich in die erste Zeile jeweils die Funktion geschrieben, ich hoffe das ist klar, sonst einfach fragen.
Hier muss noch einiges ergänzt werden, siehe TODO
Es sollten hier keine langwierigen Geschichten geschrieben werden ;) am Besten nur Flags setzen
"""
class EventHandler:
    def __init__(self, main):
        self.main = main
        self.window2flag = True
        self.wprunterflag = False
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
        sys.exit()
    def on_window2_destroy(self, *args):
        Gtk.main_quit(*args)
        if self.window2flag:
            sys.exit()
    def on_window2_delete_event(self, *args):
        Gtk.main_quit(*args)
    def on_window3_destroy(self, *args):
        Gtk.main_quit(*args)
        self.main.team.onExit()
        self.main.arduino.onExit()
    #drawingarea
    def on_drawingarea1_draw(self, widget, cr):
        #do_expose_event(*args)
        #self.main.gui.draw(*args)
        #self.main.gui.drawing(self.main, *args)
        #thread.start_new_thread(self.main.gui.drawing, (widget, cr,))
        self.main.gui.drawing(widget, cr)
        #self.main.map.onDraw(widget, cr)
    #TODO
    #buttons
    #zum Testen kann in der Methode TeamX.onButtonPressed die print Zeile einkommentiert werden
    def on_button1_pressed(self, *args):
        #wp add TODO: Nummer anpassen
        #wp = WegPunkt
        self.main.team.onButtonPressed(1)
        self.main.waypointlist.append((len(self.main.waypointlist), 111, 222, 333, "neu")) #fügt den neuen WP hinzu, nicht 0 setzen, da BUG
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
        self.wprunterflag = True
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
        #start: Test von Sollwinkelfunktion
        self.main.team.onStart()
        #self.main.team.setkurswinkelflag()
        self.main.team.onButtonPressed(6)

    def on_button7_pressed(self, *args):
        #stop
        self.main.team.onStop()
        self.main.team.onButtonPressed(7)

    def on_button8_pressed(self, *args):
        #abstürzen: #Test von Istwinkelfunktion
        self.main.team.course_angle_pos()
        self.main.team.onButtonPressed(8)

    def on_button9_pressed(self, *args):
        #bombe
        if self.main.team.XBeeflag:
            self.main.team.onButtonPressed(9)
            string = "bdrop\n"
            self.main.team.XBee_send(string)
            print("Paket abgeworfen\n\n")
            string = ''
        else:
            print("Konnte Paket nicht abwerfen, schließen Sie XBee an.")

    def on_button10_pressed(self, *args):
        #kreis
        self.main.team.onButtonPressed(10)

    def on_button12_pressed(self, *args):
        #init-Fenster reload 
        pass

    def on_button13_pressed(self, *args):
        #init-Fenster und los
        self.window2flag = False
        self.on_window2_destroy()
        self.main.builder.get_object("window2").destroy()
        #init go
        pass

    def on_button15_pressed(self, *args):
        #edit wp TODO: neues Fenster soll geöffnet werden um Daten in Textfelden zu bearbeiten, zweitrangig
        self.main.team.onButtonPressed(15)
        self.main.builder.get_object("window3")
        self.main.builder.get_object("window3").show_all()
        

    def on_button16_pressed(self, *args):
        #edit obstacle TODO
        self.main.team.onButtonPressed(16)

    def on_button17_pressed(self, *args):
        #edit station TODO
        self.main.team.onButtonPressed(17)
        
    def on_button18_pressed(self, *args):
        #close window3
        self.main.team.onButtonPressed(18)
        on_window3_destroy(self, *args)
        
    def on_button19_pressed(self, *args):
        #edit liststore1
        self.main.team.onButtonPressed(19)
        pass
    ##    
    def on_button20_pressed(self, *args):
        #Radien anzeigen
        self.main.team.onButtonPressed(20)
        if self.main.gui.showRadius:
            self.main.gui.showRadius = False
        else:
            self.main.gui.showRadius = True
        pass
    def on_button21_pressed(self, *args):
        #Flugweg zurücksetzen
        self.main.positionslist = [[self.main.filterdPos[0],self.main.filterdPos[1],self.main.filterdPos[2]]]
        self.main.team.onButtonPressed(21)
        pass
    def on_button22_pressed(self, *args):
        #Wegpunktwinkel ausgeben lassen
        self.main.team.kurswinkelflag = True
        self.main.team.course_angle_reference()
        self.main.team.onButtonPressed(22)
        pass
    def on_button23_pressed(self, *args):
        #etc
        self.main.team.onButtonPressed(23)
        pass
    def on_button24_pressed(self, *args):
        #etc
        self.main.team.onButtonPressed(24)
        pass    
    ##    
    #edited: text wurde geändert
    
    ###
    def on_cellrenderertext1_edited(self, widget, path, text):
        #NR
        self.main.waypointlist[path][0] = int(text)
        self.main.waypoints[int(path)][3] = int(text)
        self.main.team.onWaypointUpdate()
        pass
    
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
        self.main.stations[int(path)][0]=int(text)
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
        #debug("Team.NewPos")
        self.main.team.onNewPos()
        self.main.builder.get_object("label14").set_text('%.0f' % self.main.filterdPos[0])
        self.main.builder.get_object("label15").set_text('%.0f' % self.main.filterdPos[1])
        self.main.builder.get_object("label16").set_text('%.0f' % self.main.filterdPos[2])
        ##
        self.main.positionslist.append([self.main.filterdPos[0],self.main.filterdPos[1],self.main.filterdPos[2]])
        ##
        #self.main.gui.onNewPos()
        pass
