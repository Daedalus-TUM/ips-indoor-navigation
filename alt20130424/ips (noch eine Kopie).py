#!/usr/bin/python
from gi.repository import Gtk,GObject,Gdk
from collections import namedtuple
import gtk
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
        multilat.wrapperx.restype=c_double
        multilat.wrappery.restype=c_double
        multilat.wrapperz.restype=c_double

        x = multilat.wrapperx(cstations, cstartpos, cradii, cnn)
        y = multilat.wrappery(cstations, cstartpos, cradii, cnn)
        z = multilat.wrapperz(cstations, cstartpos, cradii, cnn)

        posx = x
        posy = y
        posz = z

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
        stationnr = int(tmp.group(1))
        millis = int(round(time.time() * 1000))
        stations[stationnr][3] = deltat
        stations[stationnr][4] = millis

  def reset(self):
    self.s.setDTR(False)
    time.sleep(0.00001)
    self.s.setDTR(True)


class Grid (gtk.DrawingArea):

    zoom     = 1
    position = (0,0)
    _drag_to = (0,0)

    def __init__(self):
        gtk.DrawingArea.__init__(self)
        self.set_events(gtk.gdk.EXPOSURE_MASK
                        | gtk.gdk.LEAVE_NOTIFY_MASK
                        | gtk.gdk.BUTTON_PRESS_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.BUTTON_RELEASE_MASK
                        | gtk.gdk.SCROLL_MASK
                        | gtk.gdk.POINTER_MOTION_MASK
                        | gtk.gdk.POINTER_MOTION_HINT_MASK)
        self.connect ("expose-event",         self.expose)
        self.connect ("button-press-event",   self.button_press)
        self.connect ("scroll-event",         self.scroll)
        self.connect ("button-release-event", self.button_release)
        self.connect ("motion-notify-event",  self.motion)

    def expose (self, widget, event):
        self.context = widget.window.cairo_create()
        self.context.rectangle (event.area.x, event.area.y,
                                event.area.width, event.area.height)
        self.context.clip()
        self.draw ()
        return False

    def button_press (self, widget, event):
        if event.button == 1:
            window = widget.get_parent_window()
            window.set_cursor (gtk.gdk.Cursor(gtk.gdk.FLEUR))
            self.drag_start (event.x, event.y)
            
    def scroll (self, widget, event):
        if event.direction == gtk.gdk.SCROLL_UP:
            self.zoom_in()
        elif event.direction == gtk.gdk.SCROLL_DOWN:
            self.zoom_out()
        self.queue_draw()

    def button_release (self, widget, event):
        window = widget.get_parent_window()
        window.set_cursor (gtk.gdk.Cursor(gtk.gdk.TOP_LEFT_ARROW))
        self.drag_end ()

    def motion (self, widget, event):
        if event.is_hint:
            x, y, state = event.window.get_pointer()
        else:
            x = event.x
            y = event.y
            state = event.state
        if state & gtk.gdk.BUTTON1_MASK:
            self.drag_to (x,y)
            self.queue_draw()

    def zoom_in (self):
        self.zoom = self.zoom * 1.1

    def zoom_out (self):
        self.zoom = self.zoom / 1.1

    def drag_start (self, x, y):
        self._drag_start = x,y

    def drag_to (self, x, y):
        dx = x - self._drag_start[0]
        dy = y - self._drag_start[1]
        self._drag_to = dx,dy

    def drag_end (self):
        self._drag_to = 0,0
        self.position = (self.position[0]+self._translated_drag_to[0], 
                         self.position[1]+self._translated_drag_to[1])

    def draw (self):
        
        cr = self.context
        x, y, width, height = self.get_allocation()

        # Set a normalized and undeformed scale
        size = min (width, height)/1.0
        print size
        size *= self.zoom
        cr.scale (size,size)
        width  = width/size
        height = height/size
        print width
        
        # White background
        cr.set_source_rgb (1.0, 1.0, 1.0)
        cr.rectangle (0, 0, width, height)
        cr.fill()
        
        cr.set_source_rgb (0, 0, 0)
        # cr.set_line_width (max (cr.device_to_user_distance (1,1)))
        cr.set_line_width (.001)

        # Compute current move in user_distance
        dx,dy = self._drag_to
        self._translated_drag_to = cr.device_to_user_distance (dx,dy)
        dx,dy = self._translated_drag_to
        dx += self.position[0]
        dy += self.position[1]

        # Draw the box
        cr.move_to ((width-1.0)/2.0  + dx, (height-1.0)/2.0 + dy) 
        cr.rel_line_to (0,1)
        cr.rel_line_to (1,0)
        cr.rel_line_to (0,-1)
        cr.rel_line_to (-1,0)
        cr.stroke()

        cr.move_to ((width-1.0)/2.0  + dx, (height-1.0)/2.0 + dy) 
        cr.rel_line_to (0,0.6)
        cr.rel_line_to (0.6,0.4)
        cr.rel_line_to (0,-1)
        cr.rel_line_to (-1,0)
        cr.stroke()

        
        cr.set_line_width(4.0/size)
        cr.set_source_rgb(1, 0, 0)
        cr.arc((width-1.0)/2.0 + dx, (height-1.0)/2.0 + dy, 8.0/width/size, 0, 2.0/width/size * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()


def main():
    arduino = arduino()
    while 1:
      if (arduino.s.inWaiting() > 0):
          arduino.recv_packet() 
          clib_multilat()

    GObject.threads_init() # init threads?
    window = gtk.Window()
    window.set_default_size (512,512)
    grid = Grid ()
    window.add(grid)
    window.connect("destroy", gtk.main_quit())
    window.show_all()
    gtk.main()

if __name__ == "__main__":
    main()
