DeDRM_App - DeDRM_App.pyw and DeDRM_Drop_Target.bat
===========================================================

DeDRM_App.pyw is a pure python drag and drop application that allows users to drag and drop ebooks or folders of ebooks onto the DeDRM_Drop_Target.bat to have the DRM removed.  It repackages all the "tools" python software in one easy to use program that remembers preferences and settings.

It will work without manual configuration for Kindle for PC ebooks and Adobe Digital Edition epub and pdf ebooks, when Kindle for PC and/or Adobe Digital Editions are installed on the same computer.

To remove the DRM from eInk Kindle ebooks, Barnes and Noble epubs, Mobipocket ebooks and Fictionwise eReader ebooks requires the user to double-click the DeDRM_Drop_Target.bat file and set some additional Preferences including:

eInk Kindle: 16 digit Serial Number
Barnes & Noble: key file (bnepubkey.b64) generate using ignoblekeygen.pyw
eReader Social DRM: Name:Last 8 digits of CC number
MobiPocket: 10 digit PID

Once these preferences have been set, the user can simply drag and drop ebooks onto the DeDRM_Drop_Target to remove the DRM. Note that after setting preferences it is necessary to click on "Set Prefs" button and then quit the application for the change in preferences to fully take effect.

This program requires that a 32 bit version of Python 2.x (tested with Python 2.5 through Python 2.7) and PyCrypto be installed on your computer before it will work.  See below for where to get theese programs for Windows.


Installation
------------
0. If you don't already have a correct version of Python and PyCrypto installed, follow the "Installing Python on Windows" and "Installing PyCrypto on Windows" sections below before continuing.

1. Drag the DeDRM_App folder from tools_v6.0.0/DeDRM_Application_Windows to your "My Documents" folder.

2. Open the DeDRM_App folder you've just dragged, and make a short-cut of the DeDRM_Drop_Target.bat file (right-click/Create Shortcut). Drag the shortcut file onto your Desktop.

3. To set the preferences simply double-click on the short-cut you've just created.


Credits
-------
The mobidedrm and erdr2pml scripts were created by The Dark Reverser
The ignobleepub, ignoblekeygen, ineptepub and adobe key scripts were created by i♥cabbages
The k4mobidedrm script and supporting scripts were written by some_updates with help from DiapDealer and Apprentice Alf, based on code by Bart Simpson (aka Skindle), CMBDTC and clarknova
The alfcrypto library was created by some_updates
The ePub encryption detection script was adapted by Apprentice Alf from a script by Paul Durrant
The DeDRM all-in-one AppleScript was created by Apprentice Alf
The DeDRM all-in-one python script was created by some_updates and Apprentice Alf


Installing Python on Windows
----------------------------
I strongly recommend fully installing ActiveState’s Active Python, free Community Edition for Windows (x86) 32 bits. This is a free, full version of the Python.  It comes with some important additional modules that are not included in the bare-bones version from www.python.org unless you choose to install everything.

1. Download ActivePython 2.7.X for Windows (x86) (or later 2.7 version for Windows (x86) ) from http://www.activestate.com/activepython/downloads. Do not download the ActivePython 2.7.X for Windows (64-bit, x64) verson, even if you are running 64-bit Windows.

2. When it has finished downloading, run the installer. Accept the default options.


Installing PyCrypto on Windows
------------------------------
PyCrypto is a set of encryption/decryption routines that work with Python. The sources are freely available, and compiled versions are available from several sources. You must install a version that is for 32-bit Windows and Python 2.7. I recommend the installer linked from Michael Foord’s blog.

1. Download PyCrypto 2.1 for 32bit Windows and Python 2.7 from http://www.voidspace.org.uk/python/modules.shtml#pycrypto

2. When it has finished downloading, unzip it. This will produce a file “pycrypto-2.1.0.win32-py2.7.exe”.

3. Double-click “pycrypto-2.1.0.win32-py2.7.exe” to run it. Accept the default options.




Linux Users
===========
The DeDRM_app.pyw script, although not the bat shortcut, should work under Linux. Drag & drop functionality is not available.
