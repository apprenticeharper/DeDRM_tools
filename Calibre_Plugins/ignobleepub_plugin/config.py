#!/usr/bin/env python

from __future__ import with_statement
__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib

# PyQT4 modules (part of calibre).
from PyQt4.Qt import (Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem,
                      QAbstractItemView, QIcon, QDialog, QUrl, QString)
from PyQt4 import QtGui

# calibre modules and constants.
from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url,
                            choose_dir, choose_files)
from calibre.utils.config import dynamic, config_dir, JSONConfig

# modules from this plugin's zipfile.
from calibre_plugins.ignoble_epub.__init__ import PLUGIN_NAME, PLUGIN_VERSION 
from calibre_plugins.ignoble_epub.__init__ import RESOURCE_NAME as help_file_name
from calibre_plugins.ignoble_epub.utilities import (_load_crypto, normalize_name,
                                generate_keyfile, caselessStrCmp, AddKeyDialog,
                                DETAILED_MESSAGE, parseCustString)

JSON_NAME = PLUGIN_NAME.strip().lower().replace(' ', '_')
JSON_PATH = 'plugins/' + JSON_NAME + '.json'

# This is where all preferences for this plugin will be stored
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig(JSON_PATH)

# Set defaults
prefs.defaults['keys'] = {}
prefs.defaults['configured'] = False

class ConfigWidget(QWidget):
    def __init__(self, help_file_data):
        QWidget.__init__(self)
        
        self.help_file_data = help_file_data
        self.plugin_keys = prefs['keys']

        # Handle the old plugin's customization string by either converting the
        # old string to stored keys or by saving the string to a text file of the
        # user's choice. Either way... get that personal data out of plain sight.
        from calibre.customize.ui import config
        sc = config['plugin_customization']
        val = sc.get(PLUGIN_NAME, None)
        if val is not None:
            title = 'Convert existing customization data?'
            msg = '<p>Convert your existing insecure customization data? (Please '+ \
                        'read the detailed message)'
            det_msg = DETAILED_MESSAGE

            # Offer to convert the old string to the new format
            if question_dialog(self, _(title), _(msg), det_msg, True, True):
                userkeys = parseCustString(str(val))
                if userkeys:
                    counter = 0
                    # Yay! We found valid customization data... add it to the new plugin
                    for k in userkeys:
                        counter += 1
                        self.plugin_keys['Converted Old Plugin Key - ' + str(counter)] = k
                    msg = '<p><b>' + str(counter) + '</b> User key(s) configured from old plugin customization string'
                    inf = info_dialog(None, _(PLUGIN_NAME + 'info_dlg'), _(msg), show=True)
                    val = sc.pop(PLUGIN_NAME, None)
                    if val is not None:
                        config['plugin_customization'] = sc
                else:
                    # The existing customization string was invalid and wouldn't have
                    # worked anyway. Offer to save it as a text file and get rid of it.
                    errmsg = '<p>Unknown Error converting user supplied-customization string'
                    r = error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
                    self.saveOldCustomizationData(str(val))
                    val = sc.pop(PLUGIN_NAME, None)
                    if val is not None:
                        config['plugin_customization'] = sc
            # If they don't want to convert the old string to keys then
            # offer to save the old string to a text file and delete the
            # the old customization string.
            else:
                self.saveOldCustomizationData(str(val))
                val = sc.pop(PLUGIN_NAME, None)
                if val is not None:
                    config['plugin_customization'] = sc
                    
        # First time run since upgrading to new key storage method, or 0 keys configured.
        # Prompt to import pre-existing key files.
        if not prefs['configured']:
            title = 'Import existing key files?'
            msg = '<p>This plugin no longer uses *.b64 keyfiles stored in calibre\'s configuration '+ \
                        'directory. Do you have any exsiting key files there (or anywhere) that you\'d '+ \
                        'like to migrate into the new plugin preferences method?'
            if question_dialog(self, _(title), _(msg)):
                self.migrate_files()

        # Start Qt Gui dialog layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        
        help_layout = QHBoxLayout()
        layout.addLayout(help_layout)
        # Add hyperlink to a help file at the right. We will replace the correct name when it is clicked.
        help_label = QLabel('<a href="http://www.foo.com/">Plugin Help</a>', self)
        help_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        help_label.setAlignment(Qt.AlignRight)
        help_label.linkActivated.connect(self.help_link_activated)
        help_layout.addWidget(help_label)
        
        keys_group_box = QGroupBox(_('Configured Ignoble Keys:'), self)
        layout.addWidget(keys_group_box)
        keys_group_box_layout = QHBoxLayout()
        keys_group_box.setLayout(keys_group_box_layout)
        
        self.listy = QListWidget(self)
        self.listy.setToolTip(_('<p>Stored Ignoble keys that will be used for decryption'))
        self.listy.setSelectionMode(QAbstractItemView.SingleSelection)
        self.populate_list()
        keys_group_box_layout.addWidget(self.listy)

        button_layout = QVBoxLayout()
        keys_group_box_layout.addLayout(button_layout)
        self._add_key_button = QtGui.QToolButton(self)
        self._add_key_button.setToolTip(_('Create new key'))
        self._add_key_button.setIcon(QIcon(I('plus.png')))
        self._add_key_button.clicked.connect(self.add_key)
        button_layout.addWidget(self._add_key_button)
        
        self._delete_key_button = QtGui.QToolButton(self)
        self._delete_key_button.setToolTip(_('Delete highlighted key'))
        self._delete_key_button.setIcon(QIcon(I('list_remove.png')))
        self._delete_key_button.clicked.connect(self.delete_key)
        button_layout.addWidget(self._delete_key_button)
        
        self.export_key_button = QtGui.QToolButton(self)
        self.export_key_button.setToolTip(_('Export highlighted key'))
        self.export_key_button.setIcon(QIcon(I('save.png')))
        self.export_key_button.clicked.connect(self.export_key)
        button_layout.addWidget(self.export_key_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)
        
        layout.addSpacing(20)
        migrate_layout = QHBoxLayout()
        layout.addLayout(migrate_layout)
        self.migrate_btn = QPushButton(_('Import Existing Keyfiles'), self)
        self.migrate_btn.setToolTip(_('<p>Import *.b64 keyfiles (used by older versions of the plugin).'))
        self.migrate_btn.clicked.connect(self.migrate_wrapper)
        migrate_layout.setAlignment(Qt.AlignLeft)
        migrate_layout.addWidget(self.migrate_btn)
        
        self.resize(self.sizeHint())

    def populate_list(self):
        for key in self.plugin_keys.keys():
            self.listy.addItem(QListWidgetItem(key))

    def add_key(self):
        d = AddKeyDialog(self)
        d.exec_()

        if d.result() != d.Accepted:
            # New key generation cancelled.
            return
        self.plugin_keys[d.key_name] = generate_keyfile(d.user_name, d.cc_number)

        self.listy.clear()
        self.populate_list()

    def delete_key(self):
        if not self.listy.currentItem():
            return
        keyname = unicode(self.listy.currentItem().text())
        if not question_dialog(self, _('Are you sure?'), _('<p>'+
                    'Do you really want to delete the Ignoble key named <strong>%s</strong>?') % keyname,
                    show_copy_button=False, default_yes=False):
            return
        del self.plugin_keys[keyname]
        
        self.listy.clear()
        self.populate_list()
  
    def help_link_activated(self, url):
        def get_help_file_resource():
            # Copy the HTML helpfile to the plugin directory each time the
            # link is clicked in case the helpfile is updated in newer plugins.
            file_path = os.path.join(config_dir, 'plugins', help_file_name)
            with open(file_path,'w') as f:
                f.write(self.help_file_data)
            return file_path
        url = 'file:///' + get_help_file_resource()
        open_url(QUrl(url))
        
    def save_settings(self):
        prefs['keys'] = self.plugin_keys
        if prefs['keys']:
            prefs['configured'] = True
        else:
            prefs['configured'] = False

    def migrate_files(self):
        dynamic[PLUGIN_NAME + 'config_dir'] = config_dir
        files = choose_files(self, PLUGIN_NAME + 'config_dir',
                _('Select Ignoble keyfiles to import'), [('Ignoble Keyfiles', ['b64'])], False)
        if files:
            counter = 0
            skipped = 0
            for filename in files:
                fpath = os.path.join(config_dir, filename)
                new_key_name = os.path.splitext(os.path.basename(filename))[0]
                match = False
                for key in self.plugin_keys.keys():
                    if caselessStrCmp(new_key_name, key) == 0:
                        match = True
                        break
                if not match:
                    with open(fpath, 'rb') as f:
                        counter += 1
                        self.plugin_keys[unicode(new_key_name)] = f.read()
                else:
                    skipped += 1
                    msg = '<p>A key with the name <strong>' + new_key_name + '</strong> already exists! </p>' + \
                           '<p>Skipping key file named <strong>' + filename + '</strong>.</p>' + \
                           '<p>Either delete the existing key and re-migrate, or ' + \
                           'create that key manually with a different name.'
                    inf = info_dialog(None, _(PLUGIN_NAME + 'info_dlg'),
                                _(msg), show=True)

            msg = '<p>Done migrating <strong>' + str(counter) + '</strong> ' + \
                                'key files...</p><p>Skipped <strong>' + str(skipped) + '</strong> key files.'
            inf = info_dialog(None, _(PLUGIN_NAME + 'info_dlg'),
                                    _(msg), show=True)
            return 1
        return 0

    def migrate_wrapper(self):
        if self.migrate_files():
            self.listy.clear()
            self.populate_list()

    def export_key(self):
        if not self.listy.currentItem():
            errmsg = '<p>No keyfile selected to export. Highlight a keyfile first.'
            r = error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
            return
        filter = QString('Ignoble Key Files (*.b64)')
        keyname = unicode(self.listy.currentItem().text())
        if dynamic.get(PLUGIN_NAME + 'save_dir'):
            defaultname = os.path.join(dynamic.get(PLUGIN_NAME + 'save_dir'), keyname + '.b64')
        else:
            defaultname = os.path.join(os.path.expanduser('~'), keyname + '.b64')
        filename = str(QtGui.QFileDialog.getSaveFileName(self, "Save Ignoble Key File as...", defaultname,
                                            "Ignoble Key Files (*.b64)", filter))
        if filename:
            dynamic[PLUGIN_NAME + 'save_dir'] = os.path.split(filename)[0]
            fname = open(filename, 'w')
            fname.write(self.plugin_keys[keyname])
            fname.close()

    def saveOldCustomizationData(self, strdata):
        filter = QString('Text files (*.txt)')
        default_basefilename = PLUGIN_NAME + ' old customization data.txt'
        defaultname = os.path.join(os.path.expanduser('~'), default_basefilename)
        filename = str(QtGui.QFileDialog.getSaveFileName(self, "Save old plugin style customization data as...", defaultname,
                                    "Text Files (*.txt)", filter))
        if filename:
            fname = open(filename, 'w')
            fname.write(strdata)
            fname.close()