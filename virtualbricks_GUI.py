#!/usr/bin/python
import os
import sys
import gtk
import gtk.glade
import virtualbricks_Global as Global
import virtualbricks_BrickFactory as BrickFactory
import gobject
import time

class VBGUI:
	def __init__(self):
		if not os.access(Global.MYPATH, os.X_OK):
			os.mkdir(Global.MYPATH)

		gtk.gdk.threads_init()
		self.brickfactory = BrickFactory.BrickFactory(True)
		self.brickfactory.start()
		try:
			self.gladefile = gtk.glade.XML('./virtualbricks.glade')
		except:
			print "Cannot open required file 'virtualbricks.glade'"
			sys.exit(1)
		self.widg = self.get_widgets(self.widgetnames())
		self.widg['main_win'].show()
		self.ps = []
		self.bricks = []
		self.signals()
		self.timers()
		self.set_nonsensitivegroup(['cfg_Wirefilter_lossburst_text', 'cfg_Wirefilter_mtu_text'])
		self.running_bricks = self.treestore('treeview_joblist', 
			[gobject.TYPE_STRING, gobject.TYPE_STRING, gobject.TYPE_STRING], 
			['PID','Type','Name'])
		self.bookmarks = self.treestore('treeview_bookmarks', 
				[gtk.gdk.Pixbuf, 
				 gobject.TYPE_STRING, 
				 gobject.TYPE_STRING, 
				 gobject.TYPE_STRING], 
				['Status','Type','Name', 'Parameters'])
		
		self.curtain = self.gladefile.get_widget('vpaned_mainwindow')
		self.Dragging = None
		self.curtain_down()
		
		self.selected = None
		self.joblist_selected = None
		

		try:
			gtk.main()
		except KeyboardInterrupt:
			self.quit()



	""" ******************************************************** """
	"""                                                          """
	""" BRICK CONFIGURATION                                      """
	"""                                                          """
	"""                                                          """
	""" ******************************************************** """
	
	def config_brick_prepare(self):
		# Fill socks combobox
		b = self.selected
		for k in self.sockscombo():
			w = self.gladefile.get_widget(k)
        		model = w.get_model()
        		w.set_model(None)
        		model.clear()
        		w.set_model(model)
			for so in self.brickfactory.socks:
				w.append_text(so.nickname)
			t = b.get_type()
			active = 0
			idx = 0
			if (not t.startswith('Wire')) or k.endswith('0'):
				if len(b.plugs) >= 1 and b.plugs[0].sock:
					model = w.get_model()
					i = model.get_iter_first()
					while i is not None:
						s = model.get_value(i, 0)
                				if s == b.plugs[0].sock.nickname:
							active = idx
						i = model.iter_next(i)
						idx += 1
						
        				w.set_active(active)

			elif k.endswith('1') and t.startswith('Wire'):
				if len(b.plugs) > 1 and b.plugs[1].sock: 
					model = w.get_model()
					i = model.get_iter_first()
					while i is not None:
						s = model.get_value(i, 0)
                				if s == b.plugs[1].sock.nickname:
							active = idx
						i = model.iter_next(i)
						idx += 1
						
        				w.set_active(active)

		for key in b.cfg.__dict__.keys():
			t = b.get_type()
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "text")
			if (widget is not None):
				widget.set_text(b.cfg.__dict__[key])
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "spinint")
			if (widget is not None):
				widget.set_value(int(b.cfg.__dict__[key]))
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "spinfloat")
			if (widget is not None):
				widget.set_value(float(b.cfg.__dict__[key]))
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "check")
			if (widget is not None):
				if (b.cfg.__dict__[key] == "*"):
					widget.set_active(True)
				else:
					widget.set_active(False)
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "comboinitial")
			if (widget is not None):
				#TODO combobox selection for units and distribution
				print
			

	def config_brick_confirm(self):
		b = self.selected
		for key in b.cfg.__dict__.keys():
			t = b.get_type()
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "text")
			if (widget is not None):
				b.cfg.set(key+"="+widget.get_text())
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "spinint")
			if (widget is not None):
				b.cfg.set(key+"="+str(int(widget.get_value())))
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "spinfloat")
			if (widget is not None):
				b.cfg.set(key+"="+str(widget.get_value()))
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "comboinitial")
			if (widget is not None):
				txt = widget.get_active_text()
				if (txt):
					b.cfg.set(key+"="+txt[0])
			
			widget = self.gladefile.get_widget("cfg_" + t + "_" + key + "_" + "check")
			if (widget is not None):
				if widget.get_active():
					b.cfg.set(key+'=*')
			b.gui_changed = True
		self.curtain_down()
		

	def config_brick_cancel(self):
		self.curtain_down()

	
	""" ******************************************************** """
	"""                                                          """
	""" MISC / WINDOWS BEHAVIOR                                  """
	"""                                                          """
	"""                                                          """
	""" ******************************************************** """

	def curtain_is_down(self):
		print self.curtain.get_position()
		return (self.curtain.get_position()>660)

	def curtain_down(self):
		print "Old position: %d" % self.curtain.get_position()
		self.curtain.set_position(99999)
		self.gladefile.get_widget('label_showhidesettings').set_text('Show Settings')

	def curtain_up(self):
		print "Old position: %d" % self.curtain.get_position()
		self.gladefile.get_widget('box_vmconfig').hide()
		self.gladefile.get_widget('box_tapconfig').hide()
		self.gladefile.get_widget('box_tunnellconfig').hide()
		self.gladefile.get_widget('box_tunnelcconfig').hide()
		self.gladefile.get_widget('box_wireconfig').hide()
		self.gladefile.get_widget('box_wirefilterconfig').hide()
		self.gladefile.get_widget('box_switchconfig').hide()
		
		if self.selected is None:
			return  
		
		wg = self.curtain
		if self.selected.get_type() == 'Switch':
			print "switch config"
			ww = self.gladefile.get_widget('box_switchconfig')
			wg.set_position(589)	
		
		elif self.selected.get_type() == 'Qemu':
			print "qemu config"
			ww = self.gladefile.get_widget('box_vmconfig')
			wg.set_position(245)

		
		elif self.selected.get_type() == 'Tap':
			print "tap config"
			ww = self.gladefile.get_widget('box_tapconfig')
			wg.set_position(606)	
			
		elif self.selected.get_type() == 'Wire':
			print "wire config"
			ww = self.gladefile.get_widget('box_wireconfig')
			wg.set_position(606)	
		elif self.selected.get_type() == 'Wirefilter':
			print "wirefilter config"
			ww = self.gladefile.get_widget('box_wirefilterconfig')
			wg.set_position(424)	
		elif self.selected.get_type() == 'TunnelConnect':
			print "tunnelc config"
			ww = self.gladefile.get_widget('box_tunnelcconfig')
			wg.set_position(424)	
		elif self.selected.get_type() == 'TunnelListen':
			print "tunnell config"
			ww = self.gladefile.get_widget('box_tunnellconfig')
			wg.set_position(424)	
		self.config_brick_prepare()
		ww.show_all()

		self.gladefile.get_widget('label_showhidesettings').set_text('Hide Settings')
		
	def get_treeselected(self, tree, store, pthinfo, c):

		if pthinfo is not None:
			path, col, cellx, celly = pthinfo
			tree.grab_focus()
			tree.set_cursor(path, col, 0)
			iter = self.bookmarks.get_iter(path)
			name = self.bookmarks.get_value(iter, c)
			self.config_last_iter = iter
			return name
		return ""

	def get_treeselected_name(self, t, s, p):
		return self.get_treeselected(t, s, p, 2)
	
	def get_treeselected_type(self, t, s, p):
		return self.get_treeselected(t, s, p, 1)
		

	def quit(self):
		print
		print "GUI: Goodbye!"
		self.brickfactory.quit()
		sys.exit(0)


	def get_widgets(self, l):
		r = dict()
		for i in l:	
			r[i] =  self.gladefile.get_widget(i)
			r[i].hide()
		return r

	def treestore(self, tree_name, fields,names):
		tree = self.gladefile.get_widget(tree_name)
		ret = gtk.TreeStore(*fields)
		tree.set_model(ret)
		for idx, name in enumerate(names):
			col = gtk.TreeViewColumn(name)
			if fields[idx] == gtk.gdk.Pixbuf:
				elem = gtk.CellRendererPixbuf()
				col.pack_start(elem, False)
				col.add_attribute(elem, 'pixbuf', idx)
			else:
				elem = gtk.CellRendererText()
				col.pack_start(elem, False)
				col.add_attribute(elem, 'text', idx)
			tree.append_column(col)
		return ret
		

	def widgetnames(self):
		return ['main_win', 
		'filechooserdialog_openimage', 
		'dialog_settings', 
		'dialog_bookmarks', 
		'menu_popup_bookmarks', 
		'dialog_about1',
		'dialog_create_image',
		'dialog_messages', 
		'menu_popup_imagelist', 
		'dialog_jobmonitor', 
		'menu_popup_joblist', 
		'menu_popup_usbhost',
		'menu_popup_usbguest', 
		'menu_popup_volumes',
		'dialog_newnetcard',
		'dialog_confirm_action',
		'dialog_new_redirect',
		'ifconfig_win', 
		'dialog_newbrick',
		'menu_brickactions',
		'dialog_warn'
		]
	def sockscombo(self):
		return [
		'sockscombo_vmethernet',
		'sockscombo_tap',
		'sockscombo_wire0',
		'sockscombo_wire1',
		'sockscombo_wirefilter0',
		'sockscombo_wirefilter1',
		'sockscombo_tunnell',
		'sockscombo_tunnelc'
		]
	def show_window(self, name):
		for w in self.widg.keys():
			if name == w or w == 'main_win':
				if w.startswith('menu'):
					self.widg[w].popup(None,None,None, 3, 0)
				else:
					self.widg[w].show_all()
			elif not name.startswith('menu'):
				self.widg[w].hide()
	
	""" ******************************************************** """
	"""                                                          """
	""" EVENTS / SIGNALS                                         """
	"""                                                          """
	"""                                                          """
	""" ******************************************************** """
	def on_window1_destroy(self, widget=None, data=""):
		self.quit()
		pass
	def on_windown_destroy(self, widget=None, data=""):
		widget.hide()
		return True

	def error(self, text):
		self.gladefile.get_widget('texterror').set_text(text)
		self.show_window('dialog_warn')

	def on_error_close(self, widget=None, data =""):
		print "ERROR CLOSE"
		self.widg['dialog_warn'].hide()
		return True

	def on_newbrick_cancel(self, widget=None, data=""):
		self.show_window('')
		
	def on_newbrick_ok(self, widget=None, data=""):
		self.show_window('')
		name = self.gladefile.get_widget('text_newbrickname').get_text()
		ntype = self.gladefile.get_widget('combo_newbricktype').get_active_text()
		try:
			self.brickfactory.newbrick(ntype, name)
		except BrickFactory.InvalidNameException:
			self.error("Cannot create brick: Invalid name.")
		else:
			print "Created successfully"


	def on_config_cancel(self, widget=None, data=""):
		self.config_brick_cancel()
	def on_config_ok(self, widget=None, data=""):
		self.config_brick_confirm()

	def set_sensitivegroup(self,l):
		for i in l:
			w = self.gladefile.get_widget(i)
			w.set_sensitive(True)

	def set_nonsensitivegroup(self,l):
		for i in l:
			w = self.gladefile.get_widget(i)
			w.set_sensitive(False)

	def on_gilbert_toggle(self, widget=None, data=""):	
		if widget.get_active():
			self.gladefile.get_widget('cfg_Wirefilter_lossburst_text').set_sensitive(True)
			self.gladefile.get_widget('cfg_Wirefilter_lossburst_text').set_text("0")
		else:
			self.gladefile.get_widget('cfg_Wirefilter_lossburst_text').set_text("")
			self.gladefile.get_widget('cfg_Wirefilter_lossburst_text').set_sensitive(False)
		
	def on_mtu_toggle(self, widget=None, data=""):
		if widget.get_active():
			self.gladefile.get_widget('cfg_Wirefilter_mtu_text').set_sensitive(True)
			self.gladefile.get_widget('cfg_Wirefilter_mtu_text').set_text("1024")
		else:
			self.gladefile.get_widget('cfg_Wirefilter_mtu_text').set_text("")
			self.gladefile.get_widget('cfg_Wirefilter_mtu_text').set_sensitive(False)
 

	def on_item_quit_activate(self, widget=None, data=""):
		self.quit()
		pass
	def on_item_settings_activate(self, widget=None, data=""):
		self.show_window('dialog_settings')
		pass
	def on_item_settings_autoshow_activate(self, widget=None, data=""):
		print "on_item_settings_autoshow_activate undefined!"
		pass
	def on_item_settings_autohide_activate(self, widget=None, data=""):
		print "on_item_settings_autohide_activate undefined!"
		pass
	def on_item_create_image_activate(self, widget=None, data=""):
		print "on_item_create_image_activate undefined!"
		pass
	def on_item_about_activate(self, widget=None, data=""):
		self.show_window('dialog_about1')
		pass
	def on_toolbutton_launch_clicked(self, widget=None, data=""):
		print "on_toolbutton_launch_clicked undefined!"
		pass
	def on_toolbutton_launchxterm_clicked(self, widget=None, data=""):
		print "on_toolbutton_launchxterm_clicked undefined!"
		pass

	def on_toolbutton_launch_unmanaged_clicked(self, widget=None, data=""):
		print "on_toolbutton_launch_unmanaged_clicked undefined!"
		pass

	def on_vpaned_mainwindow_button_release_event(self, widget=None, event=None, data=""):
		tree = self.gladefile.get_widget('treeview_bookmarks');
		store = self.bookmarks
		x = int(event.x)
		y = int(event.y)
		time = event.time
		pthinfo = tree.get_path_at_pos(x, y)
		name = self.get_treeselected_name(tree, store, pthinfo)
		dropbrick = self.brickfactory.getbrickbyname(name)
		if (dropbrick != self.Dragging):
			print "drag&drop!"
			if (len(dropbrick.socks) > 0):
				self.Dragging.connect(dropbrick.socks[0])
			elif (len(self.Dragging.socks) > 0):
				dropbrick.connect(self.Dragging.socks[0])
			
		self.Dragging = None

	def on_treeview_bookmarks_button_press_event(self, widget=None, event=None, data=""):
		tree = self.gladefile.get_widget('treeview_bookmarks');
		store = self.bookmarks
		x = int(event.x)
		y = int(event.y)
		time = event.time
		pthinfo = tree.get_path_at_pos(x, y)
		name = self.get_treeselected_name(tree, store, pthinfo)
		self.Dragging = self.brickfactory.getbrickbyname(name)
		if event.button == 3:
			self.selected = self.brickfactory.getbrickbyname(name)
			if self.selected:
				self.show_window('menu_brickactions')
			
		
	def on_treeview_bookmarks_cursor_changed(self, widget=None, event=None, data=""):
		tree = self.gladefile.get_widget('treeview_bookmarks');
		store = self.bookmarks
		path, focus = tree.get_cursor()
                iter = store.get_iter(path)
                ntype = store.get_value(iter, 1)
                name = store.get_value(iter, 2)
		self.selected = self.brickfactory.getbrickbyname(name)
		self.curtain_down()
		
	def on_treeview_bookmarks_row_activated_event(self, widget=None, event=None , data=""):
		self.tree_startstop()

	def on_treeview_bookmarks_focus_out(self, widget=None, event=None , data=""):
		self.curtain_down()
		self.selected=None

	def tree_startstop(self, widget=None, event=None , data=""):
		tree = self.gladefile.get_widget('treeview_bookmarks');
		store = self.bookmarks
		path, focus = tree.get_cursor()
                iter = store.get_iter(path)
                ntype = store.get_value(iter, 1)
                name = store.get_value(iter, 2)
		print "Activating %s %s" % (ntype, name)
		b = self.brickfactory.getbrickbyname(name)
		if b.proc is not None:
			b.poweroff()
		else:
			try:
				b.poweron()
			except(BrickFactory.BadConfigException):
				b.gui_changed=True
				self.error("Cannot start this Brick: Brick not configured, yet.")
			except(BrickFactory.NotConnectedException):
				self.error("Cannot start this Brick: Brick not connected.")
			except(BrickFactory.LinkDownException):
				self.error("Cannot start this Brick: Link down.")
				pass
	def on_treeview_bootimages_button_press_event(self, widget=None, data=""):
		print "on_treeview_bootimages_button_press_event undefined!"
		pass
	def on_treeview_bootimages_cursor_changed(self, widget=None, data=""):
		print "on_treeview_bootimages_cursor_changed undefined!"
		pass
	def on_treeview_bootimages_row_activated_event(self, widget=None, data=""):
		print "on_treeview_bootimages_row_activated_event undefined!"
		pass
	def on_treeview_joblist_button_press_event(self, widget=None, event=None, data=""):
		print "Hello"
		tree = self.gladefile.get_widget('treeview_joblist');
		store = self.running_bricks
		x = int(event.x)
		y = int(event.y)
		time = event.time
		pthinfo = tree.get_path_at_pos(x, y)
		name = self.get_treeselected_name(tree, store, pthinfo)
		if event.button == 3:
			self.joblist_selected = self.brickfactory.getbrickbyname(name)
			if self.joblist_selected:
				self.show_window('menu_popup_joblist')
		pass
	def on_treeview_joblist_row_activated_event(self, widget=None, data=""):
		print "on_treeview_joblist_row_activated_event undefined!"
		pass
	def on_button_togglesettings_clicked(self, widget=None, data=""):
		if self.curtain_is_down():
			self.curtain_up()
			print "up"
		else:
			self.curtain_down()
			print "down"
	def on_filechooserdialog_openimage_response(self, widget=None, data=""):
		print "on_filechooserdialog_openimage_response undefined!"
		pass
	def on_button_openimage_cancel_clicked(self, widget=None, data=""):
		print "on_button_openimage_cancel_clicked undefined!"
		pass
	def on_button_openimage_open_clicked(self, widget=None, data=""):
		print "on_button_openimage_open_clicked undefined!"
		pass
	def on_dialog_settings_response(self, widget=None, data=""):
		print "on_dialog_settings_response undefined!"
		pass
	def on_treeview_cdromdrives_row_activated(self, widget=None, data=""):
		print "on_treeview_cdromdrives_row_activated undefined!"
		pass
	def on_button_settings_add_cdevice_clicked(self, widget=None, data=""):
		print "on_button_settings_add_cdevice_clicked undefined!"
		pass
	def on_button_settings_rem_cdevice_clicked(self, widget=None, data=""):
		print "on_button_settings_rem_cdevice_clicked undefined!"
		pass
	def on_treeview_qemupaths_row_activated(self, widget=None, data=""):
		print "on_treeview_qemupaths_row_activated undefined!"
		pass
	def on_button_settings_add_qemubin_clicked(self, widget=None, data=""):
		print "on_button_settings_add_qemubin_clicked undefined!"
		pass
	def on_button_settings_rem_qemubin_clicked(self, widget=None, data=""):
		print "on_button_settings_rem_qemubin_clicked undefined!"
		pass
	def on_dialog_bookmarks_response(self, widget=None, data=""):
		print "on_dialog_bookmarks_response undefined!"
		pass
	def on_edit_bookmark_activate(self, widget=None, data=""):
		print "on_edit_bookmark_activate undefined!"
		pass
	def on_bookmark_info_activate(self, widget=None, data=""):
		print "on_bookmark_info_activate undefined!"
		pass
	def on_delete_bookmark_activate(self, widget=None, data=""):
		print "on_delete_bookmark_activate undefined!"
		pass
	def on_dialog_about_response(self, widget=None, data=""):
		self.widg['dialog_about1'].hide()
		return True
	def on_dialog_create_image_response(self, widget=None, data=""):
		print "on_dialog_create_image_response undefined!"
		pass
	def on_filechooserbutton_newimage_dest_selection_changed(self, widget=None, data=""):
		print "on_filechooserbutton_newimage_dest_selection_changed undefined!"
		pass
	def on_filechooserbutton_newimage_dest_current_folder_changed(self, widget=None, data=""):
		print "on_filechooserbutton_newimage_dest_current_folder_changed undefined!"
		pass
	def on_entry_newimage_name_changed(self, widget=None, data=""):
		print "on_entry_newimage_name_changed undefined!"
		pass
	def on_combobox_newimage_format_changed(self, widget=None, data=""):
		print "on_combobox_newimage_format_changed undefined!"
		pass
	def on_spinbutton_newimage_size_changed(self, widget=None, data=""):
		print "on_spinbutton_newimage_size_changed undefined!"
		pass
	def on_combobox_newimage_sizeunit_changed(self, widget=None, data=""):
		print "on_combobox_newimage_sizeunit_changed undefined!"
		pass
	def on_button_create_image_clicked(self, widget=None, data=""):
		print "on_button_create_image_clicked undefined!"
		pass
	def on_dialog_messages_response(self, widget=None, data=""):
		print "on_dialog_messages_response undefined!"
		pass
	def on_item_info_activate(self, widget=None, data=""):
		print "on_item_info_activate undefined!"
		pass
	def on_item_bookmark_activate(self, widget=None, data=""):
		print "on_item_bookmark_activate undefined!"
		pass
	def on_dialog_jobmonitor_response(self, widget=None, data=""):
		print "on_dialog_jobmonitor_response undefined!"
		pass
	def on_toolbutton_stop_job_clicked(self, widget=None, data=""):
		print "on_toolbutton_stop_job_clicked undefined!"
		pass
	def on_toolbutton_reset_job_clicked(self, widget=None, data=""):
		print "on_toolbutton_reset_job_clicked undefined!"
		pass
	def on_toolbutton_pause_job_clicked(self, widget=None, data=""):
		print "on_toolbutton_pause_job_clicked undefined!"
		pass
	def on_toolbutton_rerun_job_clicked(self, widget=None, data=""):
		print "on_toolbutton_rerun_job_clicked undefined!"
		pass
	def on_treeview_jobmon_volumes_button_press_event(self, widget=None, data=""):
		print "on_treeview_jobmon_volumes_button_press_event undefined!"
		pass
	def on_treeview_jobmon_volumes_row_activated(self, widget=None, data=""):
		print "on_treeview_jobmon_volumes_row_activated undefined!"
		pass
	def on_button_jobmon_apply_cdrom_clicked(self, widget=None, data=""):
		print "on_button_jobmon_apply_cdrom_clicked undefined!"
		pass
	def on_button_jobmon_apply_fda_clicked(self, widget=None, data=""):
		print "on_button_jobmon_apply_fda_clicked undefined!"
		pass
	def on_button_jobmon_apply_fdb_clicked(self, widget=None, data=""):
		print "on_button_jobmon_apply_fdb_clicked undefined!"
		pass
	def on_combobox_jobmon_cdrom_changed(self, widget=None, data=""):
		print "on_combobox_jobmon_cdrom_changed undefined!"
		pass
	def on_combobox_jobmon_fda_changed(self, widget=None, data=""):
		print "on_combobox_jobmon_fda_changed undefined!"
		pass
	def on_combobox_jobmon_fdb_changed(self, widget=None, data=""):
		print "on_combobox_jobmon_fdb_changed undefined!"
		pass
	def on_treeview_usbhost_button_press_event(self, widget=None, data=""):
		print "on_treeview_usbhost_button_press_event undefined!"
		pass
	def on_treeview_usbhost_row_activated(self, widget=None, data=""):
		print "on_treeview_usbhost_row_activated undefined!"
		pass
	def on_treeview_usbguest_button_press_event(self, widget=None, data=""):
		print "on_treeview_usbguest_button_press_event undefined!"
		pass
	def on_treeview_usbguest_row_activated(self, widget=None, data=""):
		print "on_treeview_usbguest_row_activated undefined!"
		pass
	def on_item_jobmonoitor_activate(self, widget=None, data=""):
		print "on_item_jobmonoitor_activate undefined!"
		pass
	def on_item_stop_job_activate(self, widget=None, data=""):
		print "on_item_stop_job_activate undefined!"
		pass
	def on_item_cont_job_activate(self, widget=None, data=""):
		print "on_item_cont_job_activate undefined!"
		pass
	def on_item_reset_job_activate(self, widget=None, data=""):
		print "on_item_reset_job_activate undefined!"
		pass
	def on_item_kill_job_activate(self, widget=None, data=""):
		print "on_item_kill_job_activate undefined!"
		pass
	def on_attach_device_activate(self, widget=None, data=""):
		print "on_attach_device_activate undefined!"
		pass
	def on_detach_device_activate(self, widget=None, data=""):
		print "on_detach_device_activate undefined!"
		pass
	def on_item_eject_activate(self, widget=None, data=""):
		print "on_item_eject_activate undefined!"
		pass
	def on_dialog_newnetcard_response(self, widget=None, data=""):
		print "on_dialog_newnetcard_response undefined!"
		pass
	def on_combobox_networktype_changed(self, widget=None, data=""):
		print "on_combobox_networktype_changed undefined!"
		pass
	def on_entry_network_macaddr_changed(self, widget=None, data=""):
		print "on_entry_network_macaddr_changed undefined!"
		pass
	def on_entry_network_ip_changed(self, widget=None, data=""):
		print "on_entry_network_ip_changed undefined!"
		pass
	def on_spinbutton_network_port_changed(self, widget=None, data=""):
		print "on_spinbutton_network_port_changed undefined!"
		pass
	def on_spinbutton_network_vlan_changed(self, widget=None, data=""):
		print "on_spinbutton_network_vlan_changed undefined!"
		pass
	def on_entry_network_ifacename_changed(self, widget=None, data=""):
		print "on_entry_network_ifacename_changed undefined!"
		pass
	def on_entry_network_tuntapscript_changed(self, widget=None, data=""):
		print "on_entry_network_tuntapscript_changed undefined!"
		pass
	def on_button__network_open_tuntap_file_clicked(self, widget=None, data=""):
		print "on_button__network_open_tuntap_file_clicked undefined!"
		pass
	def on_spinbutton_network_filedescriptor_changed(self, widget=None, data=""):
		print "on_spinbutton_network_filedescriptor_changed undefined!"
		pass
	def on_dialog_new_redirect_response(self, widget=None, data=""):
		print "on_dialog_new_redirect_response undefined!"
		pass
	def on_radiobutton_redirect_TCP_toggled(self, widget=None, data=""):
		print "on_radiobutton_redirect_TCP_toggled undefined!"
		pass
	def on_radiobutton_redirect_UDP_toggled(self, widget=None, data=""):
		print "on_radiobutton_redirect_UDP_toggled undefined!"
		pass
	def on_spinbutton_redirect_sport_changed(self, widget=None, data=""):
		print "on_spinbutton_redirect_sport_changed undefined!"
		pass
	def on_entry_redirect_gIP_changed(self, widget=None, data=""):
		print "on_entry_redirect_gIP_changed undefined!"
		pass
	def on_spinbutton_redirect_dport_changed(self, widget=None, data=""):
		print "on_spinbutton_redirect_dport_changed undefined!"
		pass

	def on_newbrick(self, widget=None, event=None, data=""):
		self.gladefile.get_widget('combo_newbricktype').set_active(0)
		self.show_window('dialog_newbrick')

	def on_brick_startstop(self,widget=None, event=None, data=""):
		pass
	def on_brick_delete(self,widget=None, event=None, data=""):
		pass
	def on_brick_configure(self,widget=None, event=None, data=""):
		self.curtain_up()
		pass
	def on_brick_copy(self,widget=None, event=None, data=""):
		pass
		

	def signals(self):
		self.signaldict =  {
			"on_window1_destroy":self.on_window1_destroy,
			"on_windown_destroy":self.on_windown_destroy,
			"on_newbrick_cancel":self.on_newbrick_cancel,
			"on_newbrick_ok":self.on_newbrick_ok,
			"on_error_close":self.on_error_close,
			"on_config_cancel":self.on_config_cancel,
			"on_config_ok":self.on_config_ok,
			"on_gilbert_toggle": self.on_gilbert_toggle,
			"on_mtu_toggle": self.on_mtu_toggle,
			"on_brick_startstop": self.tree_startstop,
			"on_brick_configure": self.on_brick_configure,
			"on_brick_copy":self.on_brick_copy,
			"on_brick_delete": self.on_brick_delete,
			"on_item_quit_activate":self.on_item_quit_activate,
			"on_item_settings_activate":self.on_item_settings_activate,
			"on_item_settings_autoshow_activate":self.on_item_settings_autoshow_activate,
			"on_item_settings_autohide_activate":self.on_item_settings_autohide_activate,
			"on_item_create_image_activate":self.on_item_create_image_activate,
			"on_item_about_activate":self.on_item_about_activate,
			"on_toolbutton_launch_clicked":self.on_toolbutton_launch_clicked,
			"on_toolbutton_launchxterm_clicked":self.on_toolbutton_launchxterm_clicked,
			"on_toolbutton_launch_unmanaged_clicked":self.on_toolbutton_launch_unmanaged_clicked,
			"on_vpaned_mainwindow_button_release_event":self.on_vpaned_mainwindow_button_release_event,
			"on_treeview_bookmarks_button_press_event":self.on_treeview_bookmarks_button_press_event,
			"on_treeview_bookmarks_cursor_changed":self.on_treeview_bookmarks_cursor_changed,
			"on_treeview_bookmarks_row_activated_event":self.on_treeview_bookmarks_row_activated_event,
			"on_focus_out":self.on_treeview_bookmarks_focus_out,
			"on_treeview_bootimages_button_press_event":self.on_treeview_bootimages_button_press_event,
			"on_treeview_bootimages_cursor_changed":self.on_treeview_bootimages_cursor_changed,
			"on_treeview_bootimages_row_activated_event":self.on_treeview_bootimages_row_activated_event,
			"on_treeview_joblist_button_press_event":self.on_treeview_joblist_button_press_event,
			"on_treeview_joblist_row_activated_event":self.on_treeview_joblist_row_activated_event,
			"on_button_togglesettings_clicked":self.on_button_togglesettings_clicked,
			"on_filechooserdialog_openimage_response":self.on_filechooserdialog_openimage_response,
			"on_button_openimage_cancel_clicked":self.on_button_openimage_cancel_clicked,
			"on_button_openimage_open_clicked":self.on_button_openimage_open_clicked,
			"on_dialog_settings_response":self.on_dialog_settings_response,
			"on_treeview_cdromdrives_row_activated":self.on_treeview_cdromdrives_row_activated,
			"on_button_settings_add_cdevice_clicked":self.on_button_settings_add_cdevice_clicked,
			"on_button_settings_rem_cdevice_clicked":self.on_button_settings_rem_cdevice_clicked,
			"on_treeview_qemupaths_row_activated":self.on_treeview_qemupaths_row_activated,
			"on_button_settings_add_qemubin_clicked":self.on_button_settings_add_qemubin_clicked,
			"on_button_settings_rem_qemubin_clicked":self.on_button_settings_rem_qemubin_clicked,
			"on_dialog_bookmarks_response":self.on_dialog_bookmarks_response,
			"on_edit_bookmark_activate":self.on_edit_bookmark_activate,
			"on_bookmark_info_activate":self.on_bookmark_info_activate,
			"on_delete_bookmark_activate":self.on_delete_bookmark_activate,
			"on_dialog_about_response":self.on_dialog_about_response,
			"on_dialog_create_image_response":self.on_dialog_create_image_response,
			"on_filechooserbutton_newimage_dest_selection_changed":self.on_filechooserbutton_newimage_dest_selection_changed,
			"on_filechooserbutton_newimage_dest_current_folder_changed":self.on_filechooserbutton_newimage_dest_current_folder_changed,
			"on_entry_newimage_name_changed":self.on_entry_newimage_name_changed,
			"on_combobox_newimage_format_changed":self.on_combobox_newimage_format_changed,
			"on_spinbutton_newimage_size_changed":self.on_spinbutton_newimage_size_changed,
			"on_combobox_newimage_sizeunit_changed":self.on_combobox_newimage_sizeunit_changed,
			"on_button_create_image_clicked":self.on_button_create_image_clicked,
			"on_dialog_messages_response":self.on_dialog_messages_response,
			"on_item_info_activate":self.on_item_info_activate,
			"on_item_bookmark_activate":self.on_item_bookmark_activate,
			"on_dialog_jobmonitor_response":self.on_dialog_jobmonitor_response,
			"on_toolbutton_stop_job_clicked":self.on_toolbutton_stop_job_clicked,
			"on_toolbutton_reset_job_clicked":self.on_toolbutton_reset_job_clicked,
			"on_toolbutton_pause_job_clicked":self.on_toolbutton_pause_job_clicked,
			"on_toolbutton_rerun_job_clicked":self.on_toolbutton_rerun_job_clicked,
			"on_treeview_jobmon_volumes_button_press_event":self.on_treeview_jobmon_volumes_button_press_event,
			"on_treeview_jobmon_volumes_row_activated":self.on_treeview_jobmon_volumes_row_activated,
			"on_button_jobmon_apply_cdrom_clicked":self.on_button_jobmon_apply_cdrom_clicked,
			"on_button_jobmon_apply_fda_clicked":self.on_button_jobmon_apply_fda_clicked,
			"on_button_jobmon_apply_fdb_clicked":self.on_button_jobmon_apply_fdb_clicked,
			"on_combobox_jobmon_cdrom_changed":self.on_combobox_jobmon_cdrom_changed,
			"on_combobox_jobmon_fda_changed":self.on_combobox_jobmon_fda_changed,
			"on_combobox_jobmon_fdb_changed":self.on_combobox_jobmon_fdb_changed,
			"on_treeview_usbhost_button_press_event":self.on_treeview_usbhost_button_press_event,
			"on_treeview_usbhost_row_activated":self.on_treeview_usbhost_row_activated,
			"on_treeview_usbguest_button_press_event":self.on_treeview_usbguest_button_press_event,
			"on_treeview_usbguest_row_activated":self.on_treeview_usbguest_row_activated,
			"on_item_jobmonoitor_activate":self.on_item_jobmonoitor_activate,
			"on_item_stop_job_activate":self.on_item_stop_job_activate,
			"on_item_cont_job_activate":self.on_item_cont_job_activate,
			"on_item_reset_job_activate":self.on_item_reset_job_activate,
			"on_item_kill_job_activate":self.on_item_kill_job_activate,
			"on_attach_device_activate":self.on_attach_device_activate,
			"on_detach_device_activate":self.on_detach_device_activate,
			"on_item_eject_activate":self.on_item_eject_activate,
			"on_dialog_newnetcard_response":self.on_dialog_newnetcard_response,
			"on_combobox_networktype_changed":self.on_combobox_networktype_changed,
			"on_entry_network_macaddr_changed":self.on_entry_network_macaddr_changed,
			"on_entry_network_ip_changed":self.on_entry_network_ip_changed,
			"on_spinbutton_network_port_changed":self.on_spinbutton_network_port_changed,
			"on_spinbutton_network_vlan_changed":self.on_spinbutton_network_vlan_changed,
			"on_entry_network_ifacename_changed":self.on_entry_network_ifacename_changed,
			"on_entry_network_tuntapscript_changed":self.on_entry_network_tuntapscript_changed,
			"on_button__network_open_tuntap_file_clicked":self.on_button__network_open_tuntap_file_clicked,
			"on_spinbutton_network_filedescriptor_changed":self.on_spinbutton_network_filedescriptor_changed,
			"on_dialog_new_redirect_response":self.on_dialog_new_redirect_response,
			"on_radiobutton_redirect_TCP_toggled":self.on_radiobutton_redirect_TCP_toggled,
			"on_radiobutton_redirect_UDP_toggled":self.on_radiobutton_redirect_UDP_toggled,
			"on_spinbutton_redirect_sport_changed":self.on_spinbutton_redirect_sport_changed,
			"on_entry_redirect_gIP_changed":self.on_entry_redirect_gIP_changed,
			"on_spinbutton_redirect_dport_changed":self.on_spinbutton_redirect_dport_changed,
			"on_newbrick":self.on_newbrick,
		}
		self.gladefile.signal_autoconnect(self.signaldict)

	""" ******************************************************** """
	"""                                                          """
	""" TIMERS                                                   """
	"""                                                          """
	"""                                                          """
	""" ******************************************************** """

	def timers(self):
		gobject.timeout_add(1000,self.check_joblist)
		gobject.timeout_add(200,self.check_bricks)

	def check_bricks(self):
		new_bricks = []
		force_render = False
		for b in self.brickfactory.bricks:
			if b.gui_changed:
				b.gui_changed = False
				force_render = True
			new_bricks.append(b)
		if force_render or new_bricks != self.bricks:
			self.bookmarks.clear()
			self.bricks = new_bricks
			tree = self.gladefile.get_widget('treeview_bookmarks')
			for b in self.bricks:
				iter = self.bookmarks.append(None, None)
				if b.proc is not None:
		                        self.bookmarks.set_value(iter,0,tree.render_icon(gtk.STOCK_YES, gtk.ICON_SIZE_LARGE_TOOLBAR))
				elif not b.properly_connected():
		                        self.bookmarks.set_value(iter,0,tree.render_icon(gtk.STOCK_DIALOG_ERROR, gtk.ICON_SIZE_LARGE_TOOLBAR))
				else:
		                        self.bookmarks.set_value(iter,0,tree.render_icon(gtk.STOCK_NO, gtk.ICON_SIZE_LARGE_TOOLBAR))

				self.bookmarks.set_value(iter,1,b.get_type())
				self.bookmarks.set_value(iter,2,b.name)
				if (b.get_type() == "Switch"):
					self.bookmarks.set_value(iter, 3, "Free ports: %d/%d" % (b.socks[0].get_free_ports(), int(str(b.cfg.numports))))
				if (b.get_type().startswith("Wire")):
						
					ok = -2
					p0 = "disconnected"
					p1 = "disconnected"
					if (b.plugs[0].sock):
						ok+=1
						p0 = b.plugs[0].sock.brick.name
					if b.plugs[1].sock:
						ok+=1
						p1 = b.plugs[1].sock.brick.name
					if ok == 0:
						self.bookmarks.set_value(iter, 3, "Configured to connect %s to %s" %(p0,p1))
					else:
						self.bookmarks.set_value(iter, 3, "Not yet configured. Left plug is %s and right plug is %s" % (p0,p1))
				if (b.get_type() == "Tap"):
					p0 = "disconnected"
					if b.plugs[0].sock:
						p0 = "plugged to " + b.plugs[0].sock.brick.name 
					self.bookmarks.set_value(iter, 3, p0)
				if (b.get_type() == "TunnelListen"):
					p0 = "disconnected"
					if b.plugs[0].sock:
						p0 = "plugged to " + b.plugs[0].sock.brick.name + ", listening to udp:" + b.cfg.port 
					self.bookmarks.set_value(iter, 3, p0)
				if (b.get_type() == "TunnelConnect"):
					p0 = "disconnected"
					if b.plugs[0].sock:
						p0 = "plugged to " + b.plugs[0].sock.brick.name + ", connecting to udp://" + b.cfg.host
					self.bookmarks.set_value(iter, 3, p0)
					
			print "bricks list updated"
		return True
			
			
		
	def check_joblist(self):
		new_ps = []
		for b in self.brickfactory.bricks:
			if b.proc is not None:
				new_ps.append(b)
				ret = b.proc.poll()
				if ret != None:
					b.poweroff()
					self.error("%s '%s' Terminated with code %d" %(b.get_type(), b.name, ret))
					b.gui_changed = True
		
		if self.ps != new_ps:
			self.ps = new_ps
			self.bricks = []
			self.running_bricks.clear()
			for b in self.ps:
				iter = self.running_bricks.append(None, None)
				self.running_bricks.set_value(iter,0,b.pid)
				self.running_bricks.set_value(iter,1,b.get_type())
				self.running_bricks.set_value(iter,2,b.name)
			print "proc list updated"
		return True
