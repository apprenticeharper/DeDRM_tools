DeDRM_plugin.zip
================

This calibre plugin replaces many previously separate DRM removal plugins. Before you install this plugin, you should uninstall any older individual DRM removal plugins, e.g. K4MobiDeDRM. The exception is the obok plugin, which should not be removed.

This plugin will remove the DRM from
 - Kindle ebooks (from Kindle for Mac/PC and eInk Kindles).
 - Barnes and Noble ePubs
 - Adobe Digital Editions (v2.0.1*) ePubs (including Kobo and Google ePubs downloaded to ADE)
 - Adobe Digital Editions (v2.0.1) PDFs
 - Mobipocket ebooks
 - eReader PDB books
 
These tools do NOT work with kepubs downloaded using Kobo's desktop app (see the separate obok plugin) nor Apple's iBooks FairPlay DRM (see details about Requiem at the end of this file.)

* With Adobe Digital Editions 3.0 and later, Adobe have introduced a new, optional, DRM scheme. To avoid this new scheme, you should use Adobe Digital Editions 2.0.1. Some books are required to use the new DRM scheme and so will not download with ADE 2.0.1. If you still want such a book, you will need to use ADE 3.0 or later to download it, but you should remember that no tools to remove Adobe's new DRM scheme exist as of June 2016.


Installation
------------
Open calibre's Preferences dialog.  Click on the "Plugins" button.  Next, click on the button, "Load plugin from file".  Navigate to the unzipped DeDRM_tools folder and, in the folder "DeDRM_calibre_plugin", find the file "DeDRM_plugin.zip".  Click to select the file and select "Open".  Click "Yes" in the "Are you sure?" dialog box. Click the "OK" button in the "Success" dialog box.


Customization
-------------
You MUST add some key information for the following kinds of ebooks:
 - Kindle ebooks from an E-Ink based Kindle (e.g. Voyage).
 - Barnes & Noble ePubs other than those downloaded using NOOK Study
 - Mobipocket ebooks
 - eReader PDB books
 
 You do not need to add any key information for eBooks
  - downloaded using Kindle for Mac/PC
  - downloaded using Adobe Digital Editions (v2.0.1)
  - downloaded using NOOK Study
 as the necessary keys are automatically retrieved from files on your computer.

 To add needed key information for other books, highlight the plugin (DeDRM under the "File type plugins" category) and click the "Customize Plugin" button.

The buttons in the configuration dialog will open individual configuration dialogs that will allow you to enter the needed information, depending on the type and source of your DRMed eBooks. Additional help on the information required is available in each of the the dialogs vias the [?] help button.

If you have used previous versions of the various DeDRM plugins on this machine, you may find that some of the configuration dialogs already contain the information you entered through those previous plugins.

When you have finished entering your configuration information, you must click the OK button to save it. If you click the Cancel button, all your changes in all the configuration dialogs will be lost.


Troubleshooting
---------------
If you find that the DeDRM plugin  is not working for you (imported ebooks still have DRM - that is, they won't convert or open in the calibre ebook viewer), you should make a log of the import process by deleting the DRMed ebook from calibre and then adding the ebook to calibre when it's running in debug mode. This will generate a lot of helpful debugging info that can be copied into any online help requests. Here's how to do it:

 - Remove the DRMed book from calibre. 
 - Click the Preferences drop-down menu and choose 'Restart in debug mode'. 
 - Once calibre has re-started, import the problem ebook.
 - Now close calibre.

A log will appear that you can copy and paste into a comment at Apprentice Alf's blog, http://apprenticealf.wordpress.com/ . You should also give details of your computer, and how you obtained the ebook file.


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
