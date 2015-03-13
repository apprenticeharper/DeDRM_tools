# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'


import os, struct, time
from StringIO import StringIO
from traceback import print_exc

try:
    from PyQt5.Qt import (Qt, QDialog, QPixmap, QIcon, QLabel, QHBoxLayout, QFont, QTableWidgetItem)
except ImportError:
    from PyQt4.Qt import (Qt, QDialog, QPixmap, QIcon, QLabel, QHBoxLayout, QFont, QTableWidgetItem)
    
from calibre.utils.config import config_dir
from calibre.constants import iswindows, DEBUG
from calibre import prints
from calibre.gui2 import (error_dialog, gprefs)
from calibre.gui2.actions import menu_action_unique_name

from calibre_plugins.obok_dedrm.__init__ import (PLUGIN_NAME,  
                    PLUGIN_SAFE_NAME, PLUGIN_VERSION, PLUGIN_DESCRIPTION)

plugin_ID = None
plugin_icon_resources = {}

try:
    from calibre.gui2 import QVariant
    del QVariant
except ImportError:
    is_qt4 = False
    convert_qvariant = lambda x: x
else:
    is_qt4 = True

    def convert_qvariant(x):
        vt = x.type()
        if vt == x.String:
            return unicode(x.toString())
        if vt == x.List:
            return [convert_qvariant(i) for i in x.toList()]
        return x.toPyObject()

BASE_TIME = None
def debug_print(*args):
    global BASE_TIME
    if BASE_TIME is None:
        BASE_TIME = time.time()
    if DEBUG:
        prints('DEBUG: %6.1f'%(time.time()-BASE_TIME), *args)

try:
    debug_print("obok::utilities.py - loading translations")
    load_translations()
except NameError:
    debug_print("obok::utilities.py - exception when loading translations")
    pass # load_translations() added in calibre 1.9

def format_plural(number, possessive=False):
    '''
    Cosmetic ditty to provide the proper string formatting variable to handle singular/plural situations
    
    :param: number: variable that represents the count/len of something
    '''
    if not possessive:
        return '' if number == 1 else 's'
    return '\'s' if number == 1 else 's\''


def set_plugin_icon_resources(name, resources):
    '''
    Set our global store of plugin name and icon resources for sharing between
    the InterfaceAction class which reads them and the ConfigWidget
    if needed for use on the customization dialog for this plugin.
    '''
    global plugin_icon_resources, plugin_ID
    plugin_ID = name
    plugin_icon_resources = resources

def get_icon(icon_name):
    '''
    Retrieve a QIcon for the named image from the zip file if it exists,
    or if not then from Calibre's image cache.
    '''
    if icon_name:
        pixmap = get_pixmap(icon_name)
        if pixmap is None:
            # Look in Calibre's cache for the icon
            return QIcon(I(icon_name))
        else:
            return QIcon(pixmap)
    return QIcon()

def get_pixmap(icon_name):
    '''
    Retrieve a QPixmap for the named image
    Any icons belonging to the plugin must be prefixed with 'images/'
    '''
    if not icon_name.startswith('images/'):
        # We know this is definitely not an icon belonging to this plugin
        pixmap = QPixmap()
        pixmap.load(I(icon_name))
        return pixmap

    # Check to see whether the icon exists as a Calibre resource
    # This will enable skinning if the user stores icons within a folder like:
    # ...\AppData\Roaming\calibre\resources\images\Plugin Name\
    if plugin_ID:
        local_images_dir = get_local_images_dir(plugin_ID)
        local_image_path = os.path.join(local_images_dir, icon_name.replace('images/', ''))
        if os.path.exists(local_image_path):
            pixmap = QPixmap()
            pixmap.load(local_image_path)
            return pixmap

    # As we did not find an icon elsewhere, look within our zip resources
    if icon_name in plugin_icon_resources:
        pixmap = QPixmap()
        pixmap.loadFromData(plugin_icon_resources[icon_name])
        return pixmap
    return None

def get_local_images_dir(subfolder=None):
    '''
    Returns a path to the user's local resources/images folder
    If a subfolder name parameter is specified, appends this to the path
    '''
    images_dir = os.path.join(config_dir, 'resources/images')
    if subfolder:
        images_dir = os.path.join(images_dir, subfolder)
    if iswindows:
        images_dir = os.path.normpath(images_dir)
    return images_dir

def showErrorDlg(errmsg, parent, trcbk=False):
    '''
    Wrapper method for calibre's error_dialog
    '''
    if trcbk:
        error= ''
        f=StringIO()     
        print_exc(file=f)
        error_mess = f.getvalue().splitlines()
        for line in error_mess:
            error = error + str(line) + '\n'
        errmsg = errmsg + '\n\n' + error
    return  error_dialog(parent, _(PLUGIN_NAME + ' v' + PLUGIN_VERSION),
                _(errmsg), show=True)

class SizePersistedDialog(QDialog):
    '''
    This dialog is a base class for any dialogs that want their size/position
    restored when they are next opened.
    '''
    def __init__(self, parent, unique_pref_name):
        QDialog.__init__(self, parent)
        self.unique_pref_name = unique_pref_name
        self.geom = gprefs.get(unique_pref_name, None)
        self.finished.connect(self.dialog_closing)

    def resize_dialog(self):
        if self.geom is None:
            self.resize(self.sizeHint())
        else:
            self.restoreGeometry(self.geom)

    def dialog_closing(self, result):
        geom = bytearray(self.saveGeometry())
        gprefs[self.unique_pref_name] = geom
        self.persist_custom_prefs()

    def persist_custom_prefs(self):
        '''
        Invoked when the dialog is closing. Override this function to call
        save_custom_pref() if you have a setting you want persisted that you can
        retrieve in your __init__() using load_custom_pref() when next opened
        '''
        pass

    def load_custom_pref(self, name, default=None):
        return gprefs.get(self.unique_pref_name+':'+name, default)

    def save_custom_pref(self, name, value):
        gprefs[self.unique_pref_name+':'+name] = value

class ImageTitleLayout(QHBoxLayout):
    '''
    A reusable layout widget displaying an image followed by a title
    '''
    def __init__(self, parent, icon_name, title):
        '''
        :param parent: Parent gui
        :param icon_name: Path to plugin image resource
        :param title: String to be displayed beside the image
        '''
        QHBoxLayout.__init__(self)
        self.title_image_label = QLabel(parent)
        self.update_title_icon(icon_name)
        self.addWidget(self.title_image_label)

        title_font = QFont()
        title_font.setPointSize(16)
        shelf_label = QLabel(title, parent)
        shelf_label.setFont(title_font)
        self.addWidget(shelf_label)
        self.insertStretch(-1)

    def update_title_icon(self, icon_name):
        pixmap = get_pixmap(icon_name)
        if pixmap is None:
            error_dialog(self.parent(), _('Restart required'),
                         _('Title image not found - you must restart Calibre before using this plugin!'), show=True)
        else:
            self.title_image_label.setPixmap(pixmap)
        self.title_image_label.setMaximumSize(32, 32)
        self.title_image_label.setScaledContents(True)


class ReadOnlyTableWidgetItem(QTableWidgetItem):

    def __init__(self, text):
        if text is None:
            text = ''
        QTableWidgetItem.__init__(self, text, QTableWidgetItem.UserType)
        self.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
