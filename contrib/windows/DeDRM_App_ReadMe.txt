DeDRM_App - DeDRM_App.pyw and DeDRM_Drop_Target.bat
===================================================

DeDRM_App.pyw is a python drag and drop application that allows users to drag and drop ebooks or folders of ebooks onto the DeDRM_Drop_Target.bat to have the DRM removed.  It repackages all the tools (except obok) in one easy to use program that remembers preferences and settings.

It will work without manual configuration for Kindle for PC ebooks, Adobe Digital Edition (2.0.1) epub and pdf ebooks and Barnes & Noble NOOK Study ePubs when Kindle for PC, Adobe Digital Editions and NOOK Study are installed on the same computer and user account.

To remove the DRM from eInk Kindle ebooks, Mobipocket ebooks and Fictionwise eReader ebooks requires the user to double-click the DeDRM_Drop_Target.bat file and set some additional Preferences including:

eInk Kindle: 16 digit Serial Number
MobiPocket: 10 digit PID
eReader Social DRM: Name:Last 8 digits of CC number

Once these preferences have been set, the user can simply drag and drop ebooks onto the DeDRM_Drop_Target to remove the DRM. Note that after setting preferences it is necessary to click on "Set Prefs" button and then quit the application for the change in preferences to fully take effect.

This program requires that Python 2.7 and PyCrypto 2.6 for Python 2.7 be installed on your computer before it will work.  See below for how to get and install these programs for Windows.


Installation
------------
0. If you don't already have a correct version of Python and PyCrypto installed, follow the "Installing Python on Windows" and "Installing PyCrypto on Windows" sections below before continuing.

1. Drag the DeDRM_App folder from DeDRM_Application_Windows to your "My Documents" folder.

2. Open the DeDRM_App folder you've just dragged, and make a short-cut of the DeDRM_Drop_Target.bat file (right-click/Create Shortcut). Drag the shortcut file onto your Desktop.

3. To set the preferences simply double-click on the short-cut you've just created.


Credits
-------
The original inept and ignoble scripts were by i♥cabbages
The original mobidedrm and erdr2pml scripts were by The Dark Reverser
The original topaz DRM removal script was by CMBDTC
The original topaz format conversion scripts were by some_updates, clarknova and Bart Simpson

The alfcrypto library is by some_updates
The ePub encryption detection script is by Apprentice Alf, adapted from a script by Paul Durrant
The ignoblekey script is by Apprentice Harper
The DeDRM python GUI was by some_updates and is maintained by Apprentice Alf and Apprentice Harper

Many fixes, updates and enhancements to the scripts and applicatons have been made by many other people. For more details, see the commments in the individual scripts.


Installing Python on Windows
----------------------------
I strongly recommend fully installing ActiveState’s Active Python, free Community Edition for Windows. This is a free, full version of the Python.  It comes with some important additional modules that are not included in the bare-bones version from www.python.org unless you choose to install everything.

1. Download ActivePython 2.7.8 for Windows (or later 2.7.x version for Windows, but NOT 3.x) from http://www.activestate.com/activepython/downloads.

2. When it has finished downloading, run the installer. Accept the default options.


Installing PyCrypto on Windows
------------------------------
PyCrypto is a set of encryption/decryption routines that work with Python. The sources are freely available, and compiled versions are available from several sources. You must install a version that is for Python 2.7. I recommend the installer linked from Michael Foord’s blog.

1. Download PyCrypto 2.6 (or later) for Windows and Python 2.7 from http://www.voidspace.org.uk/python/modules.shtml#pycrypto

2. When it has finished downloading, run the application. Accept the default options.


Linux Users
===========
The DeDRM_app.pyw script, although not the .bat shortcut, should work under Linux. Drag & drop functionality is not available. Depending on your Linux installation, you may or may not need to install Python 2 and PyCrypto.
