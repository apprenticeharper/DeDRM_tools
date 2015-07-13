#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

from __future__ import with_statement
__license__ = 'GPL v3'

# Standard Python modules.
import os, sys, re, hashlib
import json

from PyQt4.Qt import (Qt, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QListWidget, QListWidgetItem, QAbstractItemView, QLineEdit, QPushButton, QIcon, QGroupBox, QDialog, QDialogButtonBox, QUrl, QString)
from PyQt4 import QtGui

# calibre modules and constants.
from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url,
                            choose_dir, choose_files)
from calibre.utils.config import dynamic, config_dir, JSONConfig

from calibre_plugins.dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION
from calibre_plugins.dedrm.utilities import (uStrCmp, DETAILED_MESSAGE, parseCustString)
from calibre_plugins.dedrm.ignoblekeyfetch import fetch_key as generate_bandn_key
from calibre_plugins.dedrm.erdr2pml import getuser_key as generate_ereader_key
from calibre_plugins.dedrm.adobekey import adeptkeys as retrieve_adept_keys
from calibre_plugins.dedrm.kindlekey import kindlekeys as retrieve_kindle_keys

class ManageKeysDialog(QDialog):
    def __init__(self, parent, key_type_name, plugin_keys, create_key, keyfile_ext = u""):
        QDialog.__init__(self,parent)
        self.parent = parent
        self.key_type_name = key_type_name
        self.plugin_keys = plugin_keys
        self.create_key = create_key
        self.keyfile_ext = keyfile_ext
        self.import_key = (keyfile_ext != u"")
        self.binary_file = (key_type_name == u"Adobe Digital Editions Key")
        self.json_file = (key_type_name == u"Kindle for Mac and PC Key")

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
        self._add_key_button.setToolTip(u"Create new {0}".format(self.key_type_name))
        self._add_key_button.setIcon(QIcon(I('plus.png')))
        self._add_key_button.clicked.connect(self.add_key)
        button_layout.addWidget(self._add_key_button)

        self._delete_key_button = QtGui.QToolButton(self)
        self._delete_key_button.setToolTip(_(u"Delete highlighted key"))
        self._delete_key_button.setIcon(QIcon(I('list_remove.png')))
        self._delete_key_button.clicked.connect(self.delete_key)
        button_layout.addWidget(self._delete_key_button)

        if type(self.plugin_keys) == dict:
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
        keyname = unicode(self.listy.currentItem().text().toUtf8(),'utf8')
        if not question_dialog(self, "{0} {1}: Confirm Rename".format(PLUGIN_NAME, PLUGIN_VERSION), u"Do you really want to rename the {2} named <strong>{0}</strong> to <strong>{1}</strong>?".format(keyname,d.key_name,self.key_type_name), show_copy_button=False, default_yes=False):
            return
        self.plugin_keys[d.key_name] = self.plugin_keys[keyname]
        del self.plugin_keys[keyname]

        self.listy.clear()
        self.populate_list()

    def delete_key(self):
        if not self.listy.currentItem():
            return
        keyname = unicode(self.listy.currentItem().text().toUtf8(), 'utf8')
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
        dynamic[PLUGIN_NAME + u"config_dir"] = config_dir
        files = choose_files(self, PLUGIN_NAME + u"config_dir",
                u"Select {0} files to import".format(self.key_type_name), [(u"{0} files".format(self.key_type_name), [self.keyfile_ext])], False)
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
        filter = QString(u"{0} Files (*.{1})".format(self.key_type_name, self.keyfile_ext))
        keyname = unicode(self.listy.currentItem().text().toUtf8(), 'utf8')
        if dynamic.get(PLUGIN_NAME + 'save_dir'):
            defaultname = os.path.join(dynamic.get(PLUGIN_NAME + 'save_dir'), u"{0}.{1}".format(keyname , self.keyfile_ext))
        else:
            defaultname = os.path.join(os.path.expanduser('~'), u"{0}.{1}".format(keyname , self.keyfile_ext))
        filename = unicode(QtGui.QFileDialog.getSaveFileName(self, u"Save {0} File as...".format(self.key_type_name), defaultname,
                                            u"{0} Files (*.{1})".format(self.key_type_name,self.keyfile_ext), filter))
        if filename:
            dynamic[PLUGIN_NAME + 'save_dir'] = os.path.split(filename)[0]
            with file(filename, 'w') as fname:
                if self.binary_file:
                    fname.write(self.plugin_keys[keyname].decode('hex'))
                elif self.json_file:
                    fname.write(json.dumps(self.plugin_keys[keyname]))
                else:
                    fname.write(self.plugin_keys[keyname])




class RenameKeyDialog(QDialog):
    def __init__(self, parent=None,):
        print repr(self), repr(parent)
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
        if self.key_ledit.text().isEmpty() or unicode(self.key_ledit.text()).isspace():
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
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()








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
        key_label = QLabel(_(''), self)
        key_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(key_label)

        name_group = QHBoxLayout()
        data_group_box_layout.addLayout(name_group)
        name_group.addWidget(QLabel(u"Your Name:", self))
        self.name_ledit = QLineEdit(u"", self)
        self.name_ledit.setToolTip(_(u"<p>Enter your name as it appears in your B&N " +
                                u"account or on your credit card.</p>" +
                                u"<p>It will only be used to generate this " +
                                u"one-time key and won\'t be stored anywhere " +
                                u"in calibre or on your computer.</p>" +
                                u"<p>(ex: Jonathan Smith)"))
        name_group.addWidget(self.name_ledit)
        name_disclaimer_label = QLabel(_(u"(Will not be saved in configuration data)"), self)
        name_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(name_disclaimer_label)

        ccn_group = QHBoxLayout()
        data_group_box_layout.addLayout(ccn_group)
        ccn_group.addWidget(QLabel(u"Credit Card#:", self))
        self.cc_ledit = QLineEdit(u"", self)
        self.cc_ledit.setToolTip(_(u"<p>Enter the full credit card number on record " +
                                u"in your B&N account.</p>" +
                                u"<p>No spaces or dashes... just the numbers. " +
                                u"This number will only be used to generate this " +
                                u"one-time key and won\'t be stored anywhere in " +
                                u"calibre or on your computer."))
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
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

    @property
    def key_value(self):
        return generate_bandn_key(self.user_name,self.cc_number)

    @property
    def user_name(self):
        return unicode(self.name_ledit.text().toUtf8(), 'utf8').strip().lower().replace(' ','')

    @property
    def cc_number(self):
        return unicode(self.cc_ledit.text().toUtf8(), 'utf8').strip().replace(' ', '').replace('-','')


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
        key_label = QLabel(_(''), self)
        key_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(key_label)

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
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

    @property
    def key_value(self):
        return generate_ereader_key(self.user_name,self.cc_number).encode('hex')

    @property
    def user_name(self):
        return unicode(self.name_ledit.text().toUtf8(), 'utf8').strip().lower().replace(' ','')

    @property
    def cc_number(self):
        return unicode(self.cc_ledit.text().toUtf8(), 'utf8').strip().replace(' ', '').replace('-','')


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
            self.default_key = retrieve_adept_keys()[0]
        except:
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
            self.key_ledit = QLineEdit("", self)
            self.key_ledit.setToolTip(u"<p>Enter an identifying name for the current default Adobe Digital Editions key.")
            key_group.addWidget(self.key_ledit)
            key_label = QLabel(_(''), self)
            key_label.setAlignment(Qt.AlignHCenter)
            data_group_box_layout.addWidget(key_label)
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
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

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
            self.default_key = retrieve_kindle_keys()[0]
        except:
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
            self.key_ledit = QLineEdit("", self)
            self.key_ledit.setToolTip(u"<p>Enter an identifying name for the current default Kindle for Mac/PC key.")
            key_group.addWidget(self.key_ledit)
            key_label = QLabel(_(''), self)
            key_label.setAlignment(Qt.AlignHCenter)
            data_group_box_layout.addWidget(key_label)
            self.button_box.accepted.connect(self.accept)
        else:
            default_key_error = QLabel(u"The default encryption key for Kindle for Mac/PC could not be found.", self)
            default_key_error.setAlignment(Qt.AlignHCenter)
            layout.addWidget(default_key_error)
            # if no default, bot buttons do the same
            self.button_box.accepted.connect(self.reject)

        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

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
        key_label = QLabel(_(''), self)
        key_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(key_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

    @property
    def key_value(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"Please enter an eInk Kindle Serial Number or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 16:
            errmsg = u"EInk Kindle Serial Numbers must be 16 characters long. This is {0:d} characters long.".format(len(self.key_name))
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
        key_label = QLabel(_(''), self)
        key_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(key_label)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.sizeHint())

    @property
    def key_name(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

    @property
    def key_value(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8').strip()

    def accept(self):
        if len(self.key_name) == 0 or self.key_name.isspace():
            errmsg = u"Please enter a Mobipocket PID or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 8 and len(self.key_name) != 10:
            errmsg = u"Mobipocket PIDs must be 8 or 10 characters long. This is {0:d} characters long.".format(len(self.key_name))
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)


