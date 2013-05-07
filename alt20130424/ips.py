#!/usr/bin/python
from gi.repository import Gtk,GObject,Gdk
from collections import namedtuple
import math
import serial
import pickle
import glob
import time
import re
from ctypes import *

#multilat=CDLL('/home/ga34yoz/ips/multilat.so')
#multilat=CDLL('/home/alex/ips20130405/ips/multilat.so')
multilat=CDLL('/home/alex/ips/multilat.so')

stations = [[0 for col in range(5)] for row in range(10)]

stations[0][0] = 0
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
stations[5][2] = 0

posx = 0.0
posy = 0.0
posz = 1000.0


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

        x = c_double
        y = c_double
        z = c_double
        deltar = c_double
        multilat.wrapper.restype=c_double
        

        deltar = multilat.wrapper(cstations, cstartpos, cradii, cnn, byref(x), byref(y), byref(z))

        posx = x.value
        posy = y
        posz = z
        print posx, posy, posz

class ttyWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="daedalus Indor Possitioning System - Select serial Port")
        self.box = Gtk.Box(spacing=6)
        self.add(self.box)
        

class arduino:
  def __init__(self):
    ttydevs = glob.glob('/dev/ttyUSB*') + glob.glob('/dev/ttyACM*')# + glob.glob('/dev/ttyS*')
    if len(ttydevs) == 0:
      print "error: no tty Port"
    elif len(ttydevs) == 1:
      self.ttyport = ttydevs[0]
    else:
      self.ttywin = ttyWindow()
      for item in ttydevs:
        self.ttywin.button = Gtk.Button(label=item)
        self.ttywin.button.connect("clicked", self.setttydev, item)
        self.ttywin.box.pack_start(self.ttywin.button, True, True, 0)
      self.ttywin.connect("delete-event", Gtk.main_quit)
      self.ttywin.show_all()
      Gtk.main()
    self.s = serial.Serial(self.ttyport, 115200, 8, 'N', 1, 0.05)
    self.s.flush()
    self.pattern = re.compile(r"deltat from (\d+) - (\d+) - (\d+\.\d+)")
  def setttydev(self, button, dev):
    self.ttyport = dev
    print self.ttyport
    self.ttywin.destroy()
    Gtk.main_quit()
  def setled(self, led, state):
    self.s.write("\x02" + led + chr(state) + "\x03")
    self.s.flush()
    self.recv_packet()
  def recv_packet(self):
    if (self.s.inWaiting() > 0):
      res = self.s.readline()
      print res
      tmp = self.pattern.search(res)
      if tmp is not None:
        deltat = float(tmp.group(2))
        deltat = deltat * 0.34
        if deltat > 1:
            stationnr = int(tmp.group(1))
            millis = int(round(time.time() * 1000))
            stations[stationnr][3] = deltat
            stations[stationnr][4] = millis

  def reset(self):
    self.s.setDTR(False)
    time.sleep(0.00001)
    self.s.setDTR(True)




arduino = arduino()
while 1:
  if (arduino.s.inWaiting() > 0):
      arduino.recv_packet() 
      clib_multilat()


