#!/usr/bin/env python3
from gi.repository import Gtk,Gdk, GLib

class TeamX():
    def __init__(self):
        print("TeamX")
    def run():
        print(1)


def main():
    builder = Gtk.Builder()
    builder.add_from_file("/home/alex/ips/glade_gui/init.glade")
    handlers = {
        "onDeleteWindow": Gtk.main_quit,
        "on_window1_destroy": Gtk.main_quit,
        "onButtonPressed": print("obp")
    }
    builder.connect_signals(handlers)
    window = builder.get_object("window1")
    window.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
