#!/bin/python3

import os

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Wnck', '3.0')
gi.require_version('GMenu', '3.0')
from gi.repository import GLib, Gio, Gtk, Gdk, GdkX11, Wnck, GMenu

from Xlib import Xatom, display

settings = Gtk.Settings.get_default()
settings.set_property("gtk-application-prefer-dark-theme", True)

class Window(Gtk.ApplicationWindow):
	def __init__(self, application):
		super().__init__()

		self.application = application

		self.get_style_context().add_class("panel")

		self.display = display.Display()
		self.screen = Wnck.Screen.get_default()

		self.set_application(application)
		self.set_title("Taskbar")
		self.set_default_icon_name("cs-panel")
		self.set_type_hint(Gdk.WindowTypeHint.DOCK)
		self.set_default_size(self.screen.get_width(), 0)
		self.connect("size-allocate", self.on_size_allocate)

		# Start Menu
		self.menu_model = Gio.Menu()

		# Start
		# start = Gtk.MenuButton.new_from_icon_name("distributor-logo-archlinux", Gtk.IconSize.BUTTON)
		start = Gtk.MenuButton.new()
		start.set_image(Gtk.Image.new_from_icon_name("start-here", Gtk.IconSize.LARGE_TOOLBAR))
		start.set_always_show_image(True)
		start.set_tooltip_text("Start")
		start.set_use_popover(False)
		start.set_menu_model(self.menu_model)

		launch_action = Gio.SimpleAction.new("launch", GLib.VariantType.new("s"))
		launch_action.connect("activate", self.launch)
		self.add_action(launch_action)
		
		# GNOME Menu
		self.gmenu_tree = GMenu.Tree.new(os.environ.get("XDG_MENU_PREFIX", "") + "applications.menu", 0)
		self.gmenu_tree.connect("changed", self.on_menu_changed)
		self.load_menu()
		
		# WNCK Tasklist
		tasklist = Wnck.Tasklist.new()

		# WNCK Pager
		pager = Wnck.Pager.new()

		# Calendar
		calendar_window = Gtk.Window.new(Gtk.WindowType.TOPLEVEL)
		calendar_window.set_type_hint(Gdk.WindowTypeHint.UTILITY)
		calendar_window.set_decorated(False)
		calendar_window.add_events(Gdk.EventMask.FOCUS_CHANGE_MASK)
		calendar_window.connect("focus-out-event", self.on_calendar_focus_out)
		calendar_box = Gtk.Box.new(Gtk.Orientation.VERTICAL, 0)
		calendar_box.pack_start(Gtk.Calendar.new(), False, False, 0)
		calendar_window.add(calendar_box)
		calendar_window.move(self.screen.get_width(), self.screen.get_height())

		# Clock
		self.clock = Gtk.ToggleButton.new()
		self.clock.connect("toggled", self.on_clock_toggled, calendar_window)
		GLib.timeout_add_seconds(1, self.update_clock)

		# Desktop
		desktop = Gtk.Button.new_from_icon_name("desktop", Gtk.IconSize.BUTTON)
		desktop.set_tooltip_text("Show desktop")
		desktop.connect("clicked", self.on_desktop_clicked)

		box = Gtk.Box.new(Gtk.Orientation.HORIZONTAL, 2)
		box.pack_start(start, False, False, 0)
		box.pack_start(tasklist, False, False, 0)
		box.pack_end(desktop, False, False, 0)
		box.pack_end(self.clock, False, False, 0)
		# box.pack_end(pager, False, False, 0)
		self.add(box)

	def on_size_allocate(self, window, allocation):
		size = self.get_size()
		self.move(0, self.screen.get_height() - size.height)
		
		if(not self.get_toplevel().get_window()):
			return
		
		root = self.display.create_resource_object('window', self.get_toplevel().get_window().get_xid())
		# root.change_property(self.display.intern_atom('_NET_WM_STRUT'), Xatom.CARDINAL, 32, [0, 0, 0, 32])
		root.change_property(self.display.intern_atom('_NET_WM_STRUT_PARTIAL'), Xatom.CARDINAL, 32, [0, 0, 0, size.height, 0, 0, 0, 0, 0, 0, 0, size.width])

	def on_calendar_focus_out(self, widget: Gtk.Widget, event: Gdk.EventFocus):
		self.clock.set_active(False)

	def on_clock_toggled(self, button: Gtk.ToggleButton, window: Gtk.Window):
		if button.get_active():
			window.show_all()
			window.present()
		else:
			window.hide()
		
	def launch(self, action, parameter):
		print(parameter)
		entry = self.gmenu_tree.get_entry_by_id(parameter.get_string())
		entry.get_app_info().launch(None, None)
		
	def load_directory(self, directory, menu):		
		item_iter = directory.iter()
		item_type = item_iter.next()
		
		# TODO: separators, directory icons
		while item_type != GMenu.TreeItemType.INVALID:
			if item_type == GMenu.TreeItemType.DIRECTORY:
				new_directory = item_iter.get_directory()
				directory_menu_model = Gio.Menu()
				directory_item = Gio.MenuItem.new_submenu(new_directory.get_name(), directory_menu_model)
				directory_icon = new_directory.get_icon()
				if directory_icon != None:
					directory_item.set_icon(directory_icon)
				menu.append_item(directory_item)
				self.load_directory(new_directory, directory_menu_model)
			elif item_type == GMenu.TreeItemType.ENTRY:
				entry = item_iter.get_entry()
				app_info = entry.get_app_info()
				name = app_info.get_display_name()
				
				item = Gio.MenuItem.new(name, None)
				item.set_icon(app_info.get_icon())
				item.set_action_and_target_value("win.launch", GLib.Variant.new_string(entry.get_desktop_file_id()))
				menu.append_item(item)
				
			item_type = item_iter.next()
		
	def load_menu(self):
		self.menu_model.remove_all()

		if not self.gmenu_tree.load_sync():
			print("ERROR: Could not load GMenu tree")
			
		self.load_directory(self.gmenu_tree.get_root_directory(), self.menu_model)
		
	def on_menu_changed(self, tree):
		self.load_menu()

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