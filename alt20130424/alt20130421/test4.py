#!/usr/bin/env python
import gtk
import math
import random

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
        mindim = min (width, height)/1.0
        print mindim
        size = mindim * self.zoom
        cr.scale (size,size)
        width  = width/size
        height = height/size
        print width
        onepixel = 1.0 / size
        
        
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
        
        # Draw the box
        cr.set_line_width (onepixel)
        cr.set_source_rgb(1, 1, 0)
        cr.move_to ((width-1.0)/2.0  + dx, (height-1.0)/2.0 + dy) 
        cr.rel_line_to (0,1)
        cr.rel_line_to (1,0)
        cr.rel_line_to (0,-1)
        cr.rel_line_to (-1,0)
        cr.stroke()


        cr.set_source_rgb(1, 0, 0)
        cr.arc(200 / size / self.zoom + dx, 100 / size / self.zoom + dy, 0.08, 0, 0.01 * 2 * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()

        cr.set_line_width(4.0/size)
        cr.set_source_rgb(1, 0, 0)
        cr.arc((width-1.0)/2.0 + dx, (height-1.0)/2.0 + dy, 8.0/width/size, 0, 2.0/width/size * math.pi)
        cr.stroke_preserve()
        cr.set_source_rgb(1, 1, 1)
        cr.fill()


def main():
    window = gtk.Window()
    window.set_default_size (512,512)
    grid = Grid ()
    window.add(grid)
    window.connect("destroy", gtk.main_quit)
    window.show_all()
    gtk.main()

if __name__ == "__main__":
    main()
