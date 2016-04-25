DeDRM_plugin.zip
================

This calibre plugin replaces all previous DRM removal plugins. Before you install this plugin, you should uninstall any older individual DRM removal plugins, e.g. K4MobiDeDRM.

This plugin will remove the DRM from Amazon Kindle ebooks (Mobi, KF8, Topaz and Print Replica), Mobipocket, Adobe Digital Edition ePubs (including Sony and Kobo ePubs), Barnes and Noble (nook) ePubs, Adobe Digital Edition PDFs, and Fictionwise eReader ebooks.


Installation
------------
Open the Preferences menu.

![Preferences menu](http://i.imgur.com/N9v6ZuL.png)

Under "Advanced", select the option for "Plugins".

![Select plugins](http://i.imgur.com/8zTVXgI.png)

Click "Load plugin from file" in the bottom right corner.

![](http://i.imgur.com/k4PB88a.png)

Browse to the location of the downloaded plugin zip file - `DeDRM_plugin.zip`.
You will get two popup dialogs for installing the plugin. Say "Yes" and "Ok", respectively.

![Are you sure?](http://i.imgur.com/TB54DXC.png)

![Success](http://i.imgur.com/j0T7J2i.png)

Once the plugin is successfully loaded, the DeDRM plugin will appear under "File type plugins".

![File type plugins](http://i.imgur.com/R1XkJ8d.png)

Customization
-------------
The keys for ebooks downloaded using Kindle for Mac/PC, Adobe Digital Editions and NOOK Study are automatically generated and saved when needed. If all your DRMed ebooks can be downloaded and read in Kindle for Mac/PC, Adobe Digital Editions or NOOK Study on the same computer and user account on which you are running calibre, you do not need to do add any customisation data to this plugin. (Linux users should see the Linux section at the end of this ReadMe.)

If you have books from other sources (e.g. from an eInk Kindle), highlight the plugin (DeDRM under the "File type plugins" category) and click the "Customize Plugin" button.

The buttons in the configuration dialog will open individual configuration dialogs that will allow you to enter the needed information, depending on the type and source of your DRMed eBooks. Additional help on the information required is available in each of the the dialogs.

If you have used previous versions of the various DeDRM plugins on this machine, you may find that some of the configuration dialogs already contain the information you entered through those previous plugins.

When you have finished entering your configuration information, you must click the OK button to save it. If you click the Cancel button, all your changes in all the configuration dialogs will be lost.


Troubleshooting
---------------
If you find that it's not working for you (imported ebooks still have DRM - that is, they won't convert or open in the calibre ebook viewer), you should make a log of import process by deleting the DRMed ebook from calibre and then adding the ebook to calibre when it's running in debug mode. This will generate a lot of helpful debugging info that can be copied into any online help requests. Here's how to do it:

On Windows, open a terminal/command window. (Start/Run… and then type 'cmd.exe' (without the 's) as the program to run).
On Macintosh, open the Terminal application (in your Utilities folder).
On Linux open a command window. Hopefully all Linux users know how to do this.

You should now have a text-based command-line window open.

Type in "calibre-debug -g" (without the "s but with the space before the -g) and press the return/enter key. Calibre will launch and run as normal, but with debugging information output to the terminal window.

Import the DRMed eBook into calibre in any of the the normal ways. (I usually drag&drop onto the calibre window.)

Debug information will be written to the terminal window.

Copy the output from the terminal window.
On Windows, you must use the window menu (little icon at left of window bar) to select all the text and then to copy it.
On Macintosh and Linux, just use the normal text select and copy commands.

Paste the information into a comment at my blog, http://apprenticealf.wordpress.com/ describing your problem.


Credits
-------
The original inept and ignoble scripts were by i♥cabbages
The original mobidedrm and erdr2pml scripts were by The Dark Reverser
The original topaz DRM removal script was by CMBDTC
The original topaz format conversion scripts were by some_updates, clarknova and Bart Simpson
The original obok script was by Physisticated

The alfcrypto library is by some_updates
The ePub encryption detection script is by Apprentice Alf, adapted from a script by Paul Durrant
The ignoblekey script is by Apprentice Harper
The DeDRM plugin was based on plugins by DiapDealer and is maintained by Apprentice Alf and Apprentice Harper

Many fixes, updates and enhancements to the scripts and applicatons have been made by many other people. For more details, see the commments in the individual scripts.


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

If everything has been installed in wine as above, the keys will be retrieved automatically.

If you have a more complex wine installation, you may enter the appropriate WINEPREFIX in the configuration dialogs for Kindle for PC and Adobe Digital Editions. You can also test that you have entered the WINEPREFIX correctly by trying to add the default keys to the preferences by clicking on the green plus button in the configuration dialogs.
