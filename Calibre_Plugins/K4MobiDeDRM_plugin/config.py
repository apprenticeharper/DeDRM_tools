from PyQt4.Qt import QWidget, QVBoxLayout, QLabel, QLineEdit

from calibre.utils.config import JSONConfig

# This is where all preferences for this plugin will be stored
# You should always prefix your config file name with plugins/,
# so as to ensure you dont accidentally clobber a calibre config file
prefs = JSONConfig('plugins/K4MobiDeDRM')

# Set defaults
prefs.defaults['pids'] = ""
prefs.defaults['serials'] = ""
prefs.defaults['WINEPREFIX'] = None


class ConfigWidget(QWidget):

    def __init__(self):
        QWidget.__init__(self)
        self.l = QVBoxLayout()
        self.setLayout(self.l)

        self.serialLabel = QLabel('eInk Kindle Serial numbers (First character B, 16 characters, use commas if more than one)')
        self.l.addWidget(self.serialLabel)

        self.serials = QLineEdit(self)
        self.serials.setText(prefs['serials'])
        self.l.addWidget(self.serials)
        self.serialLabel.setBuddy(self.serials)

        self.pidLabel = QLabel('Mobipocket PIDs (8 or 10 characters, use commas if more than one)')
        self.l.addWidget(self.pidLabel)

        self.pids = QLineEdit(self)
        self.pids.setText(prefs['pids'])
        self.l.addWidget(self.pids)
        self.pidLabel.setBuddy(self.serials)

        self.wpLabel = QLabel('For Linux only: WINEPREFIX (enter absolute path)')
        self.l.addWidget(self.wpLabel)

        self.wineprefix = QLineEdit(self)
        wineprefix = prefs['WINEPREFIX']
        if wineprefix is not None:
            self.wineprefix.setText(wineprefix)
        else:
            self.wineprefix.setText('')

        self.l.addWidget(self.wineprefix)
        self.wpLabel.setBuddy(self.wineprefix)

    def save_settings(self):
    	prefs['pids'] = str(self.pids.text()).replace(" ","")
        prefs['serials'] = str(self.serials.text()).replace(" ","")
        winepref=str(self.wineprefix.text())
        if winepref.strip() != '':
            prefs['WINEPREFIX'] = winepref
        else:
            prefs['WINEPREFIX'] = None
