#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import with_statement

__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib

# PyQT4 modules (part of calibre).
from PyQt4.Qt import (Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QPushButton, QListWidget, QListWidgetItem,
                      QAbstractItemView, QIcon, QDialog, QUrl, QString)
from PyQt4 import QtGui

import zipfile
from zipfile import ZipFile

# calibre modules and constants.
from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url,
                            choose_dir, choose_files)
from calibre.utils.config import dynamic, config_dir, JSONConfig
from calibre.constants import iswindows, isosx

# modules from this plugin's zipfile.
from calibre_plugins.dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION
from calibre_plugins.dedrm.__init__ import RESOURCE_NAME as help_file_name
from calibre_plugins.dedrm.utilities import (uStrCmp, DETAILED_MESSAGE)

import calibre_plugins.dedrm.dialogs as dialogs

JSON_NAME = PLUGIN_NAME.strip().lower().replace(' ', '_')
JSON_PATH = os.path.join(u"plugins", JSON_NAME + '.json')

IGNOBLEPLUGINNAME = "Ignoble Epub DeDRM"
EREADERPLUGINNAME = "eReader PDB 2 PML"
OLDKINDLEPLUGINNAME = "K4PC, K4Mac, Kindle Mobi and Topaz DeDRM"

# This is where all preferences for this plugin will be stored
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
dedrmprefs = JSONConfig(JSON_PATH)

# get prefs from older tools
kindleprefs = JSONConfig(os.path.join(u"plugins", u"K4MobiDeDRM"))
ignobleprefs = JSONConfig(os.path.join(u"plugins", u"ignoble_epub_dedrm"))

# Set defaults for the prefs
dedrmprefs.defaults['configured'] = False
dedrmprefs.defaults['bandnkeys'] = {}
dedrmprefs.defaults['adeptkeys'] = {}
dedrmprefs.defaults['ereaderkeys'] = {}
dedrmprefs.defaults['kindlekeys'] = {}
dedrmprefs.defaults['pids'] = []
dedrmprefs.defaults['serials'] = []


class ConfigWidget(QWidget):
    def __init__(self, plugin_path):
        QWidget.__init__(self)

        self.plugin_path = plugin_path

        # get copy of the prefs from the file
        # Otherwise we seem to get a persistent local copy.
        self.dedrmprefs = JSONConfig(JSON_PATH)

        self.tempdedrmprefs = {}
        self.tempdedrmprefs['bandnkeys'] = self.dedrmprefs['bandnkeys'].copy()
        self.tempdedrmprefs['adeptkeys'] = self.dedrmprefs['adeptkeys'].copy()
        self.tempdedrmprefs['ereaderkeys'] = self.dedrmprefs['ereaderkeys'].copy()
        self.tempdedrmprefs['kindlekeys'] = self.dedrmprefs['kindlekeys'].copy()
        self.tempdedrmprefs['pids'] = list(self.dedrmprefs['pids'])
        self.tempdedrmprefs['serials'] = list(self.dedrmprefs['serials'])

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
        button_layout.addWidget(self.bandn_button)
        button_layout.addWidget(self.mobi_button)
        button_layout.addWidget(self.ereader_button)
        button_layout.addWidget(self.adept_button)
        button_layout.addWidget(self.kindle_key_button)

        self.resize(self.sizeHint())

    def kindle_serials(self):
        d = dialogs.ManageKeysDialog(self,u"EInk Kindle Serial Number",self.tempdedrmprefs['serials'], dialogs.AddSerialDialog)
        d.exec_()

    def kindle_keys(self):
        d = dialogs.ManageKeysDialog(self,u"Kindle for Mac and PC Key",self.tempdedrmprefs['kindlekeys'], dialogs.AddKindleDialog, 'k4i')
        d.exec_()

    def adept_keys(self):
        d = dialogs.ManageKeysDialog(self,u"Adobe Digital Editions Key",self.tempdedrmprefs['adeptkeys'], dialogs.AddAdeptDialog, 'der')
        d.exec_()

    def mobi_keys(self):
        d = dialogs.ManageKeysDialog(self,u"Mobipocket PID",self.tempdedrmprefs['pids'], dialogs.AddPIDDialog)
        d.exec_()

    def bandn_keys(self):
        d = dialogs.ManageKeysDialog(self,u"Barnes and Noble Key",self.tempdedrmprefs['bandnkeys'], dialogs.AddBandNKeyDialog, 'b64')
        d.exec_()

    def ereader_keys(self):
        d = dialogs.ManageKeysDialog(self,u"eReader Key",self.tempdedrmprefs['ereaderkeys'], dialogs.AddEReaderDialog, 'b63')
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
        self.dedrmprefs['bandnkeys'] = self.tempdedrmprefs['bandnkeys']
        self.dedrmprefs['adeptkeys'] = self.tempdedrmprefs['adeptkeys']
        self.dedrmprefs['ereaderkeys'] = self.tempdedrmprefs['ereaderkeys']
        self.dedrmprefs['kindlekeys'] = self.tempdedrmprefs['kindlekeys']
        self.dedrmprefs['pids'] = self.tempdedrmprefs['pids']
        self.dedrmprefs['serials'] = self.tempdedrmprefs['serials']
        self.dedrmprefs['configured'] = True

    def load_resource(self, name):
        with ZipFile(self.plugin_path, 'r') as zf:
            if name in zf.namelist():
                return zf.read(name)
        return ""

def writeprefs(value = True):
    dedrmprefs['configured'] = value

def addnamedvaluetoprefs(prefkind, keyname, keyvalue):
    try:
        if keyvalue not in dedrmprefs[prefkind].values():
            # ensure that the keyname is unique
            # by adding a number (starting with 2) to the name if it is not
            namecount = 1
            newname = keyname
            while newname in dedrmprefs[prefkind]:
                namecount += 1
                newname = "{0:s}_{1:d}".format(keyname,namecount)
            # add to the preferences
            dedrmprefs[prefkind][newname] = keyvalue
            return (True, newname)
    except:
        pass
    return (False, keyname)

def addvaluetoprefs(prefkind, prefsvalue):
    # ensure the keyvalue isn't already in the preferences
    if prefsvalue not in dedrmprefs[prefkind]:
        dedrmprefs[prefkind].append(prefsvalue)
        return True
    return False

def convertprefs(always = False):

    def parseIgnobleString(keystuff):
        import calibre_plugins.dedrm.ignoblekeygen as bandn
        userkeys = {}
        ar = keystuff.split(':')
        for i, keystring in enumerate(ar):
            try:
                name, ccn = keystring.split(',')
                # Generate Barnes & Noble EPUB user key from name and credit card number.
                keyname = u"{0}_{1}_{2:d}".format(name.strip(),ccn.strip()[-4:],i+1)
                keyvalue = bandn.generate_key(name, ccn)
                if keyvalue not in userkeys.values():
                    while keyname in dedrmprefs['bandnkeys']:
                        keyname = keyname + keyname[-1]
                    userkeys[keyname] = keyvalue
            except Exception, e:
                print e.args[0]
                pass
        return userkeys

    def parseeReaderString(keystuff):
        import calibre_plugins.dedrm.erdr2pml as ereader
        userkeys = {}
        ar = keystuff.split(':')
        for i, keystring in enumerate(ar):
            try:
                name, cc = keystring.split(',')
                # Generate eReader user key from name and credit card number.
                keyname = u"{0}_{1}_{2:d}".format(name.strip(),cc.strip()[-4:],i+1)
                keyvalue = ereader.getuser_key(name,cc).encode('hex')
                if keyvalue not in userkeys.values():
                    while keyname in dedrmprefs['ereaderkeys']:
                        keyname = keyname + keyname[-1]
                    userkeys[keyname] = keyvalue
            except Exception, e:
                print e.args[0]
                pass
        return userkeys

    def parseKindleString(keystuff):
        pids = []
        serials = []
        ar = keystuff.split(',')
        for keystring in ar:
            keystring = str(keystring).strip().replace(" ","")
            if len(keystring) == 10 or len(keystring) == 8 and keystring not in pids:
                pids.append(keystring)
            elif len(keystring) == 16 and keystring[0] == 'B' and keystring not in serials:
                serials.append(keystring)
        return (pids,serials)

    def addConfigFiles(extension, prefskey, encoding = ''):
        # get any files with extension 'extension' in the config dir
        files = [f for f in os.listdir(config_dir) if f.endswith(extension)]
        try:
            priorkeycount = len(dedrmprefs[prefskey])
            for filename in files:
                fpath = os.path.join(config_dir, filename)
                key = os.path.splitext(filename)[0]
                value = open(fpath, 'rb').read()
                if encoding is not '':
                    value = value.encode(encoding)
                if value not in dedrmprefs[prefskey].values():
                    while key in dedrmprefs[prefskey]:
                        key = key+key[-1]
                    dedrmprefs[prefskey][key] = value
                #os.remove(fpath)
            return len(dedrmprefs[prefskey])-priorkeycount
        except IOError:
            return -1

    if (not always) and dedrmprefs['configured']:
        # We've already converted old preferences,
        # and we're not being forced to do it again, so just return
        return

    # initialise
    # we must actually set the prefs that are dictionaries and lists
    # to empty dictionaries and lists, otherwise we are unable to add to them
    # as then it just adds to the (memory only) dedrmprefs.defaults versions!
    if dedrmprefs['bandnkeys'] == {}:
        dedrmprefs['bandnkeys'] = {}
    if dedrmprefs['adeptkeys'] == {}:
        dedrmprefs['adeptkeys'] = {}
    if dedrmprefs['ereaderkeys'] == {}:
        dedrmprefs['ereaderkeys'] = {}
    if dedrmprefs['kindlekeys'] == {}:
        dedrmprefs['kindlekeys'] = {}
    if dedrmprefs['pids'] == []:
        dedrmprefs['pids'] = []
    if dedrmprefs['serials'] == []:
        dedrmprefs['serials'] = []

    # get default adobe adept key(s)
    import calibre_plugins.dedrm.adobekey as adobe
    priorkeycount = len(dedrmprefs['adeptkeys'])
    try:
        defaultkeys = adobe.adeptkeys()
    except:
        import traceback
        traceback.print_exc()
        defaultkeys = []
    defaultcount = 1
    for keyvalue in defaultkeys:
        keyname = u"default_key_{0:d}".format(defaultcount)
        keyvaluehex = keyvalue.encode('hex')
        if keyvaluehex not in dedrmprefs['adeptkeys'].values():
            while keyname in dedrmprefs['adeptkeys']:
                defaultcount += 1
                keyname = u"default_key_{0:d}".format(defaultcount)
            dedrmprefs['adeptkeys'][keyname] = keyvaluehex
    addedkeycount = len(dedrmprefs['adeptkeys']) - priorkeycount
    if addedkeycount > 0:
        print u"{0} v{1}: {2:d} Default Adobe Adept {3} found.".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, u"key" if addedkeycount==1 else u"keys")
    # Make the json write all the prefs to disk
    writeprefs(False)


    # get default kindle key(s)
    import calibre_plugins.dedrm.kindlekey as amazon
    priorkeycount = len(dedrmprefs['kindlekeys'])
    try:
        defaultkeys = amazon.kindlekeys()
    except:
        defaultkeys = []
    defaultcount = 1
    for keyvalue in defaultkeys:
        keyname = u"default_key_{0:d}".format(defaultcount)
        if keyvalue not in dedrmprefs['kindlekeys'].values():
            while keyname in dedrmprefs['kindlekeys']:
                defaultcount += 1
                keyname = u"default_key_{0:d}".format(defaultcount)
            dedrmprefs['kindlekeys'][keyname] = keyvalue
    addedkeycount = len(dedrmprefs['kindlekeys']) - priorkeycount
    if addedkeycount > 0:
        print u"{0} v{1}: {2:d} Default Kindle for Mac/PC {3} found.".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, u"key" if addedkeycount==1 else u"keys")
    # Make the json write all the prefs to disk
    writeprefs(False)

    print u"{0} v{1}: Importing configuration data from old DeDRM plugins".format(PLUGIN_NAME, PLUGIN_VERSION)

    # Handle the old ignoble plugin's customization string by converting the
    # old string to stored keys... get that personal data out of plain sight.
    from calibre.customize.ui import config
    sc = config['plugin_customization']
    val = sc.pop(IGNOBLEPLUGINNAME, None)
    if val is not None:
        print u"{0} v{1}: Converting old Ignoble plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION)
        priorkeycount = len(dedrmprefs['bandnkeys'])
        userkeys = parseIgnobleString(str(val))
        for key in userkeys:
            value = userkeys[key]
            if value not in dedrmprefs['bandnkeys'].values():
                while key in dedrmprefs['bandnkeys']:
                    key = key+key[-1]
                dedrmprefs['bandnkeys'][key] = value
        addedkeycount = len(dedrmprefs['bandnkeys'])-priorkeycount
        print u"{0} v{1}: {2:d} Barnes and Noble {3} imported from old Ignoble plugin configuration string".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, u"key" if addedkeycount==1 else u"keys")
    # Make the json write all the prefs to disk
    writeprefs(False)

    # Handle the old eReader plugin's customization string by converting the
    # old string to stored keys... get that personal data out of plain sight.
    val = sc.pop(EREADERPLUGINNAME, None)
    if val is not None:
        print u"{0} v{1}: Converting old eReader plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION)
        priorkeycount = len(dedrmprefs['ereaderkeys'])
        userkeys = parseeReaderString(str(val))
        for key in userkeys:
            value = userkeys[key]
            if value not in dedrmprefs['ereaderkeys'].values():
                while key in dedrmprefs['ereaderkeys']:
                    key = key+key[-1]
                dedrmprefs['ereaderkeys'][key] = value
        addedkeycount = len(dedrmprefs['ereaderkeys'])-priorkeycount
        print u"{0} v{1}: {2:d} eReader {3} imported from old eReader plugin configuration string".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, u"key" if addedkeycount==1 else u"keys")
    # Make the json write all the prefs to disk
    writeprefs(False)

    # get old Kindle plugin configuration string
    val = sc.pop(OLDKINDLEPLUGINNAME, None)
    if val is not None:
        print u"{0} v{1}: Converting old Kindle plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION)
        priorpidcount = len(dedrmprefs['pids'])
        priorserialcount = len(dedrmprefs['serials'])
        pids, serials = parseKindleString(val)
        for pid in pids:
            if pid not in dedrmprefs['pids']:
                dedrmprefs['pids'].append(pid)
        for serial in serials:
            if serial not in dedrmprefs['serials']:
                dedrmprefs['serials'].append(serial)
        addedpidcount = len(dedrmprefs['pids']) - priorpidcount
        addedserialcount = len(dedrmprefs['serials']) - priorserialcount
        print u"{0} v{1}: {2:d} {3} and {4:d} {5} imported from old Kindle plugin configuration string.".format(PLUGIN_NAME, PLUGIN_VERSION, addedpidcount, u"PID" if addedpidcount==1 else u"PIDs", addedserialcount, u"serial number" if addedserialcount==1 else u"serial numbers")
    # Make the json write all the prefs to disk
    writeprefs(False)

    # copy the customisations back into calibre preferences, as we've now removed the nasty plaintext
    config['plugin_customization'] = sc

    # get any .b64 files in the config dir
    ignoblecount = addConfigFiles('.b64', 'bandnkeys')
    if ignoblecount > 0:
        print u"{0} v{1}: {2:d} Barnes and Noble {3} imported from config folder.".format(PLUGIN_NAME, PLUGIN_VERSION, ignoblecount, u"key file" if ignoblecount==1 else u"key files")
    elif ignoblecount < 0:
        print u"{0} v{1}: Error reading Barnes & Noble keyfiles from config directory.".format(PLUGIN_NAME, PLUGIN_VERSION)
    # Make the json write all the prefs to disk
    writeprefs(False)

    # get any .der files in the config dir
    ineptcount = addConfigFiles('.der', 'adeptkeys','hex')
    if ineptcount > 0:
        print u"{0} v{1}: {2:d} Adobe Adept {3} imported from config folder.".format(PLUGIN_NAME, PLUGIN_VERSION, ineptcount, u"keyfile" if ineptcount==1 else u"keyfiles")
    elif ineptcount < 0:
        print u"{0} v{1}: Error reading Adobe Adept keyfiles from config directory.".format(PLUGIN_NAME, PLUGIN_VERSION)
    # Make the json write all the prefs to disk
    writeprefs(False)

    # get ignoble json prefs
    if 'keys' in ignobleprefs:
        priorkeycount = len(dedrmprefs['bandnkeys'])
        for key in ignobleprefs['keys']:
            value = ignobleprefs['keys'][key]
            if value not in dedrmprefs['bandnkeys'].values():
                while key in dedrmprefs['bandnkeys']:
                    key = key+key[-1]
                dedrmprefs['bandnkeys'][key] = value
        addedkeycount = len(dedrmprefs['bandnkeys']) - priorkeycount
        # no need to delete old prefs, since they contain no recoverable private data
        if addedkeycount > 0:
            print u"{0} v{1}: {2:d} Barnes and Noble {3} imported from Ignoble plugin preferences.".format(PLUGIN_NAME, PLUGIN_VERSION, addedkeycount, u"key" if addedkeycount==1 else u"keys")
    # Make the json write all the prefs to disk
    writeprefs(False)

    # get kindle json prefs
    priorpidcount = len(dedrmprefs['pids'])
    priorserialcount = len(dedrmprefs['serials'])
    if 'pids' in kindleprefs:
        pids, serials = parseKindleString(kindleprefs['pids'])
        for pid in pids:
            if pid not in dedrmprefs['pids']:
                dedrmprefs['pids'].append(pid)
    if 'serials' in kindleprefs:
        pids, serials = parseKindleString(kindleprefs['serials'])
        for serial in serials:
            if serial not in dedrmprefs['serials']:
                dedrmprefs['serials'].append(serial)
    addedpidcount = len(dedrmprefs['pids']) - priorpidcount
    if addedpidcount > 0:
        print u"{0} v{1}: {2:d} {3} imported from Kindle plugin preferences".format(PLUGIN_NAME, PLUGIN_VERSION, addedpidcount, u"PID" if addedpidcount==1 else u"PIDs")
    addedserialcount = len(dedrmprefs['serials']) - priorserialcount
    if addedserialcount > 0:
        print u"{0} v{1}: {2:d} {3} imported from Kindle plugin preferences".format(PLUGIN_NAME, PLUGIN_VERSION, addedserialcount, u"serial number" if addedserialcount==1 else u"serial numbers")

    # Make the json write all the prefs to disk
    writeprefs()
    print u"{0} v{1}: Finished setting up configuration data.".format(PLUGIN_NAME, PLUGIN_VERSION)
