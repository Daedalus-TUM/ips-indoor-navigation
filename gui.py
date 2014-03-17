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
import colorsys
try:    
    import thread 
except ImportError:
    import _thread as thread #Py3K changed it.
"""
wie der Name schon sagt geht es hier um die GUI
Die GUI selbst ist in daedalus.glade beschrieben (Buttons,Menü etc).
Wichtig ist die Methode draw: hier wird die Karte gezeichnet
"""
class GraphicalUserInterface(threading.Thread):
    def __init__(self, main):
        threading.Thread.__init__(self)
        self.main = main
        self.run_ = True
        self.showPositionflag = True
        #self.main.builder.connect_signals(EventHandler(self.main))
        window = self.main.builder.get_object("window1")
        self.drawingarea = self.main.builder.get_object("drawingarea1")
        #self.drawingarea.queue_draw()
        GObject.timeout_add(99, self.onRedraw)
        window.show_all()
        self.roti = 1 #debug
        self.showRadius = False
        pass
        
    def onExit(self):
        # Programm beenden
        self.run_=False
        pass
        
    def run(self):
        ##while (self.run_):
            ##
        Gdk.threads_enter() #Gdk.threads_enter()
            ##
        Gtk.main()
            ##
        Gdk.threads_leave() #Gdk.threads_leave()
            ##
        pass
    def draw(self, widget, cr):
        self.drawing(widget, cr)
        #thread.start_new_thread(self.drawing, (widget, cr,)) 
        pass
    def drawing(self, widget, cr):
        #Zeichnet die Karte
        rect = self.drawingarea.get_allocation()
        self.screenx = rect.width
        self.screeny = rect.height
        a,b,c,d,e,f = self.maxdim()
        self.zmin = e
        self.zmax = f
        self.ppmm = min(self.screenx/(b-a),self.screeny/(d-c)) * 0.8
        self.mmdx = (a+b)/2
        self.mmdy = (c+d)/2
        ##
        self.drawStations(widget, cr)#self.drawStations(widget, cr)
        ##
        ##
        if self.showRadius:
            self.drawStationsDebug(widget, cr)
        #self.drawStationsDebug(widget, cr) #Debug: Radien mit einzeichnen
        ##
        self.drawObstacles(widget, cr)
        if self.showPositionflag:
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
        ##
        a = min(min(self.main.stations, key=lambda x: x[0])[0],self.main.filterdPos[0])
        b = max(max(self.main.stations, key=lambda x: x[0])[0],self.main.filterdPos[0])
        c = min(min(self.main.stations, key=lambda x: x[1])[1],self.main.filterdPos[1])
        d = max(max(self.main.stations, key=lambda x: x[1])[1],self.main.filterdPos[1])
        e = min(min(self.main.stations, key=lambda x: x[2])[2],self.main.filterdPos[2])
        f = max(max(self.main.stations, key=lambda x: x[2])[2],self.main.filterdPos[2])
        #a,b,c,d,e,f = -3000,3000,-3000,3000,0,3000 #TODO: Maximalwerte bestimmen
        ##
        return a,b,c,d,e,f
        #print( a[0],b[0],c[1],d[1],e[2],f[2])
        #return a[0],b[0],c[1],d[1],e[2],f[2]
    def zcolor (self, z):
        h = (z - self.zmin) / (self.zmax - self.zmin)
        if h < 0.0:
            h = 0.0
        elif h > 1.0:
            h = 1.0
        if h < 0.25:
            r = 0
            g = 4*h
            b = 1
        elif h < 0.5:
            r = 0
            g = 1
            b = 2-4*h
        elif h < 0.75:
            r = 4*h-2
            g = 1
            b = 0
        else:
            r = 1
            g = 4-4*h
            b = 0
        return r,g,b
    def drawBlimp(self, widget, cr):
        #self.roti = self.roti + 5 #debug
        self.roti = self.main.heading
        angle = self.roti/360.0 * math.pi*2 #TODO: Kompasswert oder Bewegungsrichtung aus letzten Messungen
        rotx = self.rotx
        roty = self.roty
        cr.set_line_width(2)
        cr.set_source_rgb(1, 0, 0)
        r,g,b = self.zcolor(self.main.filterdPos[2])
        cr.set_source_rgb(r,g,b)
        cr.move_to(self.mm2px(self.main.filterdPos[0])+rotx(-9,9,angle), self.mm2py(self.main.filterdPos[1])+roty(-9,9,angle))
        cr.line_to(self.mm2px(self.main.filterdPos[0])+rotx(0,-12,angle), self.mm2py(self.main.filterdPos[1])+roty(0,-12,angle))
        cr.line_to(self.mm2px(self.main.filterdPos[0])+rotx(9,9,angle), self.mm2py(self.main.filterdPos[1])+roty(9,9,angle))
        cr.line_to(self.mm2px(self.main.filterdPos[0])+rotx(0,3,angle), self.mm2py(self.main.filterdPos[1])+roty(0,3,angle))
        cr.close_path()
        #cr.arc(self.mm2px(self.main.filterdPos[0]), self.mm2py(self.main.filterdPos[1]), 6, 0, 2 * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgba(r,g,b,0.5)
        cr.fill()
        pass
    def rotx(self,x,y,angle): #Hilfsfunktion für drawBlimp
        return x*math.cos(angle)+y*math.sin(angle)
    def roty(self,x,y,angle):
        return -x*math.sin(angle)+y*math.cos(angle)
    def drawWaypoints(self, widget, cr):
        #TODO: Wegpunkte, Spline (B-Spline) oder Bézierkurve
        
        cr.set_line_width(1)
        for index, waypoint in enumerate(self.main.waypointlist):
            cr.set_source_rgb(0,0,0)
            cr.arc(self.mm2px(waypoint[1]), self.mm2py(waypoint[2]), 2, 0, 2 * math.pi)
            cr.stroke()
            # Wegpunktnummer dazu
            cr.select_font_face("Courier", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(14)
            cr.new_path()
            cr.move_to(self.mm2px(waypoint[1])+ 4, self.mm2py(waypoint[2]))
            if self.main.eventhandler.wprunterflag:
                cr.show_text('WP'+str(index))
            else:
                cr.show_text('WP'+str(waypoint[0]))
            cr.new_path()
        pass
    def drawStations(self, widget, cr):
        millis = int(round(time.time() * 1000))
        cr.set_line_width(1)
        ##
        for index, station in enumerate(self.main.stations):
        #for self.main.station in self.main.stations:
        ##
            if (millis - station[4]) < 1500:
                cr.set_source_rgb(0,1,0)
                ##
                cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), 2, 0, 2 * math.pi)
                #cr.arc(self.mm2px(self.main.station[0]), self.mm2py(self.main.station[1]), 2, 0, 2 * math.pi)
                ##
                cr.stroke()
                #TODO: Stationsnummer dazu
            ##
            else:
                cr.set_source_rgb(1, 0, 0)
                cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), 2, 0, 2 * math.pi)
                cr.stroke()
            # Stationsnummer dazu
            cr.select_font_face("Courier", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
            cr.set_font_size(10)
            cr.new_path()
            cr.move_to(self.mm2px(station[0])+ 4, self.mm2py(station[1]))
            cr.show_text(str(index))
            cr.new_path()
            ##
        pass
    def drawStationsDebug(self, widget, cr):
        millis = int(round(time.time() * 1000))
        cr.set_line_width(1)
        ##
        for station in self.main.stations:
        #for self.main.station in self.main.stations:
            ##
            if (millis - station[4]) < 300:
                cr.set_source_rgba(0.2, 0.9, 0.2, 0.5)
                cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), station[3]*self.ppmm, 0, 2 * math.pi)
                cr.stroke()
                if station[3]**2 > (self.main.filterdPos[2]-station[2])**2:
                    cr.set_source_rgba(0, 0, 0.7, 0.5)
                    cr.arc(self.mm2px(station[0]), self.mm2py(station[1]), (math.sqrt(station[3]**2 - (self.main.filterdPos[2]-station[2])**2 ))*self.ppmm, 0, 2 * math.pi)
                    cr.stroke()
            '''
            if (millis - self.main.station[4]) < 1500:
                cr.set_source_rgb(0, 1, 0)
                cr.arc(self.mm2px(self.main.station[0]), self.mm2py(self.main.station[1]), 2, 0, 2 * math.pi)
                cr.stroke()
                cr.set_source_rgb(0.6, 0.9, 0.6)
                cr.arc(self.mm2px(self.main.station[0]), self.mm2py(self.main.station[1]), self.main.station[3]*self.ppmm, 0, 2 * math.pi)
                cr.stroke()
                if self.main.station[3]**2 > (self.main.filterdPos[2]-self.main.station[2])**2:
                    cr.set_source_rgb(0, 0, 0.7)
                    cr.arc(self.mm2px(self.main.station[0]), self.mm2py(self.main.station[1]), (math.sqrt(self.main.station[3]**2 - (self.main.filterdPos[2]-self.main.station[2])**2 ))*self.ppmm, 0, 2 * math.pi)
                    cr.stroke()
                    '''
        pass
    def drawObstacles(self, widget, cr):
        #TODO
        pass
    def drawPositions(self, widget, cr):
        ##
        cr.set_line_width(1)
        cr.set_source_rgb(0, 0, 0)
        maxpoints = len(self.main.positionslist)
        i = 0
        for point in self.main.positionslist:
            if i == 0:
                cr.move_to(self.mm2px(point[0]), self.mm2py(point[1]))
            r,g,b = self.zcolor(point[2])
            cr.set_source_rgb(r,g,b)
            i = i+1
            cr.line_to(self.mm2px(point[0]), self.mm2py(point[1]))
            cr.stroke()
            cr.move_to(self.mm2px(point[0]), self.mm2py(point[1]))
        #cr.stroke()
        ##
        #TODO: geflogene Route einzeichnen
        pass
    def drawLegend(self, widget, cr):
        #TODO
        cr.select_font_face("Courier", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
        cr.set_font_size(10)
        cr.set_source_rgb(0, 0, 0)
        cr.move_to(self.screenx - 5,self.screeny - 5)
        cr.rel_line_to(-1000 * self.ppmm, 0)
        cr.stroke()
        cr.move_to(self.screenx - 5 -15 -1000 * self.ppmm, self.screeny - 2)
        cr.show_text("1m")
        cr.new_path()
        
        lg = cairo.LinearGradient(0, self.screeny - 125, 0, self.screeny - 25)
        lg.add_color_stop_rgba(0.0, 1, 0, 0, 1)
        lg.add_color_stop_rgba(0.25, 1, 1, 0, 1)
        lg.add_color_stop_rgba(0.5, 0, 1, 0, 1)
        lg.add_color_stop_rgba(0.75, 0, 1, 1, 1)
        lg.add_color_stop_rgba(1.0, 0, 0, 1, 1)
        cr.rectangle(self.screenx - 15, self.screeny - 125, 10, 100)
        cr.set_source_rgb(0, 0, 0)
        cr.set_line_width(1)
        cr.stroke_preserve()
        cr.set_source(lg)
        cr.fill()
        zmin = round(self.zmin / 1000.0,1)
        zmax = round(self.zmax / 1000.0,1)
        (txtx, txty, txtwidth, txtheight, txtdx, txtdy) = cr.text_extents(str(zmax))
        cr.move_to(self.screenx -5 -txtwidth, self.screeny - 130)
        cr.show_text(str(zmax))
        (txtx, txty, txtwidth, txtheight, txtdx, txtdy) = cr.text_extents(str(zmin))
        cr.move_to(self.screenx -5 -txtwidth, self.screeny - 15)
        cr.show_text(str(zmin))
        cr.new_path()
        pass
    def onNewPos(self):
        #threading.Thread(target=self.drawingarea.queue_draw).start()
        #self.drawingarea.queue_draw()
        #GObject.idle_add(self.drawingarea.queue_draw)
        pass
    def onRedraw(self):
        self.drawingarea.queue_draw()
        return True 

