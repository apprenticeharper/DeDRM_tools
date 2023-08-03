#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__license__ = 'GPL v3'

# Python 3, September 2020

# Standard Python modules.
import sys, os, traceback, json, codecs, base64, time

from PyQt5.Qt import (Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem, QCheckBox,
                      QAbstractItemView, QIcon, QDialog, QDialogButtonBox, QUrl, 
                      QCheckBox, QComboBox)

from PyQt5 import Qt as QtGui
from zipfile import ZipFile


#@@CALIBRE_COMPAT_CODE@@


# calibre modules and constants.
from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url,
                            choose_dir, choose_files, choose_save_file)
from calibre.utils.config import dynamic, config_dir, JSONConfig
from calibre.constants import iswindows, isosx


from __init__ import PLUGIN_NAME, PLUGIN_VERSION
from __version import RESOURCE_NAME as help_file_name
from .utilities import uStrCmp

import prefs
import androidkindlekey

def checkForDeACSMkeys(): 
        try: 
            from calibre_plugins.deacsm.libadobeAccount import exportAccountEncryptionKeyDER, getAccountUUID
        except: 
            # Looks like DeACSM is not installed. 
            return None, None

        try:
            from calibre.ptempfile import TemporaryFile
       

            acc_uuid = getAccountUUID()
            if acc_uuid is None: 
                return None, None

            name = "DeACSM_uuid_" + getAccountUUID()

            # Unfortunately, the DeACSM plugin only has code to export to a file, not to return raw key bytes.
            # Make a temporary file, have the plugin write to that, then read (& delete) that file.

            with TemporaryFile(suffix='.der') as tmp_key_file:
                export_result = exportAccountEncryptionKeyDER(tmp_key_file)

                if (export_result is False): 
                    return None, None

                # Read key file
                with open(tmp_key_file,'rb') as keyfile:
                    new_key_value = keyfile.read()

            return new_key_value, name
        except: 
            traceback.print_exc()
            return None, None


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
        self.tempdedrmprefs['deobfuscate_fonts'] = self.dedrmprefs['deobfuscate_fonts']
        self.tempdedrmprefs['remove_watermarks'] = self.dedrmprefs['remove_watermarks']
        self.tempdedrmprefs['lcp_passphrases'] = list(self.dedrmprefs['lcp_passphrases'])
        self.tempdedrmprefs['adobe_pdf_passphrases'] = list(self.dedrmprefs['adobe_pdf_passphrases'])

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
        self.bandn_button.setToolTip(_("Click to manage keys for ADE books with PassHash algorithm. <br/>Commonly used by Barnes and Noble"))
        self.bandn_button.setText("ADE PassHash (B&&N) ebooks")
        self.bandn_button.clicked.connect(self.bandn_keys)
        self.kindle_android_button = QtGui.QPushButton(self)
        self.kindle_android_button.setToolTip(_("Click to manage keys for Kindle for Android ebooks"))
        self.kindle_android_button.setText("Kindle for Android ebooks")
        self.kindle_android_button.clicked.connect(self.kindle_android)
        self.kindle_serial_button = QtGui.QPushButton(self)
        self.kindle_serial_button.setToolTip(_("Click to manage eInk Kindle serial numbers for Kindle ebooks"))
        self.kindle_serial_button.setText("Kindle eInk ebooks")
        self.kindle_serial_button.clicked.connect(self.kindle_serials)
        self.kindle_key_button = QtGui.QPushButton(self)
        self.kindle_key_button.setToolTip(_("Click to manage keys for Kindle for Mac/PC ebooks"))
        self.kindle_key_button.setText("Kindle for Mac/PC ebooks")
        self.kindle_key_button.clicked.connect(self.kindle_keys)
        self.adept_button = QtGui.QPushButton(self)
        self.adept_button.setToolTip(_("Click to manage keys for Adobe Digital Editions ebooks"))
        self.adept_button.setText("Adobe Digital Editions ebooks")
        self.adept_button.clicked.connect(self.adept_keys)
        self.mobi_button = QtGui.QPushButton(self)
        self.mobi_button.setToolTip(_("Click to manage PIDs for Mobipocket ebooks"))
        self.mobi_button.setText("Mobipocket ebooks")
        self.mobi_button.clicked.connect(self.mobi_keys)
        self.ereader_button = QtGui.QPushButton(self)
        self.ereader_button.setToolTip(_("Click to manage keys for eReader ebooks"))
        self.ereader_button.setText("eReader ebooks")
        self.ereader_button.clicked.connect(self.ereader_keys)
        self.lcp_button = QtGui.QPushButton(self)
        self.lcp_button.setToolTip(_("Click to manage passphrases for Readium LCP ebooks"))
        self.lcp_button.setText("Readium LCP ebooks")
        self.lcp_button.clicked.connect(self.readium_lcp_keys)
        self.pdf_keys_button = QtGui.QPushButton(self)
        self.pdf_keys_button.setToolTip(_("Click to manage PDF file passphrases"))
        self.pdf_keys_button.setText("Adobe PDF passwords")
        self.pdf_keys_button.clicked.connect(self.pdf_passphrases)

        button_layout.addWidget(self.kindle_serial_button)
        button_layout.addWidget(self.kindle_android_button)
        button_layout.addWidget(self.kindle_key_button)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.adept_button)
        button_layout.addWidget(self.bandn_button)
        button_layout.addWidget(self.pdf_keys_button)
        button_layout.addSpacing(15)
        button_layout.addWidget(self.mobi_button)
        button_layout.addWidget(self.ereader_button)
        button_layout.addWidget(self.lcp_button)
        

        self.chkFontObfuscation = QtGui.QCheckBox(_("Deobfuscate EPUB fonts"))
        self.chkFontObfuscation.setToolTip("Deobfuscates fonts in EPUB files after DRM removal")
        self.chkFontObfuscation.setChecked(self.tempdedrmprefs["deobfuscate_fonts"])
        button_layout.addWidget(self.chkFontObfuscation)

        self.chkRemoveWatermarks = QtGui.QCheckBox(_("Remove watermarks"))
        self.chkRemoveWatermarks.setToolTip("Tries to remove watermarks from files")
        self.chkRemoveWatermarks.setChecked(self.tempdedrmprefs["remove_watermarks"])
        button_layout.addWidget(self.chkRemoveWatermarks)

        self.resize(self.sizeHint())

    def kindle_serials(self):
        d = ManageKeysDialog(self,"EInk Kindle Serial Number",self.tempdedrmprefs['serials'], AddSerialDialog)
        d.exec_()

    def kindle_android(self):
        d = ManageKeysDialog(self,"Kindle for Android Key",self.tempdedrmprefs['androidkeys'], AddAndroidDialog, 'k4a')
        d.exec_()

    def kindle_keys(self):
        if isosx or iswindows:
            d = ManageKeysDialog(self,"Kindle for Mac and PC Key",self.tempdedrmprefs['kindlekeys'], AddKindleDialog, 'k4i')
        else:
            # linux
            d = ManageKeysDialog(self,"Kindle for Mac and PC Key",self.tempdedrmprefs['kindlekeys'], AddKindleDialog, 'k4i', self.tempdedrmprefs['kindlewineprefix'])
        d.exec_()
        self.tempdedrmprefs['kindlewineprefix'] = d.getwineprefix()

    def adept_keys(self):
        if isosx or iswindows:
            d = ManageKeysDialog(self,"Adobe Digital Editions Key",self.tempdedrmprefs['adeptkeys'], AddAdeptDialog, 'der')
        else:
            # linux
            d = ManageKeysDialog(self,"Adobe Digital Editions Key",self.tempdedrmprefs['adeptkeys'], AddAdeptDialog, 'der', self.tempdedrmprefs['adobewineprefix'])
        d.exec_()
        self.tempdedrmprefs['adobewineprefix'] = d.getwineprefix()

    def mobi_keys(self):
        d = ManageKeysDialog(self,"Mobipocket PID",self.tempdedrmprefs['pids'], AddPIDDialog)
        d.exec_()

    def bandn_keys(self):
        d = ManageKeysDialog(self,"ADE PassHash Key",self.tempdedrmprefs['bandnkeys'], AddBandNKeyDialog, 'b64')
        d.exec_()

    def ereader_keys(self):
        d = ManageKeysDialog(self,"eReader Key",self.tempdedrmprefs['ereaderkeys'], AddEReaderDialog, 'b63')
        d.exec_()

    def readium_lcp_keys(self):
        d = ManageKeysDialog(self,"Readium LCP passphrase",self.tempdedrmprefs['lcp_passphrases'], AddLCPKeyDialog)
        d.exec_()

    def pdf_passphrases(self):
        d = ManageKeysDialog(self,"PDF passphrase",self.tempdedrmprefs['adobe_pdf_passphrases'], AddPDFPassDialog)
        d.exec_()

    def help_link_activated(self, url):
        def get_help_file_resource():
            # Copy the HTML helpfile to the plugin directory each time the
            # link is clicked in case the helpfile is updated in newer plugins.
            file_path = os.path.join(config_dir, "plugins", "DeDRM", "help", help_file_name)
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
        self.dedrmprefs.set('deobfuscate_fonts', self.chkFontObfuscation.isChecked())
        self.dedrmprefs.set('remove_watermarks', self.chkRemoveWatermarks.isChecked())
        self.dedrmprefs.set('lcp_passphrases', self.tempdedrmprefs['lcp_passphrases'])
        self.dedrmprefs.set('adobe_pdf_passphrases', self.tempdedrmprefs['adobe_pdf_passphrases'])
        self.dedrmprefs.writeprefs()

    def load_resource(self, name):
        with ZipFile(self.plugin_path, 'r') as zf:
            if name in zf.namelist():
                return zf.read(name).decode('utf-8')
        return ""



class ManageKeysDialog(QDialog):
    def __init__(self, parent, key_type_name, plugin_keys, create_key, keyfile_ext = "", wineprefix = None):
        QDialog.__init__(self,parent)
        self.parent = parent
        self.key_type_name = key_type_name
        self.plugin_keys = plugin_keys
        self.create_key = create_key
        self.keyfile_ext = keyfile_ext
        self.import_key = (keyfile_ext != "")
        self.binary_file = (keyfile_ext == "der")
        self.json_file = (keyfile_ext == "k4i")
        self.android_file = (keyfile_ext == "k4a")
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

        keys_group_box = QGroupBox(_("{0}s".format(self.key_type_name)), self)
        layout.addWidget(keys_group_box)
        keys_group_box_layout = QHBoxLayout()
        keys_group_box.setLayout(keys_group_box_layout)

        self.listy = QListWidget(self)
        self.listy.setToolTip("{0}s that will be used to decrypt ebooks".format(self.key_type_name))
        self.listy.setSelectionMode(QAbstractItemView.SingleSelection)
        self.populate_list()
        keys_group_box_layout.addWidget(self.listy)

        button_layout = QVBoxLayout()
        keys_group_box_layout.addLayout(button_layout)
        self._add_key_button = QtGui.QToolButton(self)
        self._add_key_button.setIcon(QIcon(I('plus.png')))
        self._add_key_button.setToolTip("Create new {0}".format(self.key_type_name))
        self._add_key_button.clicked.connect(self.add_key)
        button_layout.addWidget(self._add_key_button)

        self._delete_key_button = QtGui.QToolButton(self)
        self._delete_key_button.setToolTip(_("Delete highlighted key"))
        self._delete_key_button.setIcon(QIcon(I('list_remove.png')))
        self._delete_key_button.clicked.connect(self.delete_key)
        button_layout.addWidget(self._delete_key_button)

        if type(self.plugin_keys) == dict and self.import_key:
            self._rename_key_button = QtGui.QToolButton(self)
            self._rename_key_button.setToolTip(_("Rename highlighted key"))
            self._rename_key_button.setIcon(QIcon(I('edit-select-all.png')))
            self._rename_key_button.clicked.connect(self.rename_key)
            button_layout.addWidget(self._rename_key_button)

            self.export_key_button = QtGui.QToolButton(self)
            self.export_key_button.setToolTip("Save highlighted key to a .{0} file".format(self.keyfile_ext))
            self.export_key_button.setIcon(QIcon(I('save.png')))
            self.export_key_button.clicked.connect(self.export_key)
            button_layout.addWidget(self.export_key_button)
        try: 
            # QT 6
            spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Policy.Minimum, QtGui.QSizePolicy.Policy.Expanding)
        except AttributeError:
            # QT 5
            spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)

        button_layout.addItem(spacerItem)

        if self.wineprefix is not None:
            layout.addSpacing(5)
            wineprefix_layout = QHBoxLayout()
            layout.addLayout(wineprefix_layout)
            wineprefix_layout.setAlignment(Qt.AlignCenter)
            self.wp_label = QLabel("WINEPREFIX:")
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
            self.migrate_btn = QPushButton("Import Existing Keyfiles", self)
            self.migrate_btn.setToolTip("Import *.{0} files (created using other tools).".format(self.keyfile_ext))
            self.migrate_btn.clicked.connect(self.migrate_wrapper)
            migrate_layout.addWidget(self.migrate_btn)
        migrate_layout.addStretch()
        self.button_box = QDialogButtonBox(QDialogButtonBox.Close)
        self.button_box.rejected.connect(self.close)
        migrate_layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    def getwineprefix(self):
        if self.wineprefix is not None:
            return str(self.wp_lineedit.text()).strip()
        return ""

    def populate_list(self):
        if type(self.plugin_keys) == dict:
            for key in self.plugin_keys.keys():
                self.listy.addItem(QListWidgetItem(key))
        else:
            for key in self.plugin_keys:
                self.listy.addItem(QListWidgetItem(key))

        self.listy.setMinimumWidth(self.listy.sizeHintForColumn(0) + 20)

    def add_key(self):
        d = self.create_key(self)
        d.exec_()

        if d.result() != d.Accepted:
            # New key generation cancelled.
            return

        if hasattr(d, "k_key_list") and d.k_key_list is not None: 
            # importing multiple keys
            idx = -1
            dup_key_count = 0
            added_key_count = 0
            
            while True:
                idx = idx + 1
                try: 
                    new_key_value = d.k_key_list[idx]
                except:
                    break

                if type(self.plugin_keys) == dict:
                    if new_key_value in self.plugin_keys.values():
                        dup_key_count = dup_key_count + 1
                        continue
                    self.plugin_keys[d.k_name_list[idx]] = new_key_value
                    added_key_count = added_key_count + 1
                else:
                    if new_key_value in self.plugin_keys:
                        dup_key_count = dup_key_count + 1
                        continue
                    self.plugin_keys.append(new_key_value)
                    added_key_count = added_key_count + 1
                
            if (added_key_count > 0 or dup_key_count > 0):
                if (added_key_count == 0):
                    info_dialog(None, "{0} {1}: Adding {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                        "Skipped adding {0} duplicate / existing keys.".format(dup_key_count), show=True, show_copy_button=False)
                elif (dup_key_count == 0):
                    info_dialog(None, "{0} {1}: Adding {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                        "Added {0} new keys.".format(added_key_count), show=True, show_copy_button=False)
                else:
                    info_dialog(None, "{0} {1}: Adding {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                        "Added {0} new keys, skipped adding {1} existing keys.".format(added_key_count, dup_key_count), show=True, show_copy_button=False)

        else:
            # Import single key
            new_key_value = d.key_value
            if type(self.plugin_keys) == dict:
                if new_key_value in self.plugin_keys.values():
                    old_key_name = [name for name, value in self.plugin_keys.items() if value == new_key_value][0]
                    info_dialog(None, "{0} {1}: Duplicate {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                                        "The new {1} is the same as the existing {1} named <strong>{0}</strong> and has not been added.".format(old_key_name,self.key_type_name), show=True)
                    return
                self.plugin_keys[d.key_name] = new_key_value
            else:
                if new_key_value in self.plugin_keys:
                    info_dialog(None, "{0} {1}: Duplicate {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                                        "This {0} is already in the list of {0}s has not been added.".format(self.key_type_name), show=True)
                    return

                self.plugin_keys.append(d.key_value)

        self.listy.clear()
        self.populate_list()

    def rename_key(self):
        if not self.listy.currentItem():
            errmsg = "No {0} selected to rename. Highlight a keyfile first.".format(self.key_type_name)
            r = error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
            return

        d = RenameKeyDialog(self)
        d.exec_()

        if d.result() != d.Accepted:
            # rename cancelled or moot.
            return
        keyname = str(self.listy.currentItem().text())
        if not question_dialog(self, "{0} {1}: Confirm Rename".format(PLUGIN_NAME, PLUGIN_VERSION), "Do you really want to rename the {2} named <strong>{0}</strong> to <strong>{1}</strong>?".format(keyname,d.key_name,self.key_type_name), show_copy_button=False, default_yes=False):
            return
        self.plugin_keys[d.key_name] = self.plugin_keys[keyname]
        del self.plugin_keys[keyname]

        self.listy.clear()
        self.populate_list()

    def delete_key(self):
        if not self.listy.currentItem():
            return
        keyname = str(self.listy.currentItem().text())
        if not question_dialog(self, "{0} {1}: Confirm Delete".format(PLUGIN_NAME, PLUGIN_VERSION), "Do you really want to delete the {1} <strong>{0}</strong>?".format(keyname, self.key_type_name), show_copy_button=False, default_yes=False):
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
            help_file_name = "{0}_{1}_Help.htm".format(PLUGIN_NAME, self.key_type_name)
            file_path = os.path.join(config_dir, "plugins", "DeDRM", "help", help_file_name)
            with open(file_path,'w') as f:
                f.write(self.parent.load_resource(help_file_name))
            return file_path
        url = 'file:///' + get_help_file_resource()
        open_url(QUrl(url))

    def migrate_files(self):
        unique_dlg_name = PLUGIN_NAME + "import {0} keys".format(self.key_type_name).replace(' ', '_') #takes care of automatically remembering last directory
        caption = "Select {0} files to import".format(self.key_type_name)
        filters = [("{0} files".format(self.key_type_name), [self.keyfile_ext])]
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
                    new_key_value = codecs.encode(new_key_value,'hex')
                elif self.json_file:
                    new_key_value = json.loads(new_key_value)
                elif self.android_file:
                    # convert to list of the keys in the string
                    new_key_value = new_key_value.splitlines()
                match = False
                for key in self.plugin_keys.keys():
                    if uStrCmp(new_key_name, key, True):
                        skipped += 1
                        msg = "A key with the name <strong>{0}</strong> already exists!\nSkipping key file  <strong>{1}</strong>.\nRename the existing key and import again".format(new_key_name,filename)
                        inf = info_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                _(msg), show_copy_button=False, show=True)
                        match = True
                        break
                if not match:
                    if new_key_value in self.plugin_keys.values():
                        old_key_name = [name for name, value in self.plugin_keys.items() if value == new_key_value][0]
                        skipped += 1
                        info_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                            "The key in file {0} is the same as the existing key <strong>{1}</strong> and has been skipped.".format(filename,old_key_name), show_copy_button=False, show=True)
                    else:
                        counter += 1
                        self.plugin_keys[new_key_name] = new_key_value

            msg = ""
            if counter+skipped > 1:
                if counter > 0:
                    msg += "Imported <strong>{0:d}</strong> key {1}. ".format(counter, "file" if counter == 1 else "files")
                if skipped > 0:
                    msg += "Skipped <strong>{0:d}</strong> key {1}.".format(skipped, "file" if counter == 1 else "files")
                inf = info_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(msg), show_copy_button=False, show=True)
        return counter > 0

    def migrate_wrapper(self):
        if self.migrate_files():
            self.listy.clear()
            self.populate_list()

    def export_key(self):
        if not self.listy.currentItem():
            errmsg = "No keyfile selected to export. Highlight a keyfile first."
            r = error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
            return
        keyname = str(self.listy.currentItem().text())
        unique_dlg_name = PLUGIN_NAME + "export {0} keys".format(self.key_type_name).replace(' ', '_') #takes care of automatically remembering last directory
        caption = "Save {0} File as...".format(self.key_type_name)
        filters = [("{0} Files".format(self.key_type_name), ["{0}".format(self.keyfile_ext)])]
        defaultname = "{0}.{1}".format(keyname, self.keyfile_ext)
        filename = choose_save_file(self, unique_dlg_name,  caption, filters, all_files=False, initial_filename=defaultname)
        if filename:
            if self.binary_file:
                with open(filename, 'wb') as fname:
                    fname.write(codecs.decode(self.plugin_keys[keyname],'hex'))
            elif self.json_file:
                with open(filename, 'w') as fname:
                    fname.write(json.dumps(self.plugin_keys[keyname]))
            elif self.android_file:
                with open(filename, 'w') as fname:
                    for key in self.plugin_keys[keyname]:
                        fname.write(key)
                        fname.write('\n')
            else:
                with open(filename, 'w') as fname:
                    fname.write(self.plugin_keys[keyname])




class RenameKeyDialog(QDialog):
    def __init__(self, parent=None,):
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
        self.key_ledit.setToolTip("Enter a new name for this existing {0}.".format(parent.key_type_name))
        data_group_box_layout.addWidget(self.key_ledit)

        layout.addSpacing(20)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    def accept(self):
        if not str(self.key_ledit.text()) or str(self.key_ledit.text()).isspace():
            errmsg = "Key name field cannot be empty!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
        if len(self.key_ledit.text()) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
        if uStrCmp(self.key_ledit.text(), self.parent.listy.currentItem().text()):
                # Same exact name ... do nothing.
                return QDialog.reject(self)
        for k in self.parent.plugin_keys.keys():
            if (uStrCmp(self.key_ledit.text(), k, True) and
                        not uStrCmp(k, self.parent.listy.currentItem().text(), True)):
                errmsg = "The key name <strong>{0}</strong> is already being used.".format(self.key_ledit.text())
                return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION),
                                    _(errmsg), show=True, show_copy_button=False)
        QDialog.accept(self)

    @property
    def key_name(self):
        return str(self.key_ledit.text()).strip()


class AddBandNKeyDialog(QDialog):

    def update_form(self, idx):
        self.cbType.hide()

        if idx == 1:
            self.add_fields_for_passhash()
        elif idx == 2: 
            self.add_fields_for_b64_passhash()
        elif idx == 3: 
            self.add_fields_for_ade_passhash()
        elif idx == 4:
            self.add_fields_for_windows_nook()
        elif idx == 5:
            self.add_fields_for_android_nook()



    def add_fields_for_ade_passhash(self):

        self.ade_extr_group_box = QGroupBox("", self)
        ade_extr_group_box_layout = QVBoxLayout()
        self.ade_extr_group_box.setLayout(ade_extr_group_box_layout)

        self.layout.addWidget(self.ade_extr_group_box)

        ade_extr_group_box_layout.addWidget(QLabel("Click \"OK\" to try and dump PassHash data \nfrom Adobe Digital Editions. This works if\nyou've opened your PassHash books in ADE before.", self))

        self.button_box.hide()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_ade_dump_passhash)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.resize(self.sizeHint())


    def add_fields_for_android_nook(self):

        self.andr_nook_group_box = QGroupBox("", self)
        andr_nook_group_box_layout = QVBoxLayout()
        self.andr_nook_group_box.setLayout(andr_nook_group_box_layout)

        self.layout.addWidget(self.andr_nook_group_box)

        ph_key_name_group = QHBoxLayout()
        andr_nook_group_box_layout.addLayout(ph_key_name_group)
        ph_key_name_group.addWidget(QLabel("Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(_("<p>Enter an identifying name for this new key.</p>"))
        ph_key_name_group.addWidget(self.key_ledit)

        andr_nook_group_box_layout.addWidget(QLabel("Hidden in the Android application data is a " +
            "folder\nnamed '.adobe-digital-editions'. Please enter\nthe full path to that folder.", self))

        ph_path_group = QHBoxLayout()
        andr_nook_group_box_layout.addLayout(ph_path_group)
        ph_path_group.addWidget(QLabel("Path:", self))
        self.cc_ledit = QLineEdit("", self)
        self.cc_ledit.setToolTip(_("<p>Enter path to .adobe-digital-editions folder.</p>"))
        ph_path_group.addWidget(self.cc_ledit)

        self.button_box.hide()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_android_nook)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    def add_fields_for_windows_nook(self):

        self.win_nook_group_box = QGroupBox("", self)
        win_nook_group_box_layout = QVBoxLayout()
        self.win_nook_group_box.setLayout(win_nook_group_box_layout)

        self.layout.addWidget(self.win_nook_group_box)

        ph_key_name_group = QHBoxLayout()
        win_nook_group_box_layout.addLayout(ph_key_name_group)
        ph_key_name_group.addWidget(QLabel("Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(_("<p>Enter an identifying name for this new key.</p>"))
        ph_key_name_group.addWidget(self.key_ledit)

        self.button_box.hide()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_win_nook)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    def add_fields_for_b64_passhash(self):

        self.passhash_group_box = QGroupBox("", self)
        passhash_group_box_layout = QVBoxLayout()
        self.passhash_group_box.setLayout(passhash_group_box_layout)

        self.layout.addWidget(self.passhash_group_box)

        ph_key_name_group = QHBoxLayout()
        passhash_group_box_layout.addLayout(ph_key_name_group)
        ph_key_name_group.addWidget(QLabel("Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(_("<p>Enter an identifying name for this new key.</p>" +
                                "<p>It should be something that will help you remember " +
                                "what personal information was used to create it."))
        ph_key_name_group.addWidget(self.key_ledit)

        ph_name_group = QHBoxLayout()
        passhash_group_box_layout.addLayout(ph_name_group)
        ph_name_group.addWidget(QLabel("Base64 key string:", self))
        self.cc_ledit = QLineEdit("", self)
        self.cc_ledit.setToolTip(_("<p>Enter the Base64 key string</p>"))
        ph_name_group.addWidget(self.cc_ledit)

        self.button_box.hide()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_b64_passhash)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.resize(self.sizeHint())


    def add_fields_for_passhash(self):

        self.passhash_group_box = QGroupBox("", self)
        passhash_group_box_layout = QVBoxLayout()
        self.passhash_group_box.setLayout(passhash_group_box_layout)

        self.layout.addWidget(self.passhash_group_box)

        ph_key_name_group = QHBoxLayout()
        passhash_group_box_layout.addLayout(ph_key_name_group)
        ph_key_name_group.addWidget(QLabel("Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(_("<p>Enter an identifying name for this new key.</p>" +
                                "<p>It should be something that will help you remember " +
                                "what personal information was used to create it."))
        ph_key_name_group.addWidget(self.key_ledit)

        ph_name_group = QHBoxLayout()
        passhash_group_box_layout.addLayout(ph_name_group)
        ph_name_group.addWidget(QLabel("Username:", self))
        self.name_ledit = QLineEdit("", self)
        self.name_ledit.setToolTip(_("<p>Enter the PassHash username</p>"))
        ph_name_group.addWidget(self.name_ledit)

        ph_pass_group = QHBoxLayout()
        passhash_group_box_layout.addLayout(ph_pass_group)
        ph_pass_group.addWidget(QLabel("Password:", self))
        self.cc_ledit = QLineEdit("", self)
        self.cc_ledit.setToolTip(_("<p>Enter the PassHash password</p>"))
        ph_pass_group.addWidget(self.cc_ledit)

        self.button_box.hide()
        
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept_passhash)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.resize(self.sizeHint())



    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Create New PassHash (B&N) Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        self.layout = QVBoxLayout(self)
        self.setLayout(self.layout)

        self.cbType = QComboBox()
        self.cbType.addItem("--- Select key type ---")
        self.cbType.addItem("Adobe PassHash username & password")
        self.cbType.addItem("Base64-encoded PassHash key string")
        self.cbType.addItem("Extract passhashes from Adobe Digital Editions")
        self.cbType.addItem("Extract key from Nook Windows application")
        self.cbType.addItem("Extract key from Nook Android application")
        self.cbType.currentIndexChanged.connect(lambda: self.update_form(self.cbType.currentIndex()))
        self.layout.addWidget(self.cbType)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Cancel)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        try: 
            return str(self.key_ledit.text()).strip()
        except:
            return self.result_data_name

    @property
    def key_value(self):
        return self.result_data

    @property
    def user_name(self):
        return str(self.name_ledit.text()).strip().lower().replace(' ','')

    @property
    def cc_number(self):
        return str(self.cc_ledit.text()).strip()


    @property
    def k_name_list(self):
        # If the plugin supports returning multiple keys, return a list of names.
        if self.k_full_name_list is not None and self.k_full_key_list is not None:
            return self.k_full_name_list
        return None

    @property
    def k_key_list(self):
        # If the plugin supports returning multiple keys, return a list of keys.
        if self.k_full_name_list is not None and self.k_full_key_list is not None:
            return self.k_full_key_list
        return None



    def accept_android_nook(self):
        
        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        path_to_ade_data = self.cc_number

        if (os.path.isfile(os.path.join(path_to_ade_data, ".adobe-digital-editions", "activation.xml"))):
            path_to_ade_data = os.path.join(path_to_ade_data, ".adobe-digital-editions")
        elif (os.path.isfile(os.path.join(path_to_ade_data, "activation.xml"))):
            pass
        else: 
            errmsg = "This isn't the correct path, or the data is invalid."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        from ignoblekeyAndroid import dump_keys
        store_result = dump_keys(path_to_ade_data)

        if len(store_result) == 0:
            errmsg = "Failed to extract keys. Is this the correct folder?"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        if len(store_result) == 1:
            # Found exactly one key. Store it with that name.
            self.result_data = store_result[0]
            QDialog.accept(self)
            return

        # Found multiple keys
        keys = []
        names = []
        idx = 1
        for key in store_result: 
            keys.append(key)
            names.append(self.key_name + "_" + str(idx))
            idx = idx + 1

        self.k_full_name_list = names
        self.k_full_key_list = keys
        QDialog.accept(self)
        return


    def accept_ade_dump_passhash(self):
        
        try: 
            from adobekey_get_passhash import passhash_keys
            keys, names = passhash_keys()
        except:
            errmsg = "Failed to grab PassHash keys from ADE."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        # Take the first new key we found.

        idx = -1
        new_keys = []
        new_names = []
        for key in keys:
            idx = idx + 1
            if key in self.parent.plugin_keys.values():
                continue
        
            new_keys.append(key)
            new_names.append(names[idx])

        if len(new_keys) == 0:
            # Okay, we didn't find anything. How do we get rid of the window?
            errmsg = "Didn't find any PassHash keys in ADE."
            error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
            QDialog.reject(self)
            return

        # Add new keys to list.
        self.k_full_name_list = new_names
        self.k_full_key_list = new_keys
        QDialog.accept(self)
        return



    def accept_win_nook(self):

        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        try: 
            from ignoblekeyWindowsStore import dump_keys
            store_result = dump_keys(False)
        except:
            errmsg = "Failed to import from Nook Microsoft Store app."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        try: 
            # Try the Nook Study app
            from ignoblekeyNookStudy import nookkeys
            study_result = nookkeys()
        except:
            errmsg = "Failed to import from Nook Study app."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        # Add all found keys to a list
        keys = []
        names = []
        idx = 1
        for key in store_result: 
            keys.append(key)
            names.append(self.key_name + "_nookStore_" + str(idx))
            idx = idx + 1
        idx = 1
        for key in study_result: 
            keys.append(key)
            names.append(self.key_name + "_nookStudy_" + str(idx))
            idx = idx + 1

        if len(keys) > 0:
            self.k_full_name_list = names
            self.k_full_key_list = keys
            QDialog.accept(self)
            return


        # Okay, we didn't find anything. 
        errmsg = "Didn't find any Nook keys in the Windows app."
        error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.reject(self)


    def accept_b64_passhash(self):
        if len(self.key_name) == 0 or len(self.cc_number) == 0 or self.key_name.isspace() or self.cc_number.isspace():
            errmsg = "All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        
        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        try: 
            x = base64.b64decode(self.cc_number)
        except: 
            errmsg = "Key data is no valid base64 string!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)


        self.result_data = self.cc_number
        QDialog.accept(self)
    
    def accept_passhash(self):
        if len(self.key_name) == 0 or len(self.user_name) == 0 or len(self.cc_number) == 0 or self.key_name.isspace() or self.user_name.isspace() or self.cc_number.isspace():
            errmsg = "All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        try: 
            from ignoblekeyGenPassHash import generate_key
            self.result_data = generate_key(self.user_name, self.cc_number)
        except: 
            errmsg = "Key generation failed."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        
        if len(self.result_data) == 0:
            errmsg = "Key generation failed."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)

        QDialog.accept(self)

        

class AddEReaderDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Create New eReader Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox("", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel("Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip("<p>Enter an identifying name for this new key.\nIt should be something that will help you remember what personal information was used to create it.")
        key_group.addWidget(self.key_ledit)

        name_group = QHBoxLayout()
        data_group_box_layout.addLayout(name_group)
        name_group.addWidget(QLabel("Your Name:", self))
        self.name_ledit = QLineEdit("", self)
        self.name_ledit.setToolTip("Enter the name for this eReader key, usually the name on your credit card.\nIt will only be used to generate this one-time key and won\'t be stored anywhere in calibre or on your computer.\n(ex: Mr Jonathan Q Smith)")
        name_group.addWidget(self.name_ledit)
        name_disclaimer_label = QLabel(_("(Will not be saved in configuration data)"), self)
        name_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(name_disclaimer_label)

        ccn_group = QHBoxLayout()
        data_group_box_layout.addLayout(ccn_group)
        ccn_group.addWidget(QLabel("Credit Card#:", self))
        self.cc_ledit = QLineEdit("", self)
        self.cc_ledit.setToolTip("<p>Enter the last 8 digits of credit card number for this eReader key.\nThey will only be used to generate this one-time key and won\'t be stored anywhere in calibre or on your computer.")
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
        return str(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        from erdr2pml import getuser_key as generate_ereader_key
        return codecs.encode(generate_ereader_key(self.user_name, self.cc_number),'hex')

    @property
    def user_name(self):
        return str(self.name_ledit.text()).strip().lower().replace(' ','')

    @property
    def cc_number(self):
        return str(self.cc_ledit.text()).strip().replace(' ', '').replace('-','')


    def accept(self):
        if len(self.key_name) == 0 or len(self.user_name) == 0 or len(self.cc_number) == 0 or self.key_name.isspace() or self.user_name.isspace() or self.cc_number.isspace():
            errmsg = "All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if not self.cc_number.isdigit():
            errmsg = "Numbers only in the credit card number field!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddAdeptDialog():
    # We don't actually need to show a dialog, but the wrapper class is expecting a QDialog here.
    # Emulate enough methods and parameters so that that works ...

    def exec_(self):
        return

    def result(self): 
        return True

    @property
    def Accepted(self):
        return True

    def __init__(self, parent=None,):
        
        self.parent = parent
        self.new_keys = []
        self.new_names = []

        try:
            if iswindows or isosx:
                from adobekey import adeptkeys

                defaultkeys, defaultnames = adeptkeys()
            else:  # linux
                from wineutils import WineGetKeys

                scriptpath = os.path.join(parent.parent.alfdir,"adobekey.py")
                defaultkeys, defaultnames = WineGetKeys(scriptpath, ".der",parent.getwineprefix())

            if sys.version_info[0] < 3:
                # Python2
                import itertools
                zip_function = itertools.izip
            else:
                # Python3
                zip_function = zip

            for key, name in zip_function(defaultkeys, defaultnames):
                key = codecs.encode(key,'hex').decode("latin-1")
                if key in self.parent.plugin_keys.values():
                    print("Found key '{0}' in ADE - already present, skipping.".format(name))
                else:
                    self.new_keys.append(key)
                    self.new_names.append(name)
        except:
            print("Exception while checking for ADE keys")
            traceback.print_exc()

        
        # Check for keys in the DeACSM plugin
        try: 
            key, name = checkForDeACSMkeys()

            if key is not None: 
                key = codecs.encode(key,'hex').decode("latin-1")
                if key in self.parent.plugin_keys.values():
                    print("Found key '{0}' in DeACSM - already present, skipping.".format(name))
                else: 
                    # Found new key, add that.
                    self.new_keys.append(key)
                    self.new_names.append(name)
        except: 
            print("Exception while checking for DeACSM keys")
            traceback.print_exc()

        # Just in case ADE and DeACSM are activated with the same account, 
        # check the new_keys list for duplicates and remove them, if they exist.

        new_keys_2 = []
        new_names_2 = []
        i = 0
        while True: 
            if i >= len(self.new_keys):
                break
            if not self.new_keys[i] in new_keys_2:
                new_keys_2.append(self.new_keys[i])
                new_names_2.append(self.new_names[i])
            i = i + 1
        
        self.k_full_key_list = new_keys_2
        self.k_full_name_list = new_names_2


    @property
    def key_name(self):
        return str(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return codecs.encode(self.new_keys[0],'hex').decode("latin-1")

    
    @property
    def k_name_list(self):
        # If the plugin supports returning multiple keys, return a list of names.
        if self.k_full_name_list is not None and self.k_full_key_list is not None:
            return self.k_full_name_list
        return None

    @property
    def k_key_list(self):
        # If the plugin supports returning multiple keys, return a list of keys.
        if self.k_full_name_list is not None and self.k_full_key_list is not None:
            return self.k_full_key_list
        return None


class AddKindleDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Getting Default Kindle for Mac/PC Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        try:
            if iswindows or isosx:
                from kindlekey import kindlekeys

                defaultkeys = kindlekeys()
            else: # linux
                from wineutils import WineGetKeys

                scriptpath = os.path.join(parent.parent.alfdir,"kindlekey.py")
                defaultkeys, defaultnames = WineGetKeys(scriptpath, ".k4i",parent.getwineprefix())

            self.default_key = defaultkeys[0]
        except:
            traceback.print_exc()
            self.default_key = ""

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        if len(self.default_key)>0:
            data_group_box = QGroupBox("", self)
            layout.addWidget(data_group_box)
            data_group_box_layout = QVBoxLayout()
            data_group_box.setLayout(data_group_box_layout)

            key_group = QHBoxLayout()
            data_group_box_layout.addLayout(key_group)
            key_group.addWidget(QLabel("Unique Key Name:", self))
            self.key_ledit = QLineEdit("default_key_" + str(int(time.time())), self)
            self.key_ledit.setToolTip("<p>Enter an identifying name for the current default Kindle for Mac/PC key.")
            key_group.addWidget(self.key_ledit)

            self.button_box.accepted.connect(self.accept)
        else:
            default_key_error = QLabel("The default encryption key for Kindle for Mac/PC could not be found.", self)
            default_key_error.setAlignment(Qt.AlignHCenter)
            layout.addWidget(default_key_error)

            # if no default, both buttons do the same
            self.button_box.accepted.connect(self.reject)

        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return str(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return self.default_key


    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = "All fields are required!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddSerialDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Add New EInk Kindle Serial Number".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox("", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel("EInk Kindle Serial Number:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip("Enter an eInk Kindle serial number. EInk Kindle serial numbers are 16 characters long and usually start with a 'B' or a '9'. Kindle Serial Numbers are case-sensitive, so be sure to enter the upper and lower case letters unchanged.")
        key_group.addWidget(self.key_ledit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return str(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return str(self.key_ledit.text()).replace(' ', '').replace('\r', '').replace('\n', '').replace('\t', '')

    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = "Please enter an eInk Kindle Serial Number or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 16:
            errmsg = "EInk Kindle Serial Numbers must be 16 characters long. This is {0:d} characters long.".format(len(self.key_name))
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddAndroidDialog(QDialog):
    def __init__(self, parent=None,):

        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Add new Kindle for Android Key".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        data_group_box = QGroupBox("", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        file_group = QHBoxLayout()
        data_group_box_layout.addLayout(file_group)
        add_btn = QPushButton("Choose Backup File", self)
        add_btn.setToolTip("Import Kindle for Android backup file.")
        add_btn.clicked.connect(self.get_android_file)
        file_group.addWidget(add_btn)
        self.selected_file_name = QLabel("",self)
        self.selected_file_name.setAlignment(Qt.AlignHCenter)
        file_group.addWidget(self.selected_file_name)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel("Unique Key Name:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip("<p>Enter an identifying name for the Android for Kindle key.")
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
        return str(self.key_ledit.text()).strip()

    @property
    def file_name(self):
        return str(self.selected_file_name.text()).strip()

    @property
    def key_value(self):
        return self.serials_from_file

    def get_android_file(self):
        unique_dlg_name = PLUGIN_NAME + "Import Kindle for Android backup file" #takes care of automatically remembering last directory
        caption = "Select Kindle for Android backup file to add"
        filters = [("Kindle for Android backup files", ['db','ab','xml'])]
        files = choose_files(self, unique_dlg_name, caption, filters, all_files=False)
        self.serials_from_file = []
        file_name = ""
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
            errmsg = "Please choose a Kindle for Android backup file."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = "Please enter a key name."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) < 4:
            errmsg = "Key name must be at <i>least</i> 4 characters long!"
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)

class AddPIDDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Add New Mobipocket PID".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox("", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel("PID:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip("Enter a Mobipocket PID. Mobipocket PIDs are 8 or 10 characters long. Mobipocket PIDs are case-sensitive, so be sure to enter the upper and lower case letters unchanged.")
        key_group.addWidget(self.key_ledit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return str(self.key_ledit.text()).strip()

    @property
    def key_value(self):
        return str(self.key_ledit.text()).strip()

    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = "Please enter a Mobipocket PID or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 8 and len(self.key_name) != 10:
            errmsg = "Mobipocket PIDs must be 8 or 10 characters long. This is {0:d} characters long.".format(len(self.key_name))
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


class AddLCPKeyDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Add new Readium LCP passphrase".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox("", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel("Readium LCP passphrase:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip("Enter your Readium LCP passphrase")
        key_group.addWidget(self.key_ledit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return None

    @property
    def key_value(self):
        return str(self.key_ledit.text())

    def accept(self):
        if len(self.key_value) == 0 or self.key_value.isspace():
            errmsg = "Please enter your LCP passphrase or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)

class AddPDFPassDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle("{0} {1}: Add new PDF passphrase".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox("", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel("PDF password:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip("Enter the PDF file password.")
        key_group.addWidget(self.key_ledit)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return None

    @property
    def key_value(self):
        return str(self.key_ledit.text())

    def accept(self):
        if len(self.key_value) == 0 or self.key_value.isspace():
            errmsg = "Please enter a PDF password or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)
