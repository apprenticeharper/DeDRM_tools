ReadMe_DeDRM_v5.4.1_WinApp
-----------------------

DeDRM_v5.4.1_WinApp is a pure python drag and drop application that allows users to drag and drop ebooks or folders of ebooks onto the DeDRM_Drop_Target to have the DRM removed.  It repackages the"tools" python software in one easy to use program that remembers preferences and settings.

It should work out of the box with Kindle for PC ebooks and Adobe Adept epub and pdf ebooks.

To remove the DRM from standalone Kindle ebooks, eReader pdb ebooks, Barnes and Noble epubs, and Mobipocket ebooks requires the user to double-click the DeDRM_Drop_Target and set some additional Preferences including:

eInk Kindle: 16 digit Serial Number
Barnes & Noble: key file (bnepubkey.b64)
eReader Social DRM: Name:Last 8 digits of CC number
MobiPocket: 10 digit PID

Once these preferences have been set, the user can simply drag and drop ebooks onto the DeDRM_Drop_Target to remove the DRM.

This program requires that a 32 bit version of Python 2.X (tested with Python 2.5 through Python 2.7) and PyCrypto be installed on your computer before it will work.  See below for where to get theese programs for Windows.

Installation
------------

0. If you don't already have a correct version of Python and PyCrypto installed, follow the "Installing Python on Windows" and "Installing PyCrypto on Windows" sections below before continuing.

1. Drag the DeDRM_5.4.1 folder from tools_v5.4.1/DeDRM_Applications/Windows to your "My Documents" folder.

2. Open the DeDRM_5.4.1 folder you've just dragged, and make a short-cut of the DeDRM_Drop_Target.bat file (right-click/Create Shortcut). Drag the shortcut file onto your Desktop.

3. To set the preferences simply double-click on your just created short-cut.



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

