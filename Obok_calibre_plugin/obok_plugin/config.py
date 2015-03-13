# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

try:
    from PyQt5.Qt import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox)
except ImportError:
    from PyQt4.Qt import (QWidget, QLabel, QVBoxLayout, QHBoxLayout, QComboBox)
    
from calibre.utils.config import JSONConfig, config_dir

plugin_prefs = JSONConfig('plugins/obok_dedrm_prefs')
plugin_prefs.defaults['finding_homes_for_formats'] = 'Ask'

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
        
        combo_label = QLabel(_('When should Obok try to insert EPUBs into existing calibre entries?'), self)
        layout.addWidget(combo_label)
        self.find_homes = QComboBox()
        self.find_homes.setToolTip(_('<p>Default behavior when duplicates are detected. None of the choices will cause calibre ebooks to be overwritten'))
        layout.addWidget(self.find_homes)
        self.find_homes.addItems([_('Ask'), _('Always'), _('Never')])
        index = self.find_homes.findText(plugin_prefs['finding_homes_for_formats'])
        self.find_homes.setCurrentIndex(index)
    
    def save_settings(self):
        plugin_prefs['finding_homes_for_formats'] = unicode(self.find_homes.currentText())
