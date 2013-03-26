DeDRM_plugin.zip
================

This calibre plugin replaces all previous DRM removal plugins. When you install this plugin, the older separate plugins should be removed.

This plugin will remove the DRM from Amazon Kindle ebooks (Mobi, KF8, Topaz and Print Replica), Mobipocket, Adobe Digital Edition ePubs (including Kobo ePubs), Barnes and Noble ePubs, Adobe Digital Edition PDFs, and Fictionwise eReader ebooks.


Installation
------------
Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior" to go to Calibre's Preferences page.  Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (DeDRM_plugin.zip) and click the 'Add' button. Click 'Yes' in the the "Are you sure?" dialog. Click OK in the "Success" dialog.


Customization
-------------
On Windows and Mac, the keys for ebooks downloaded for Kindle for Mac/PC and Adobe Digital Editions are automatically generated. If all your DRMed ebooks can be opened and read in Kindle for Mac/PC and/or Adobe Digital Editions on the same computer on which you are running calibre, you do not need to do any configuration of this plugin. On Linux, keys for Kindle for PC and Adobe Digital Editions need to be generated separately (see Linux systems section)

Otherwise, highlight the plugin (DeDRM under the "File type plugins" category) and click the "Customize Plugin" button.

The buttons in the configuration dialog will open individual configuration dialogs that will allow you to enter the needed information, depending on the type and source of your DRMed eBooks. Additional help on the information required is available in each of the the dialogs.

If you have used previous versions of the various DeDRM plugins on this machine, you may find that some of the configuration dialogs already contain the information you entered through those previous plugins.

When you have finished entering your configuration information, you must click the OK button to save it. If you click the Cancel button, all your changes in all the configuration dialogs will be lost.


Troubleshooting
---------------
If you find that it's not working for you (imported ebooks still have DRM), you can save a lot of time and trouble by deleting the DRMed ebook from calibre and then trying to add the ebook to calibre in debug mode with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests.

On Macintosh only you must first run calibre, open Preferences, open Miscellaneous, and click on the “Install command line tools” button. (On Windows and Linux the command line tools are installed automatically.)

On Windows, open a terminal/command window. (Start/Run… and then type 'cmd' (without the 's) as the program to run).
On Macintosh, open the Terminal application (in your Utilities folder).
On Linux open a command window. Hopefully all Linux users know how to do this.

You should now have a text-based command-line window open.

Type in "calibre-debug -g" (without the ") and press the return/enter key. Calibre will launch and run as normal, but with debugging information output to the terminal window.

Import the drmed eBook into calibre in any of the the normal ways. (I usually drag&drop onto the calibre window.)

More debug information will be written to the terminal window.

Copy the output from the terminal window.
On Windows, you must use the window menu (little icon at left of window bar) to select all the text and then to copy it.
On Macintosh and Linux, just use the normal text select and copy commands.

Paste the information into a comment at my blog, http://apprenticealf.wordpress.com/ describing your problem.


Credits
-------
The mobidedrm and erdr2pml scripts were created by The Dark Reverser
The ignobleepub, ignoblekeygen, ineptepub and adobe key scripts were created by i♥cabbages
The k4mobidedrm script and supporting scripts were written by some_updates with help from DiapDealer and Apprentice Alf, based on code by Bart Simpson (aka Skindle), CMBDTC and clarknova
The alfcrypto library was created by some_updates
The ePub encryption detection script was adapted by Apprentice Alf from a script by Paul Durrant
The DeDRM all-in-one AppleScript was created by Apprentice Alf
The DeDRM all-in-one python script was created by some_updates and Apprentice Alf




Linux Systems Only
==================

Generating decryption keys for Adobe Digital Editions and Kindle for PC
-----------------------------------------------------------------------
If you install Kindle for PC and/or Adobe Digital Editions in Wine, you will be able to download DRMed ebooks to them under Wine. To be able to remove the DRM, you will need to generate key files and add them in the plugin's customisation dialogs.

To generate the key files you will need to install Python and PyCrypto under the same Wine setup as your Kindle for PC and/or Adobe Digital Editions installations. (Kindle for PC, Python and Pycrypto installation instructions are below.)

Once everything's installed under Wine, you'll need to run the adobekey.pyw script (for Adobe Digital Editions) and kindlekey.pyw (For Kindle for PC) using the python installation in your Wine system. The scripts can be found in Other_Tools/Key_Retrieval_Scripts.

Each script will create a key file in the same folder as the script. Copy the key files to your Linux system and use the plugin customisation dialog in calibre to load the key files.


Instructions for installing Kindle for PC on Linux under Wine. (Thank you Eyeless and Pete)
-------------------------------------------------------------------------------------------
1. upgrade to very recent versions of Wine; This has been tested with Wine 1.3.15 – 1.3.2X. It may work with earlier versions but no promises. It does not work with wine 1.2.X versions.

If you have not already installed Kindle for PC under wine, follow steps 2 and 3 otherwise jump to step 4

2. Some versions of winecfg have a bug in setting the volume serial number, so create a .windows-serial file at root of drive_c to set a proper windows volume serial number (8 digit hex value for unsigned integer).
cd ~
cd .wine
cd drive_c
echo deadbeef > .windows-serial

Replace "deadbeef" with whatever hex value you want but I would stay away from the default setting of "ffffffff" which does not seem to work. BTW: deadbeef is itself a valid possible hex value if you want to use it

3. Only ***after*** setting the volume serial number properly – download and install under wine K4PC version for Windows. Register it and download from your Archive one of your Kindle ebooks.


More such Instructions
----------------------
Hi everyone, I struggled to get this working on Ubuntu 12.04. Here are the secrets for everyone:

1. Make sure your Wine installation is set up to be 32 bit. 64 bit is not going to work! To do this, remove your .wine directory (or use a different wineprefix). Then use WINEARCH=win32 winecfg

2. But wait, you can’t install Kindle yet. It won’t work. You need to do: winetricks -q vcrun2008 or else you’ll get an error: unimplemented function msvcp90.dll .

3. Now download and install Kindle for PC and download your content as normal.

4. Now download and install Python 2.7 32 bit for Windows from python.org, 32 bit, install it the usual way, and you can now run the Kindle DRM tools.


Yet more such Instructions
--------------------------
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

