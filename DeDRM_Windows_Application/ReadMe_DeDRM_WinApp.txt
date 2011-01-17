ReadMe_DeDRM_WinApp_v1.2
-----------------------

DeDRM_WinApp is a pure python drag and drop application that allows users to drag and drop ebooks or folders of ebooks onto theDeDRM_Drop_Target to have the DRM removed.  It repackages the"tools" python software in one easy to use program.

It should work out of the box with Kindle for PC ebooks and Adobe Adept epub and pdf ebooks.

To remove the DRM from standalone Kindle ebooks, eReader pdb ebooks, Barnes and Noble epubs, and Mobipocket ebooks requires the user to double-click the DeDRM_Drop_Target and set some additional Preferences including:

Kindle 16 digit Serial Number
Barnes & Noble key files (bnepubkey.b64)
eReader Social DRM: (Name:Last 8 digits of CC number)
MobiPocket, Kindle for iPhone/iPad/iPodTouch  10 digit PID 

Once these preferences have been set, the user can simply drag and drop ebooks onto the DeDRM_Drop_Target to remove the DRM.

This program requires that the proper 32 bit version of Python 2.X (tested with Python 2.5 through Python 2.7) and PyCrypto be installed on your computer before it will work.  See below for where to get theese programs for Windows.



Installation
------------

1. Download the latest DeDRM_WinApp_vx.x.zip and fully Extract its contents. 

2. Move the resulting DeDRM_WinApp_vX.X folder to whereever you keep you other programs.
   (I typically use an "Applications" folder inside of my home directory)

3. Open the folder, and create a short-cut to DeDRM_Drop_Target and move that short-cut to your Desktop.

4. To set the preferences simply double-click on your just created short-cut.


If you already have a correct version of Python and PyCrypto installed and in your path, you are ready to go!



If not, see where you can get these additional pieces.


Installing Python on Windows
----------------------------
I strongly recommend installing ActiveState’s Active Python, Community Edition for Windows (x86) 32 bits. This is a free, full version of the Python.  It comes with some important additional modules that are not included in the bare-bones version from www.python.org unless you choose to install everything.

1. Download ActivePython 2.7.1 for Windows (x86) (or later 2.7 version for Windows (x86) ) from http://www.activestate.com/activepython/downloads. Do not download the ActivePython 2.7.1 for Windows (64-bit, x64) verson, even if you are running 64-bit Windows.

2. When it has finished downloading, run the installer. Accept the default options.

Installing PyCrypto on Windows
------------------------------
PyCrypto is a set of encryption/decryption routines that work with Python. The sources are freely available, and compiled versions are available from several sources. You must install a version that is for 32-bit Windows and Python 2.7. I recommend the installer linked from Michael Foord’s blog.

1. Download PyCrypto 2.1 for 32bit Windows and Python 2.7 from http://www.voidspace.org.uk/python/modules.shtml#pycrypto

2. When it has finished downloading, unzip it. This will produce a file “pycrypto-2.1.0.win32-py2.7.exe”.

3. Double-click “pycrypto-2.1.0.win32-py2.7.exe” to run it. Accept the default options.

