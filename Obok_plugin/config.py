# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

try:
    from PyQt5.Qt import (Qt, QGroupBox, QListWidget, QLineEdit, QDialogButtonBox, QWidget, QLabel, QDialog, QVBoxLayout, QAbstractItemView, QIcon, QHBoxLayout, QComboBox, QListWidgetItem, QFileDialog)
except ImportError:
    from PyQt4.Qt import (Qt, QGroupBox, QListWidget, QLineEdit, QDialogButtonBox, QWidget, QLabel, QDialog, QVBoxLayout, QAbstractItemView, QIcon, QHBoxLayout, QComboBox, QListWidgetItem, QFileDialog)

try:
    from PyQt5 import Qt as QtGui
except ImportError:
    from PyQt4 import QtGui

from calibre.gui2 import (error_dialog, question_dialog, info_dialog, open_url)
from calibre.utils.config import JSONConfig, config_dir

plugin_prefs = JSONConfig('plugins/obok_dedrm_prefs')
plugin_prefs.defaults['finding_homes_for_formats'] = 'Ask'
plugin_prefs.defaults['kobo_serials'] = []
plugin_prefs.defaults['kobo_directory'] = u''

from calibre_plugins.obok_dedrm.__init__ import PLUGIN_NAME, PLUGIN_VERSION
from calibre_plugins.obok_dedrm.utilities import (debug_print)
try:
    debug_print("obok::config.py - loading translations")
    load_translations()
except NameError:
    debug_print("obok::config.py - exception when loading translations")
    pass # load_translations() added in calibre 1.9

class ConfigWidget(QWidget):
    def __init__(self, plugin_action):
        QWidget.__init__(self)
        self.plugin_action = plugin_action
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        # copy of preferences
        self.tmpserials = plugin_prefs['kobo_serials']
        self.kobodirectory = plugin_prefs['kobo_directory']

        combo_label = QLabel(_('When should Obok try to insert EPUBs into existing calibre entries?'), self)
        layout.addWidget(combo_label)
        self.find_homes = QComboBox()
        self.find_homes.setToolTip(_('<p>Default behavior when duplicates are detected. None of the choices will cause calibre ebooks to be overwritten'))
        layout.addWidget(self.find_homes)
        self.find_homes.addItems([_('Ask'), _('Always'), _('Never')])
        index = self.find_homes.findText(plugin_prefs['finding_homes_for_formats'])
        self.find_homes.setCurrentIndex(index)

        self.serials_button = QtGui.QPushButton(self)
        self.serials_button.setToolTip(_(u"Click to manage Kobo serial numbers for Kobo ebooks"))
        self.serials_button.setText(u"Kobo devices serials")
        self.serials_button.clicked.connect(self.edit_serials)
        layout.addWidget(self.serials_button)

        self.kobo_directory_button = QtGui.QPushButton(self)
        self.kobo_directory_button.setToolTip(_(u"Click to specify the Kobo directory"))
        self.kobo_directory_button.setText(u"Kobo directory")
        self.kobo_directory_button.clicked.connect(self.edit_kobo_directory)
        layout.addWidget(self.kobo_directory_button)


    def edit_serials(self):
        d = ManageKeysDialog(self,u"Kobo device serial number",self.tmpserials, AddSerialDialog)
        d.exec_()


    def edit_kobo_directory(self):
        tmpkobodirectory = QFileDialog.getExistingDirectory(self, u"Select Kobo directory", self.kobodirectory or "/home", QFileDialog.ShowDirsOnly)

        if tmpkobodirectory != u"" and tmpkobodirectory is not None:
            self.kobodirectory = tmpkobodirectory


    def save_settings(self):
        plugin_prefs['finding_homes_for_formats'] = unicode(self.find_homes.currentText())
        plugin_prefs['kobo_serials'] = self.tmpserials
        plugin_prefs['kobo_directory'] = self.kobodirectory





class ManageKeysDialog(QDialog):
    def __init__(self, parent, key_type_name, plugin_keys, create_key, keyfile_ext = u""):
        QDialog.__init__(self,parent)
        self.parent = parent
        self.key_type_name = key_type_name
        self.plugin_keys = plugin_keys
        self.create_key = create_key
        self.keyfile_ext = keyfile_ext
        self.json_file = (keyfile_ext == u"k4i")

        self.setWindowTitle("{0} {1}: Manage {2}s".format(PLUGIN_NAME, PLUGIN_VERSION, self.key_type_name))

        # Start Qt Gui dialog layout
        layout = QVBoxLayout(self)
        self.setLayout(layout)

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

        spacerItem = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        button_layout.addItem(spacerItem)

        layout.addSpacing(5)
        migrate_layout = QHBoxLayout()
        layout.addLayout(migrate_layout)
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
        if new_key_value in self.plugin_keys:
            info_dialog(None, "{0} {1}: Duplicate {2}".format(PLUGIN_NAME, PLUGIN_VERSION,self.key_type_name),
                        u"This {0} is already in the list of {0}s has not been added.".format(self.key_type_name), show=True)
            return

        self.plugin_keys.append(d.key_value)
        self.listy.clear()
        self.populate_list()

    def delete_key(self):
        if not self.listy.currentItem():
            return
        keyname = unicode(self.listy.currentItem().text())
        if not question_dialog(self, "{0} {1}: Confirm Delete".format(PLUGIN_NAME, PLUGIN_VERSION), u"Do you really want to delete the {1} <strong>{0}</strong>?".format(keyname, self.key_type_name), show_copy_button=False, default_yes=False):
            return
        self.plugin_keys.remove(keyname)

        self.listy.clear()
        self.populate_list()

class AddSerialDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle(u"{0} {1}: Add New eInk Kobo Serial Number".format(PLUGIN_NAME, PLUGIN_VERSION))
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox(u"", self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel(u"EInk Kobo Serial Number:", self))
        self.key_ledit = QLineEdit("", self)
        self.key_ledit.setToolTip(u"Enter an eInk Kobo serial number. EInk Kobo serial numbers are 13 characters long and usually start with a 'N'. Kobo Serial Numbers are case-sensitive, so be sure to enter the upper and lower case letters unchanged.")
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
            errmsg = u"Please enter an eInk Kindle Serial Number or click Cancel in the dialog."
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        if len(self.key_name) != 13:
            errmsg = u"EInk Kobo Serial Numbers must be 13 characters long. This is {0:d} characters long.".format(len(self.key_name))
            return error_dialog(None, "{0} {1}".format(PLUGIN_NAME, PLUGIN_VERSION), errmsg, show=True, show_copy_button=False)
        QDialog.accept(self)
