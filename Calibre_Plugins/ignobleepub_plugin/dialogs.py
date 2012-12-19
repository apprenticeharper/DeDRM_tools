#!/usr/bin/env python
# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

from __future__ import with_statement
__license__ = 'GPL v3'

from PyQt4.Qt import (Qt, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QDialog, QDialogButtonBox)
from calibre.gui2 import error_dialog

from calibre_plugins.ignobleepub.__init__ import PLUGIN_NAME, PLUGIN_VERSION
from calibre_plugins.ignobleepub.utilities import uStrCmp

class AddKeyDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle('Create New Ignoble Key')
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox('', self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        key_group = QHBoxLayout()
        data_group_box_layout.addLayout(key_group)
        key_group.addWidget(QLabel('Unique Key Name:', self))
        self.key_ledit = QLineEdit('', self)
        self.key_ledit.setToolTip(_('<p>Enter an identifying name for this new Ignoble key.</p>' +
                                '<p>It should be something that will help you remember ' +
                                'what personal information was used to create it.'))
        key_group.addWidget(self.key_ledit)
        key_label = QLabel(_(''), self)
        key_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(key_label)

        name_group = QHBoxLayout()
        data_group_box_layout.addLayout(name_group)
        name_group.addWidget(QLabel('Your Name:', self))
        self.name_ledit = QLineEdit('', self)
        self.name_ledit.setToolTip(_('<p>Enter your name as it appears in your B&N ' +
                                'account and/or on your credit card.</p>' +
                                '<p>It will only be used to generate this ' +
                                'one-time key and won\'t be stored anywhere ' +
                                'in calibre or on your computer.</p>' +
                                '<p>(ex: Jonathan Smith)'))
        name_group.addWidget(self.name_ledit)
        name_disclaimer_label = QLabel(_('Will not be stored/saved in configuration data:'), self)
        name_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(name_disclaimer_label)

        ccn_group = QHBoxLayout()
        data_group_box_layout.addLayout(ccn_group)
        ccn_group.addWidget(QLabel('Credit Card#:', self))
        self.cc_ledit = QLineEdit('', self)
        self.cc_ledit.setToolTip(_('<p>Enter the full credit card number on record ' +
                                'in your B&N account.</p>' +
                                '<p>No spaces or dashes... just the numbers. ' +
                                'This CC# will only be used to generate this ' +
                                'one-time key and won\'t be stored anywhere in ' +
                                'calibre or on your computer.'))
        ccn_group.addWidget(self.cc_ledit)
        ccn_disclaimer_label = QLabel(_('Will not be stored/saved in configuration data:'), self)
        ccn_disclaimer_label.setAlignment(Qt.AlignHCenter)
        data_group_box_layout.addWidget(ccn_disclaimer_label)
        layout.addSpacing(20)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

        self.resize(self.parent.sizeHint())

    def accept(self):
        if (self.key_ledit.text().isEmpty() or self.name_ledit.text().isEmpty()
                                or self.cc_ledit.text().isEmpty()):
            errmsg = '<p>All fields are required!'
            return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        if (unicode(self.key_ledit.text()).isspace() or unicode(self.name_ledit.text()).isspace()
                                or unicode(self.cc_ledit.text()).isspace()):
            errmsg = '<p>All fields are required!'
            return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        if not unicode(self.cc_ledit.text()).isdigit():
            errmsg = '<p>Numbers only in the credit card number field!'
            return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        if len(self.key_ledit.text()) < 4:
            errmsg = '<p>Key name must be at <i>least</i> 4 characters long!'
            return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        for k in self.parent.plugin_keys.keys():
            if uStrCmp(self.key_ledit.text(), k, True):
                errmsg = '<p>The key name <strong>%s</strong> is already being used.' % self.key_ledit.text()
                return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        QDialog.accept(self)

    @property
    def user_name(self):
        return unicode(self.name_ledit.text().toUtf8(), 'utf8').strip().lower().replace(' ','')
    @property
    def cc_number(self):
        return unicode(self.cc_ledit.text().toUtf8(), 'utf8').strip().replace(' ', '').replace('-','')
    @property
    def key_name(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8')

class RenameKeyDialog(QDialog):
    def __init__(self, parent=None,):
        QDialog.__init__(self, parent)
        self.parent = parent
        self.setWindowTitle('Rename Ignoble Key')
        layout = QVBoxLayout(self)
        self.setLayout(layout)

        data_group_box = QGroupBox('', self)
        layout.addWidget(data_group_box)
        data_group_box_layout = QVBoxLayout()
        data_group_box.setLayout(data_group_box_layout)

        data_group_box_layout.addWidget(QLabel('Key Name:', self))
        self.key_ledit = QLineEdit(self.parent.listy.currentItem().text(), self)
        self.key_ledit.setToolTip(_('<p>Enter a new name for this existing Ignoble key.'))
        data_group_box_layout.addWidget(self.key_ledit)

        layout.addSpacing(20)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def accept(self):
        if self.key_ledit.text().isEmpty() or unicode(self.key_ledit.text()).isspace():
            errmsg = '<p>Key name field cannot be empty!'
            return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        if len(self.key_ledit.text()) < 4:
            errmsg = '<p>Key name must be at <i>least</i> 4 characters long!'
            return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        if uStrCmp(self.key_ledit.text(), self.parent.listy.currentItem().text()):
                # Same exact name ... do nothing.
                return QDialog.reject(self)
        for k in self.parent.plugin_keys.keys():
            if (uStrCmp(self.key_ledit.text(), k, True) and
                        not uStrCmp(k, self.parent.listy.currentItem().text(), True)):
                errmsg = '<p>The key name <strong>%s</strong> is already being used.' % self.key_ledit.text()
                return error_dialog(None, PLUGIN_NAME,
                                    _(errmsg), show=True, show_copy_button=False)
        QDialog.accept(self)

    @property
    def key_name(self):
        return unicode(self.key_ledit.text().toUtf8(), 'utf8')
