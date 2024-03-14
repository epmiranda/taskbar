#!/bin/python3

import sys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
from gi.repository import GLib, Gtk, Gdk, Wnck

settings = Gtk.Settings.get_default()
settings.set_property("gtk-application-prefer-dark-theme", True)

class Window(Gtk.ApplicationWindow):
    def __init__(self, application):
        super().__init__()

        self.screen = Wnck.Screen.get_default()

        self.set_application(application)
        self.set_title("Taskbar")
        self.set_default_icon_name("cs-panel")
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_default_size(self.screen.get_width(), 0)
        self.connect("size-allocate", self.on_size_allocate)

        start = Gtk.Button.new_from_icon_name("distributor-logo-archlinux", Gtk.IconSize.BUTTON)
        start.set_label(" Start")
        start.set_always_show_image(True)
        start.set_relief(Gtk.ReliefStyle.NONE)

        tasklist = Wnck.Tasklist.new()

        self.clock = Gtk.Button.new_with_label("00:00")
        self.clock.set_relief(Gtk.ReliefStyle.NONE)
        GLib.timeout_add_seconds(1, self.update_clock)

        desktop = Gtk.Button.new_from_icon_name("desktop", Gtk.IconSize.BUTTON)
        desktop.set_relief(Gtk.ReliefStyle.NONE)
        desktop.connect("clicked", self.on_desktop_clicked)

        box = Gtk.Box()
        box.set_orientation(Gtk.Orientation.HORIZONTAL)
        box.pack_start(start, False, False, 0)
        box.pack_start(tasklist, False, False, 0)
        box.pack_end(desktop, False, False, 0)
        box.pack_end(self.clock, False, False, 0)
        self.add(box)

    def on_size_allocate(self, window, allocation):
        self.move(0, self.screen.get_height() - self.get_size().height)

    def update_clock(self):
        time = GLib.DateTime.new_now_local()
        self.clock.set_label(time.format("%R"))
        self.clock.set_tooltip_text(time.format("%c"))
        return True

    def on_desktop_clicked(self, button):
        self.screen.toggle_showing_desktop(True)

class Application(Gtk.Application):
    def __init__(self, *args, **kwargs):
        Gtk.Application.__init__(self)
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = Window(application = self)
        self.window.show_all()

    def do_startup(self):
        Gtk.Application.do_startup(self)

application = Application()
application.run(sys.argv)