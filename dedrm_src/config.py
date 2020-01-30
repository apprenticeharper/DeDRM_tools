#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement
from __future__ import print_function

__license__ = 'GPL v3'

# Standard Python modules.
import os, traceback, json

# PyQT4 modules (part of calibre).
try:
    from PyQt5.Qt import (Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem,
                      QAbstractItemView, QIcon, QDialog, QDialogButtonBox, QUrl)
except ImportError:
    from PyQt4.Qt import (Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem,
                      QAbstractItemView, QIcon, QDialog, QDialogButtonBox, QUrl)
try:
    from PyQt5 import Qt as QtGui
except ImportError:
    from PyQt4 import QtGui
    
from zipfile import ZipFile

# calibre modules and constants.
from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url,
                            choose_dir, choose_files, choose_save_file)
from calibre.utils.config import dynamic, config_dir, JSONConfig
from calibre.constants import iswindows, isosx

# modules from this plugin's zipfile.
from calibre_plugins.dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION
from calibre_plugins.dedrm.__init__ import RESOURCE_NAME as help_file_name
from calibre_plugins.dedrm.utilities import uStrCmp

import calibre_plugins.dedrm.prefs as prefs
import calibre_plugins.dedrm.androidkindlekey as androidkindlekey

class ConfigWidget(QWidget):
    def __init__(self, plugin_path, alfdir):
        QWidget.__init__(self)

        self.plugin_path = plugin_path
        self.alfdir = alfdir

        # get the prefs
        self.dedrmprefs = prefs.DeDRM_Prefs()

        # make a local copy
        self.tempdedrmprefs = {}
        self.tempdedrmprefs['bandnkeys'] = self.dedrmprefs['bandnkeys'].copy()
        self.tempdedrmprefs['adeptkeys'] = self.dedrmprefs['adeptkeys'].copy()
        self.tempdedrmprefs['ereaderkeys'] = self.dedrmprefs['ereaderkeys'].copy()
        self.tempdedrmprefs['kindlekeys'] = self.dedrmprefs['kindlekeys'].copy()
        self.tempdedrmprefs['androidkeys'] = self.dedrmprefs['androidkeys'].copy()
        self.tempdedrmprefs['pids'] = list(self.dedrmprefs['pids'])
        self.tempdedrmprefs['serials'] = list(self.dedrmprefs['serials'])
        self.tempdedrmprefs['adobewineprefix'] = self.dedrmprefs['adobewineprefix']
        self.tempdedrmprefs['kindlewineprefix'] = self.dedrmprefs['kindlewineprefix']

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

        keys_group_box = QGroupBox(_('Configuration:'), self)
        layout.addWidget(keys_group_box)
        keys_group_box_layout = QHBoxLayout()
        keys_group_box.setLayout(keys_group_box_layout)


        button_layout = QVBoxLayout()
        keys_group_box_layout.addLayout(button_layout)
        self.bandn_button = QtGui.QPushButton(self)
        self.bandn_button.setToolTip(_(u"Click to manage keys for Barnes and Noble ebooks"))
        self.bandn_button.setText(u"Barnes and Noble ebooks")
        self.bandn_button.clicked.connect(self.bandn_keys)
        self.kindle_android_button = QtGui.QPushButton(self)
        self.kindle_android_button.setToolTip(_(u"Click to manage keys for Kindle for Android ebooks"))
        self.kindle_android_button.setText(u"Kindle for Android ebooks")
        self.kindle_android_button.clicked.connect(self.kindle_android)
        self.kindle_serial_button = QtGui.QPushButton(self)
        self.kindle_serial_button.setToolTip(_(u"Click to manage eInk Kindle serial numbers for Kindle ebooks"))
        self.kindle_serial_button.setText(u"eInk Kindle ebooks")
        self.kindle_serial_button.clicked.connect(self.kindle_serials)
        self.kindle_key_button = QtGui.QPushButton(self)
        self.kindle_key_button.setToolTip(_(u"Click to manage keys for Kindle for Mac/PC ebooks"))
        self.kindle_key_button.setText(u"Kindle for Mac/PC ebooks")
        self.kindle_key_button.clicked.connect(self.kindle_keys)
        self.adept_button = QtGui.QPushButton(self)
        self.adept_button.setToolTip(_(u"Click to manage keys for Adobe Digital Editions ebooks"))
        self.adept_button.setText(u"Adobe Digital Editions ebooks")
        self.adept_button.clicked.connect(self.adept_keys)
        self.mobi_button = QtGui.QPushButton(self)
        self.mobi_button.setToolTip(_(u"Click to manage PIDs for Mobipocket ebooks"))
        self.mobi_button.setText(u"Mobipocket ebooks")
        self.mobi_button.clicked.connect(self.mobi_keys)
        self.ereader_button = QtGui.QPushButton(self)
        self.ereader_button.setToolTip(_(u"Click to manage keys for eReader ebooks"))
        self.ereader_button.setText(u"eReader ebooks")
        self.ereader_button.clicked.connect(self.ereader_keys)
        button_layout.addWidget(self.kindle_serial_button)
        button_layout.addWidget(self.kindle_android_button)
        button_layout.addWidget(self.bandn_button)
        button_layout.addWidget(self.mobi_button)
        button_layout.addWidget(self.ereader_button)
        button_layout.addWidget(self.adept_button)
        button_layout.addWidget(self.kindle_key_button)

        self.resize(self.sizeHint())

    def kindle_serials(self):
        d = ManageKeysDialog(self,u"EInk Kindle Serial Number",self.tempdedrmprefs['serials'], AddSerialDialog)
        d.exec_()
        
    def kindle_android(self):
        d = ManageKeysDialog(self,u"Kindle for Android Key",self.tempdedrmprefs['androidkeys'], AddAndroidDialog, 'k4a')
        d.exec_()

    def kindle_keys(self):
        if isosx or iswindows:
            d = ManageKeysDialog(self,u"Kindle for Mac and PC Key",self.tempdedrmprefs['kindlekeys'], AddKindleDialog, 'k4i')
        else:
            # linux
            d = ManageKeysDialog(self,u"Kindle for Mac and PC Key",self.tempdedrmprefs['kindlekeys'], AddKindleDialog, 'k4i', self.tempdedrmprefs['kindlewineprefix'])
        d.exec_()
        self.tempdedrmprefs['kindlewineprefix'] = d.getwineprefix()

    def adept_keys(self):
        if isosx or iswindows:
            d = ManageKeysDialog(self,u"Adobe Digital Editions Key",self.tempdedrmprefs['adeptkeys'], AddAdeptDialog, 'der')
        else:
            # linux
            d = ManageKeysDialog(self,u"Adobe Digital Editions Key",self.tempdedrmprefs['adeptkeys'], AddAdeptDialog, 'der', self.tempdedrmprefs['adobewineprefix'])
        d.exec_()
        self.tempdedrmprefs['adobewineprefix'] = d.getwineprefix()

    def mobi_keys(self):
        d = ManageKeysDialog(self,u"Mobipocket PID",self.tempdedrmprefs['pids'], AddPIDDialog)
        d.exec_()

    def bandn_keys(self):
        d = ManageKeysDialog(self,u"Barnes and Noble Key",self.tempdedrmprefs['bandnkeys'], AddBandNKeyDialog, 'b64')
        d.exec_()

    def ereader_keys(self):
        d = ManageKeysDialog(self,u"eReader Key",self.tempdedrmprefs['ereaderkeys'], AddEReaderDialog, 'b63')
        d.exec_()

    def help_link_activated(self, url):
        def get_help_file_resource():
            # Copy the HTML helpfile to the plugin directory each time the
            # link is clicked in case the helpfile is updated in newer plugins.
            file_path = os.path.join(config_dir, u"plugins", u"DeDRM", u"help", help_file_name)
            with open(file_path,'w') as f:
                f.write(self.load_resource(help_file_name))
            return file_path
        url = 'file:///' + get_help_file_resource()
        open_url(QUrl(url))

    def save_settings(self):
        self.dedrmprefs.set('bandnkeys', self.tempdedrmprefs['bandnkeys'])
        self.dedrmprefs.set('adeptkeys', self.tempdedrmprefs['adeptkeys'])
        self.dedrmprefs.set('ereaderkeys', self.tempdedrmprefs['ereaderkeys'])
        self.dedrmprefs.set('kindlekeys', self.tempdedrmprefs['kindlekeys'])
        self.dedrmprefs.set('androidkeys', self.tempdedrmprefs['androidkeys'])
        self.dedrmprefs.set('pids', self.tempdedrmprefs['pids'])
        self.dedrmprefs.set('serials', self.tempdedrmprefs['serials'])
        self.dedrmprefs.set('adobewineprefix', self.tempdedrmprefs['adobewineprefix'])
        self.dedrmprefs.set('kindlewineprefix', self.tempdedrmprefs['kindlewineprefix'])
        self.dedrmprefs.set('configured', True)
        self.dedrmprefs.writeprefs()

    def load_resource(self, name):
        with ZipFile(self.plugin_path, 'r') as zf:
            if name in zf.namelist():
                return zf.read(name)
        return ""



class ManageKeysDialog(QDialog):
    def __init__(self, parent, key_type_name, plugin_keys, create_key, keyfile_ext = u"", wineprefix = None):
        QDialog.__init__(self,parent)
        self.parent = parent
        self.key_type_name = key_type_name
        self.plugin_keys = plugin_keys
        self.create_key = create_key
        self.keyfile_ext = keyfile_ext
        self.import_key = (keyfile_ext != u"")
        self.binary_file = (keyfile_ext == u"der")
        self.json_file = (keyfile_ext == u"k4i")
        self.android_file = (keyfile_ext == u"k4a")
        self.wineprefix = wineprefix

        self.setWindowTitle("{0} {1}: Manage {2}s".format(PLUGIN_NAME, PLUGIN_VERSION, self.key_type_name))

        # Start Qt Gui dialog layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        help_layout = QHBoxLayout()
        layout.addLayout(help_layout)
        # Add hyperlink to a help file at the right. We will replace the correct name when it is clicked.
        help_label = QLabel('<a href="http://www.foo.com/">Help</a>', self)
        help_label.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)
        help_label.setAlignment(Qt.AlignRight)
        help_label.linkActivated.connect(self.help_link_activated)
        help_layout.addWidget(help_label)

        keys_group_box = QGroupBox(_(u"{0}s".format(self.key_type_name)), self)
        layout.addWidget(keys_group_box)
        keys_group_box_layout = QHBoxLayout()
        keys_group_box.setLayout(keys_group_box_layout)

        self.listy = QListWidget(self)
        self.listy.setToolTip(u"{0}s that will be used to decrypt ebooks".format(self.key_type_name))
        self.listy.setSelectionMode(QAbstractItemView.SingleSelection)
        self.populate_list()
        keys_group_box_layout.addWidget(self.listy)

        button_layout = QVBoxLayout()
        keys_group_box_layout.addLayout(button_layout)
        self._add_key_button = QtGui.QToolButton(self)
        self._add_key_button.setIcon(QIcon(I('plus.png')))
        self._add_key_button.setToolTip(u"Create new {0}".format(self.key_type_name))
        self._add_key_button.clicked.connect(self.add_key)
        button_layout.addWidget(self._add_key_button)

        self._delete_key_button = QtGui.QToolButton(self)
        self._delete_key_button.setToolTip(_(u"Delete highlighted key"))
        self._delete_key_button.setIcon(QIcon(I('list_remove.png')))
        self._delete_key_button.clicked.connect(self.delete_key)
        button_layout.addWidget(self._delete_key_button)

        if type(self.plugin_keys) == dict and self.import_key:
            self._rename_key_button = QtGui.QToolButton(self)
            self._rename_key_button.setToolTip(_(u"Rename highlighted key"))
            self._rename_key_button.setIcon(QIcon(I('edit-select-all.png')))
            self._rename_key_button.clicked.connect(self.rename_key)
            button_layout.addWidget(self._rename_key_button)

            self.export_key_button = QtGui.QToolButton(self)
            self.export_key_button.setToolTip(u"Save highlighted key to a .{0} file".format(self.keyfile_ext))
            self.export_key_button.setIcon(QIcon(I('save.png')))
            self.export_key_button.clicked.connect(self.export_key)
            button_layout.addWidget(self.export_key_button)
        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)

        if self.wineprefix is not None:
            layout.addSpacing(5)
            wineprefix_layout = QHBoxLayout()
            layout.addLayout(wineprefix_layout)
            wineprefix_layout.setAlignment(Qt.AlignCenter)
            self.wp_label = QLabel(u"WINEPREFIX:")
            wineprefix_layout.addWidget(self.wp_label)
            self.wp_lineedit = QLineEdit(self)
            wineprefix_layout.addWidget(self.wp_lineedit)
            self.wp_label.setBuddy(self.wp_lineedit)
            self.wp_lineedit.setText(self.wineprefix)

        layout.addSpacing(5)
        migrate_layout = QHBoxLayout()
        layout.addLayout(migrate_layout)
        if self.import_key:
            migrate_layout.setAlignment(Qt.AlignJustify)
            self.migrate_btn = QPushButton(u"Import Existing Keyfiles", self)
            self.migrate_btn.setToolTip(u"Import *.{0} files (created using other tools).".format(self.keyfile_ext))
            self.migrate_btn.clicked.connect(self.migrate_wrapper)
            migrate_layout.addWidget(self.migrate_btn)
        migrate_layout.addStretch()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.close)
        migrate_layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    def getwineprefix(self):
        if self.wineprefix is not None:
            return unicode(self.wp_lineedit.text()).strip()
        return u""

    def populate_list(self):
        if type(self.plugin_keys) == dict:
            for key in self.plugin_keys.keys():
                self.listy.addItem(QListWidgetItem(key))
        else:
            for key in self.plugin_keys:
                self.listy.addItem(QListWidgetItem(key))

    def add_key(self):
        d = self.create_key(self)
        d.exec_()

        if d.result() != d.Accepted:
            # New key generation cancelled.
            return
        new_key_value = d.key_value
        if type(self.plugin_keys) == dict:
            if new_key_value in self.plugin_keys.values():
                old_key_name = [name for name, value in self.plugin_keys.iteritems() if value == new_key_value][0]
                info_dialog(None, "{0} {1}: Duplicate {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                                    u"The new {1} is the same as the existing {1} named <strong>{0}</strong> and has not been added.".format(old_key_name,self.key_type_name), show=True)
                return
            self.plugin_keys[d.key_name] = new_key_value
        else:
            if new_key_value in self.plugin_keys:
                info_dialog(None, "{0} {1}: Duplicate {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                                    u"This {0} is already in the list of {0}s has not been added.".format(self.key_type_name), show=True)
                return

            self.plugin_keys.append(d.key_value)
        self.listy.clear()
        self.populate_list()

    def rename_key(self):
        if not self.listy.currentItem():
            errmsg = u"No {0} selected to rename. Highlight a keyfile first.".format(self.key_type_name)
            r = error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
            return

        d = RenameKeyDialog(self)
        d.exec_()

        if d.result() != d.Accepted:
            # rename cancelled or moot.
            return
        keyname = unicode(self.listy.currentItem().text())
        if not question_dialog(self, "{0} {1}: Confirm Rename".format(PLUGIN_NAME, PLUGIN_VERSION), u"Do you really want to rename the {2} named <strong>{0}</strong> to <strong>{1}</strong>?".format(keyname,d.key_name,self.key_type_name), show_copy_button=False, default_yes=False):
            return
        self.plugin_keys[d.key_name] = self.plugin_keys[keyname]
        del self.plugin_keys[keyname]

        self.listy.clear()
        self.populate_list()

    def delete_key(self):
        if not self.listy.currentItem():
            return
        keyname = unicode(self.listy.currentItem().text())
        if not question_dialog(self, "{0} {1}: Confirm Delete".format(PLUGIN_NAME, PLUGIN_VERSION), u"Do you really want to delete the {1} <strong>{0}</strong>?".format(keyname, self.key_type_name), show_copy_button=False, default_yes=False):
            return
        if type(self.plugin_keys) == dict:
            del self.plugin_keys[keyname]
        else:
            self.plugin_keys.remove(keyname)

        self.listy.clear()
        self.populate_list()

    def help_link_activated(self, url):
        def get_help_file_resource():
            # Copy the HTML helpfile to the plugin directory each time the
            # link is clicked in case the helpfile is updated in newer plugins.
            help_file_name = u"{0}_{1}_Help.htm".format(PLUGIN_NAME, self.key_type_name)
            file_path = os.path.join(config_dir, u"plugins", u"DeDRM", u"help", help_file_name)
            with open(file_path,'w') as f:
                f.write(self.parent.load_resource(help_file_name))
            return file_path
        url = 'file:///' + get_help_file_resource()
        open_url(QUrl(url))

    def migrate_files(self):
        unique_dlg_name = PLUGIN_NAME + u"import {0} keys".format(self.key_type_name).replace(' ', '_') #takes care of automatically remembering last directory
        caption = u"Select {0} files to import".format(self.key_type_name)
        filters = [(u"{0} files".format(self.key_type_name), [self.keyfile_ext])]
        files = choose_files(self, unique_dlg_name, caption, filters, all_files=False)
        counter = 0
        skipped = 0
        if files:
            for filename in files:
                fpath = os.path.join(config_dir, filename)
                filename = os.path.basename(filename)
                new_key_name = os.path.splitext(os.path.basename(filename))[0]
                with open(fpath,'rb') as keyfile:
                    new_key_value = keyfile.read()
                if self.binary_file:
                    new_key_value = new_key_value.encode('hex')
                elif self.json_file:
                    new_key_value = json.loads(new_key_value)
                elif self.android_file:
                    # convert to list of the keys in the string
                    new_key_value = new_key_value.splitlines()
                match = False
                for key in self.plugin_keys.keys():
                    if uStrCmp(new_key_name, key, True):
                        skipped += 1
                        msg = u"A key with the name <strong>{0}</strong> already exists!\nSkipping key file  <strong>{1}</strong>.\nRename the existing key and import again".format(new_key_name,filename)
                        inf = info_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                _(msg), show_copy_button=False, show=True)
                        match = True
                        break
                if not match:
                    if new_key_value in self.plugin_keys.values():
                        old_key_name = [name for name, value in self.plugin_keys.iteritems() if value == new_key_value][0]
                        skipped += 1
                        info_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                            u"The key in file {0} is the same as the existing key <strong>{1}</strong> and has been skipped.".format(filename,old_key_name), show_copy_button=False, show=True)
                    else:
                        counter += 1
                        self.plugin_keys[new_key_name] = new_key_value
                            
            msg = u""
            if counter+skipped > 1:
                if counter > 0:
                    msg += u"Imported <strong>{0:d}</strong> key {1}. ".format(counter, u"file" if counter == 1 else u"files")
                if skipped > 0:
                    msg += u"Skipped <strong>{0:d}</strong> key {1}.".format(skipped, u"file" if counter == 1 else u"files")
                inf = info_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(msg), show_copy_button=False, show=True)
        return counter > 0

    def migrate_wrapper(self):
        if self.migrate_files():
            self.listy.clear()
            self.populate_list()

    def export_key(self):
        if not self.listy.currentItem():
            errmsg = u"No keyfile selected to export. Highlight a keyfile first."
            r = error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
            return
        keyname = unicode(self.listy.currentItem().text())
        unique_dlg_name = PLUGIN_NAME + u"export {0} keys".format(self.key_type_name).replace(' ', '_') #takes care of automatically remembering last directory
        caption = u"Save {0} File as...".format(self.key_type_name)
        filters = [(u"{0} Files".format(self.key_type_name), [u"{0}".format(self.keyfile_ext)])]
        defaultname = u"{0}.{1}".format(keyname, self.keyfile_ext)
        filename = choose_save_file(self, unique_dlg_name,  caption, filters, all_files=False, initial_filename=defaultname)
        if filename:
            with file(filename, 'wb') as fname:
                if self.binary_file:
                    fname.write(self.plugin_keys[keyname].decode('hex'))
                elif self.json_file:
                    fname.write(json.dumps(self.plugin_keys[keyname]))
                elif self.android_file:
                    for key in self.plugin_keys[keyname]:
                        fname.write(key)
                        fname.write("\n")
                else:
                    fname.write(self.plugin_keys[keyname])




class RenameKeyDialog(QDialog):
    def __init__(self, parent=None,):
        print(repr(self), repr(parent))
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Rename {0}".format(PLUGIN_NAME, PLUGIN_VERSION, parent.key_type_name))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox('', self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        data_group_box_layout.addWidget(QLabel('New Key Name:', self))
        self.key_ledit = QLineEdit(self.parent.listy.currentItem().text(), self)
        self.key_ledit.setToolTip(u"Enter a new name for this existing {0}.".format(parent.key_type_name))
        data_group_box_layout.addWidget(self.key_ledit)

        layout.addSpacing(20)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    def accept(self):
        if not unicode(self.key_ledit.text()) or unicode(self.key_ledit.text()).isspace():
            errmsg = u"Key name field cannot be empty!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
        if len(self.key_ledit.text()) < 4:
            errmsg = u"Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
        if uStrCmp(self.key_ledit.text(), self.parent.listy.currentItem().text()):
                # Same exact name ... do nothing.
                return QDialog.reject(self)
        for k in self.parent.plugin_keys.keys():
            if (uStrCmp(self.key_ledit.text(), k, True) and
                        not uStrCmp(k, self.parent.listy.currentItem().text(), True)):
                errmsg = u"The key name <strong>{0}</strong> is already being used.".format(self.key_ledit.text())
                return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
        QDialog.accept(self)

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()








class AddBandNKeyDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Create New Barnes & Noble Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox(u"", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(_(u"<p>Enter an identifying name for this new key.</p>" +
                                u"<p>It should be something that will help you remember " +
                                u"what personal information was used to create it."))
        key_group.addWidget(self.key_ledit)

        name_group = QHBoxLayout()
        data_group_box_layout.addLayout(name_group)
        name_group.addWidget(QLabel(u"B&N/nook account email address:", self))
        self.name_ledit = QLineEdit(u"", self)
        self.name_ledit.setToolTip(_(u"<p>Enter your email address as it appears in your B&N " +
                                u"account.</p>" +
                                u"<p>It will only be used to generate this " +
                                u"key and won\'t be stored anywhere " +
                                u"in calibre or on your computer.</p>" +
                                u"<p>eg: apprenticeharper@gmail.com</p>"))
        name_group.addWidget(self.name_ledit)
        name_disclaimer_label = QLabel(_(u"(Will not be saved in configuration data)"), self)
        name_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(name_disclaimer_label)

        ccn_group = QHBoxLayout()
        data_group_box_layout.addLayout(ccn_group)
        ccn_group.addWidget(QLabel(u"B&N/nook account password:", self))
        self.cc_ledit = QLineEdit(u"", self)
        self.cc_ledit.setToolTip(_(u"<p>Enter the password " +
                                u"for your B&N account.</p>" +
                                u"<p>The password will only be used to generate this " +
                                u"key and won\'t be stored anywhere in " +
                                u"calibre or on your computer."))
        ccn_group.addWidget(self.cc_ledit)
        ccn_disclaimer_label = QLabel(_('(Will not be saved in configuration data)'), self)
        ccn_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(ccn_disclaimer_label)
        layout.addSpacing(10)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"Retrieved key:", self))
        self.key_display = QLabel(u"", self)
        self.key_display.setToolTip(_(u"Click the Retrieve Key button to fetch your B&N encryption key from the B&N servers"))
        key_group.addWidget(self.key_display)
        self.retrieve_button = QtGui.QPushButton(self)
        self.retrieve_button.setToolTip(_(u"Click to retrieve your B&N encryption key from the B&N servers"))
        self.retrieve_button.setText(u"Retrieve Key")
        self.retrieve_button.clicked.connect(self.retrieve_key)
        key_group.addWidget(self.retrieve_button)
        layout.addSpacing(10)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return unicode(self.key_display.text()).strip()

    @property
    def user_name(self):
        return unicode(self.name_ledit.text()).strip().lower().replace(' ','')

    @property
    def cc_number(self):
        return unicode(self.cc_ledit.text()).strip()

    def retrieve_key(self):
        from calibre_plugins.dedrm.ignoblekeyfetch import fetch_key as fetch_bandn_key
        fetched_key = fetch_bandn_key(self.user_name,self.cc_number)
        if fetched_key == "":
            errmsg = u"Could not retrieve key. Check username, password and intenet connectivity and try again."
            error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        else:
            self.key_display.setText(fetched_key)

    def accept(self):
        if len(self.key_name) == 0 or len(self.user_name) == 0 or len(self.cc_number) == 0 or self.key_name.isspace() or self.user_name.isspace() or self.cc_number.isspace():
            errmsg = u"All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = u"Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_value) == 0:
            self.retrieve_key()
            if len(self.key_value) == 0:
                return
        QDialog.accept(self)

class AddEReaderDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Create New eReader Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox(u"", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(u"<p>Enter an identifying name for this new key.\nIt should be something that will help you remember what personal information was used to create it.")
        key_group.addWidget(self.key_ledit)

        name_group = QHBoxLayout()
        data_group_box_layout.addLayout(name_group)
        name_group.addWidget(QLabel(u"Your Name:", self))
        self.name_ledit = QLineEdit(u"", self)
        self.name_ledit.setToolTip(u"Enter the name for this eReader key, usually the name on your credit card.\nIt will only be used to generate this one-time key and won\'t be stored anywhere in calibre or on your computer.\n(ex: Mr Jonathan Q Smith)")
        name_group.addWidget(self.name_ledit)
        name_disclaimer_label = QLabel(_(u"(Will not be saved in configuration data)"), self)
        name_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(name_disclaimer_label)

        ccn_group = QHBoxLayout()
        data_group_box_layout.addLayout(ccn_group)
        ccn_group.addWidget(QLabel(u"Credit Card#:", self))
        self.cc_ledit = QLineEdit(u"", self)
        self.cc_ledit.setToolTip(u"<p>Enter the last 8 digits of credit card number for this eReader key.\nThey will only be used to generate this one-time key and won\'t be stored anywhere in calibre or on your computer.")
        ccn_group.addWidget(self.cc_ledit)
        ccn_disclaimer_label = QLabel(_('(Will not be saved in configuration data)'), self)
        ccn_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(ccn_disclaimer_label)
        layout.addSpacing(10)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        from calibre_plugins.dedrm.erdr2pml import getuser_key as generate_ereader_key
        return generate_ereader_key(self.user_name,self.cc_number).encode('hex')

    @property
    def user_name(self):
        return unicode(self.name_ledit.text()).strip().lower().replace(' ','')

    @property
    def cc_number(self):
        return unicode(self.cc_ledit.text()).strip().replace(' ', '').replace('-','')


    def accept(self):
        if len(self.key_name) == 0 or len(self.user_name) == 0 or len(self.cc_number) == 0 or self.key_name.isspace() or self.user_name.isspace() or self.cc_number.isspace():
            errmsg = u"All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if not self.cc_number.isdigit():
            errmsg = u"Numbers only in the credit card number field!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = u"Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddAdeptDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Getting Default Adobe Digital Editions Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        try:
            if iswindows or isosx:
                from calibre_plugins.dedrm.adobekey import adeptkeys

                defaultkeys = adeptkeys()
            else:  # linux
                from wineutils import WineGetKeys

                scriptpath = os.path.join(parent.parent.alfdir,u"adobekey.py")
                defaultkeys = WineGetKeys(scriptpath, u".der",parent.getwineprefix())

            self.default_key = defaultkeys[0]
        except:
            traceback.print_exc()
            self.default_key = u""

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        if len(self.default_key)>0:
            data_group_box = QGroupBox(u"", self)
            layout.addWidget(data_group_box)
            data_group_box_layout = QVBoxLayout()
            data_group_box.setLayout(data_group_box_layout)

            key_group = QHBoxLayout()
            data_group_box_layout.addLayout(key_group)
            key_group.addWidget(QLabel(u"Unique Key Name:", self))
            self.key_ledit = QLineEdit(u"default_key", self)
            self.key_ledit.setToolTip(u"<p>Enter an identifying name for the current default Adobe Digital Editions key.")
            key_group.addWidget(self.key_ledit)

            self.button_box.accepted.connect(self.accept)
        else:
            default_key_error = QLabel(u"The default encryption key for Adobe Digital Editions could not be found.", self)
            default_key_error.setAlignment(Qt.AlignHCenter)
            layout.addWidget(default_key_error)
            # if no default, bot buttons do the same
            self.button_box.accepted.connect(self.reject)

        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return self.default_key.encode('hex')


    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = u"Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddKindleDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Getting Default Kindle for Mac/PC Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        try:
            if iswindows or isosx:
                from calibre_plugins.dedrm.kindlekey import kindlekeys

                defaultkeys = kindlekeys()
            else: # linux
                from wineutils import WineGetKeys

                scriptpath = os.path.join(parent.parent.alfdir,u"kindlekey.py")
                defaultkeys = WineGetKeys(scriptpath, u".k4i",parent.getwineprefix())

            self.default_key = defaultkeys[0]
        except:
            traceback.print_exc()
            self.default_key = u""

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        if len(self.default_key)>0:
            data_group_box = QGroupBox(u"", self)
            layout.addWidget(data_group_box)
            data_group_box_layout = QVBoxLayout()
            data_group_box.setLayout(data_group_box_layout)

            key_group = QHBoxLayout()
            data_group_box_layout.addLayout(key_group)
            key_group.addWidget(QLabel(u"Unique Key Name:", self))
            self.key_ledit = QLineEdit(u"default_key", self)
            self.key_ledit.setToolTip(u"<p>Enter an identifying name for the current default Kindle for Mac/PC key.")
            key_group.addWidget(self.key_ledit)

            self.button_box.accepted.connect(self.accept)
        else:
            default_key_error = QLabel(u"The default encryption key for Kindle for Mac/PC could not be found.", self)
            default_key_error.setAlignment(Qt.AlignHCenter)
            layout.addWidget(default_key_error)
            
            # if no default, both buttons do the same
            self.button_box.accepted.connect(self.reject)

        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return self.default_key


    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = u"Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddSerialDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Add New EInk Kindle Serial Number".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox(u"", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"EInk Kindle Serial Number:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(u"Enter an eInk Kindle serial number. EInk Kindle serial numbers are 16 characters long and usually start with a 'B' or a '9'. Kindle Serial Numbers are case-sensitive, so be sure to enter the upper and lower case letters unchanged.")
        key_group.addWidget(self.key_ledit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return unicode(self.key_ledit.text()).replace(' ', '')

    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"Please enter an eInk Kindle Serial Number or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 16:
            errmsg = u"EInk Kindle Serial Numbers must be 16 characters long. This is {0:d} characters long.".format(len(self.key_name))
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddAndroidDialog(QDialog):
    def __init__(self, parent=None,):

        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Add new Kindle for Android Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        data_group_box = QGroupBox(u"", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        file_group = QHBoxLayout()
        data_group_box_layout.addLayout(file_group)
        add_btn = QPushButton(u"Choose Backup File", self)
        add_btn.setToolTip(u"Import Kindle for Android backup file.")
        add_btn.clicked.connect(self.get_android_file)
        file_group.addWidget(add_btn)
        self.selected_file_name = QLabel(u"",self)
        self.selected_file_name.setAlignment(Qt.AlignHCenter)
        file_group.addWidget(self.selected_file_name)
        
        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"Unique Key Name:", self))
        self.key_ledit = QLineEdit(u"", self)
        self.key_ledit.setToolTip(u"<p>Enter an identifying name for the Android for Kindle key.")
        key_group.addWidget(self.key_ledit)
        #key_label = QLabel(_(''), self)
        #key_label.setAlignment(Qt.AlignHCenter)
        #data_group_box_layout.addWidget(key_label)
        
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)
        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def file_name(self):
        return unicode(self.selected_file_name.text()).strip()

    @property
    def key_value(self):
        return self.serials_from_file
        
    def get_android_file(self):
        unique_dlg_name = PLUGIN_NAME + u"Import Kindle for Android backup file" #takes care of automatically remembering last directory
        caption = u"Select Kindle for Android backup file to add"
        filters = [(u"Kindle for Android backup files", ['db','ab','xml'])]
        files = choose_files(self, unique_dlg_name, caption, filters, all_files=False)
        self.serials_from_file = []
        file_name = u""
        if files:
            # find the first selected file that yields some serial numbers
            for filename in files:
                fpath = os.path.join(config_dir, filename)
                self.filename = os.path.basename(filename)
                file_serials = androidkindlekey.get_serials(fpath)
                if len(file_serials)>0:
                    file_name = os.path.basename(self.filename)
                    self.serials_from_file.extend(file_serials)
        self.selected_file_name.setText(file_name)
    

    def accept(self):
        if len(self.file_name) == 0 or len(self.key_value) == 0:
            errmsg = u"Please choose a Kindle for Android backup file."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"Please enter a key name."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = u"Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)

class AddPIDDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Add New Mobipocket PID".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox(u"", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"PID:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(u"Enter a Mobipocket PID. Mobipocket PIDs are 8 or 10 characters long. Mobipocket PIDs are case-sensitive, so be sure to enter the upper and lower case letters unchanged.")
        key_group.addWidget(self.key_ledit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return unicode(self.key_ledit.text()).strip()

    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"Please enter a Mobipocket PID or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 8 and len(self.key_name) != 10:
            errmsg = u"Mobipocket PIDs must be 8 or 10 characters long. This is {0:d} characters long.".format(len(self.key_name))
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


