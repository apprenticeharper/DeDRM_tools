# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__version__ = '6.7.0'
__docformat__ = 'restructuredtext en'

#####################################################################
# Plug-in base class
#####################################################################

from calibre.customize import InterfaceActionBase

try:
    load_translations()
except NameError:
    pass # load_translations() added in calibre 1.9

PLUGIN_NAME = 'Obok DeDRM'
PLUGIN_SAFE_NAME = PLUGIN_NAME.strip().lower().replace(' ', '_')
PLUGIN_DESCRIPTION = _('Removes DRM from Kobo kepubs and adds them to the library.')
PLUGIN_VERSION_TUPLE = (6, 7, 0)
PLUGIN_VERSION = '.'.join([str(x) for x in PLUGIN_VERSION_TUPLE])
HELPFILE_NAME = PLUGIN_SAFE_NAME + '_Help.htm'
PLUGIN_AUTHORS = 'Anon'
#####################################################################

class ObokDeDRMAction(InterfaceActionBase):

    name                    = PLUGIN_NAME
    description             = PLUGIN_DESCRIPTION
    supported_platforms     = ['windows', 'osx', 'linux' ]
    author                  = PLUGIN_AUTHORS
    version                 = PLUGIN_VERSION_TUPLE
    minimum_calibre_version = (1, 0, 0)

    #: This field defines the GUI plugin class that contains all the code
    #: that actually does something. Its format is module_path:class_name
    #: The specified class must be defined in the specified module.
    actual_plugin           = 'calibre_plugins.'+PLUGIN_SAFE_NAME+'.action:InterfacePluginAction'

    def is_customizable(self):
        '''
        This method must return True to enable customization via
        Preferences->Plugins
        '''
        return True

    def config_widget(self):
        '''
        Implement this method and :meth:`save_settings` in your plugin to
        use a custom configuration dialog.

        This method, if implemented, must return a QWidget. The widget can have
        an optional method validate() that takes no arguments and is called
        immediately after the user clicks OK. Changes are applied if and only
        if the method returns True.

        If for some reason you cannot perform the configuration at this time,
        return a tuple of two strings (message, details), these will be
        displayed as a warning dialog to the user and the process will be
        aborted.

        The base class implementation of this method raises NotImplementedError
        so by default no user configuration is possible.
        '''
        if self.actual_plugin_:
            from calibre_plugins.obok_dedrm.config import ConfigWidget
            return ConfigWidget(self.actual_plugin_)

    def save_settings(self, config_widget):
        '''
        Save the settings specified by the user with config_widget.
        '''
        config_widget.save_settings()
