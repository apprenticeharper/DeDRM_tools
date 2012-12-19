Kindle and Mobipocket Plugin - K4MobiDeDRM_v04.10_plugin.zip
============================================================

Credit given to The Dark Reverser for the original standalone script. Credit also to the many people who have updated and expanded that script since then.

Plugin for K4PC, K4Mac, eInk Kindles and Mobipocket.

This plugin supersedes MobiDeDRM, K4DeDRM, and K4PCDeDRM and K4X plugins. If you install this plugin, those plugins should be removed, as should any earlier versions of this plugin.

This plugin is meant to remove the DRM from .prc, .mobi, .azw, .azw1, .azw3, .azw4 and .tpz ebooks. Calibre can then convert them to whatever format you desire. It is meant to function without having to install any dependencies except for Calibre being on your same machine and in the same account as your "Kindle for PC" or "Kindle for Mac" application if you are going to remove the DRM from books from those programs.


Installation
------------

Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior" to go to Calibre's Preferences page.  Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (K4MobiDeDRM_v04.10_plugin.zip) and click the 'Add' button. Click 'Yes' in the the "Are you sure?" dialog. Click OK in the "Success" dialog.

Make sure that you delete any old versions of the plugin. They might interfere with the operation of the new one.


Customization
-------------

Highlight the plugin (K4MobiDeDRM under the "File type plugins" category) and click the "Customize Plugin" button on Calibre's Preferences->Plugins page.

If you have an eInk Kindle enter the 16 character serial number (these all begin a "B" or a "9") in the serial numbers field. The easiest way to make sure that you have the serial number right is to copy it from your Amazon account pages (the "Manage Your Devices" page). If you have more than one eInk Kindle, you can enter multiple serial numbers separated by commas.

If you have Mobipocket books, enter your 8 or 10 digit PID in the Mobipocket PIDs field. If you have more than one PID, separate them with commas.

These configuration steps are not needed if you only want to decode "Kindle for PC" or "Kindle for Mac" books.


Troubleshooting
---------------

If you find that it's not working for you (imported ebooks still have DRM), you can save a lot of time and trouble by first deleting the DRMed ebook from calibre and then trying to add the ebook to calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might as well get used to it. ;)

On Macintosh only you must first run calibre, open Preferences, open Miscellaneous, and click on the “Install command line tools” button. (On Windows and Linux the command line tools are installed automatically.)

On Windows, open a terminal/command window. (Start/Run… and then type 'cmd' (without the 's) as the program to run).
On Macintosh, open the Terminal application (in your Utilities folder).
On Linux open a command window. Hopefully all Linux users know how to do this, as I do not.

You should now have a text-based command-line window open. Also have open the folder containing the ebook to be imported. Make sure that book isn’t already in calibre, and that calibre isn’t running.

Now type in "calibredb add " (without the " but don’t miss that final space) and now drag the book to be imported onto the window. The full path to the book should be inserted into the command line. Now press the return/enter key. The import routines will run and produce some logging information.

Now copy the output from the terminal window.
On Windows, you must use the window menu (little icon at left of window bar) to select all the text and then to copy it.
On Macintosh and Linux, just use the normal text select and copy commands.

Paste the information into a comment at my blog, http://apprenticealf.wordpress.com/ describing your problem.



Linux Systems Only
-----------------

If you install Kindle for PC in Wine, the plugin should be able to decode files from that Kindle for PC installation under Wine. You might need to enter a Wine Prefix if it's not already set in your Environment variables. You will need to install Python and PyCrypto under Wine as detailed below. In addition, some people who have successfully used the plugin in this way have commented as follows:

Here are the instructions for using Kindle for PC on Linux under Wine. (Thank you Eyeless and Pete)

1. upgrade to very recent versions of Wine; This has been tested with Wine 1.3.15 – 1.3.2X. It may work with earlier versions but no promises. It does not work with wine 1.2.X versions.

If you have not already installed Kindle for PC under wine, follow steps 2 and 3 otherwise jump to step 4

2. Some versions of winecfg have a bug in setting the volume serial number, so create a .windows-serial file at root of drive_c to set a proper windows volume serial number (8 digit hex value for unsigned integer).
cd ~
cd .wine
cd drive_c
echo deadbeef > .windows-serial

Replace "deadbeef" with whatever hex value you want but I would stay away from the default setting of "ffffffff" which does not seem to work. BTW: deadbeef is itself a valid possible hex value if you want to use it

3. Only ***after*** setting the volume serial number properly – download and install under wine K4PC version for Windows. Register it and download from your Archive one of your Kindle ebooks. Versions known to work are K4PC 1.7.1 and earlier. Later version may work but no promises.


FIRST user
----------
Hi everyone, I struggled to get this working on Ubuntu 12.04. Here are the secrets for everyone:

1. Make sure your Wine installation is set up to be 32 bit. 64 bit is not going to work! To do this, remove your .wine directory (or use a different wineprefix). Then use WINEARCH=win32 winecfg

2. But wait, you can’t install Kindle yet. It won’t work. You need to do: winetricks -q vcrun2008 or else you’ll get an error: unimplemented function msvcp90.dll .

3. Now download and install Kindle for PC and download your content as normal.

4. Now download and install Python 2.7 32 bit for Windows from python.org, 32 bit, install it the usual way, and you can now run the Kindle DRM tools.

SECOND USER
-----------
It took a while to figure out that I needed wine 32 bit, plus Python 27 32 bit, plus the winetricks, to get all this working together but once it’s done, it’s great and I can read my Kindle content on my Nook Color running Cyanogenmod!!!
Linux Systems Only:
For all of the following wine installs, use WINEARCH=win32 if you are on x86_64. Also remember that in order to execute a *.msi file, you have to run ‘WINEARCH=win32 wine msiexec /i xxxxx.msi’.
1. Install Kindle for PC with wine.
2. Install ActivePython 2.7.x (Windows x86) with wine from here: http://www.activestate.com/activepython/downloads
3. Install the pycrypto (Windows 32 bit for Python 2.7) module with wine from here: http://www.voidspace.org.uk/python/modules.shtml#pycrypto
4. Install the K4MobiDeDRM plugin into your _Linux_ Calibre installation
Now all Kindle books downloaded from Kindle for PC in Wine will be automatically de-DRM’d when they are added to your _Linux_ Calibre. As always, you can troubleshoot problems by adding a book from the terminal using ‘calibredb add xxxx’.

Or something like that! Hope that helps someone out.


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

