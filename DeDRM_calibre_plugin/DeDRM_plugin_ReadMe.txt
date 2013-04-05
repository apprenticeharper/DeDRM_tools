DeDRM_plugin.zip
================

This calibre plugin replaces all previous DRM removal plugins. When you install this plugin, the older separate plugins should be removed.

This plugin will remove the DRM from Amazon Kindle ebooks (Mobi, KF8, Topaz and Print Replica), Mobipocket, Adobe Digital Edition ePubs (including Sony and Kobo ePubs), Barnes and Noble ePubs, Adobe Digital Edition PDFs, and Fictionwise eReader ebooks.


Installation
------------
Do NOT select "Get plugins to enhance calibre" as this is reserved for 'official' calibre plugins, instead select "Change calibre behavior" to go to Calibre's Preferences page.  Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (DeDRM_plugin.zip) and click the "Add" button. Click "Yes" in the the "Are you sure?" dialog. Click OK in the "Success" dialog.


Customization
-------------
The keys for ebooks downloaded using Kindle for Mac/PC and Adobe Digital Editions are automatically generated and saved when needed. If all your DRMed ebooks can be opened and read in Kindle for Mac/PC or Adobe Digital Editions on the same computer on which you are running calibre, you do not need to do any configuration of this plugin. (On Linux, Kindle for PC and Adobe Digital Editions along with Python and PyCrypto need to be installed under Wine for this to work, see the Linux section at the end.)

If you have books from other sources (e.g. from an eInk Kindle), highlight the plugin (DeDRM under the "File type plugins" category) and click the "Customize Plugin" button.

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

Instructions for installing Wine, Kindle for PC, Adobe Digital Editions, Python and PyCrypto
--------------------------------------------------------------------------------------------

These instructions have been tested with Wine 1.4 on Ubuntu.

 1. First download the software you're going to to have to install.
    a. Kindle for PC from http://www.amazon.co.uk/gp/kindle/pc/
    b. Adobe Digital Editions 1.7.x from http://helpx.adobe.com/digital-editions/kb/cant-install-digital-editions.html
       (Adobe Digital Editions 2.x doesn't work with Wine.)
    c. ActivePython 2.7.X for Windows (x86) from http://www.activestate.com/activepython/downloads
    d. PyCrypto 2.1 for 32bit Windows and Python 2.7 from http://www.voidspace.org.uk/python/modules.shtml#pycrypto
       (PyCrypto downloads as a zip file. You will need to unzip it.)
 2. Install Wine for 32-bit x86.  (e.g. on Ubuntu, Open the Ubuntu Software Center, search for Wine, and install "Wine Windows Program Loader".)
 3. Run "Configure Wine", which will set up the default 'wineprefix'
 4. Run winetricks, select the default wineprefix and install component vcrun2008
 5. Run the mis-named "Uninstall Wine Software", which also allows installation of software.
 6. Install Kindle for PC. Accept all defaults and register with your Amazon Account.
 7. Install Adobe Digital Editions. Accept all defaults and register with your Adobe ID.
 8. Install ActiveState Python 2.7.x. Accept all defaults.
 9. Install PyCrypto 2.1. Accept all defaults.


Instructions for getting Kindle for PC and Adobe Digital Editions default decryption keys
-----------------------------------------------------------------------------------------

If everything has been installed in wine as above, the keys will be retrieve automatically.

If you have a more complex wine installation, you may enter the appropriate WINEPREFIX in the configuration dialogs for Kindle for PC and Adobe Digital Editions. You can also test that you have entered the WINEPREFIX correctly by trying to add the default keys to the preferences by clicking on the green plus button in the configuration dialogs.
