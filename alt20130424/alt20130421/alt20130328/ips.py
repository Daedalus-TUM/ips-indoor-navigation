#!/usr/bin/python
from gi.repository import Gtk
from collections import namedtuple
import math
import serial
import pickle
import glob
import time
import re


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
        
        deltat = tmp.group(2)
        station = tmp.group(1)
	millis = int(round(time.time() * 1000))
        print deltat
        print station
  def reset(self):
    self.s.setDTR(False)
    time.sleep(0.00001)
    self.s.setDTR(True)

arduino = arduino()
while 1:
  if (arduino.s.inWaiting() > 0):
      arduino.recv_packet() 
      
