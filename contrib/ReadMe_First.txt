Welcome to the tools!
=====================

This ReadMe_First.txt is meant to give users a quick overview of what is available and how to get started. This document is part of the Tools v6.6.2 archive from Apprentice Harper's github repository: https://github.com/apprenticeharper/DeDRM_tools/

The is archive includes tools to remove DRM from:

 - Kindle ebooks (files from Kindle for Mac/PC* and eInk Kindles**).
 - Adobe Digital Editions (v2.0.1***) ePubs (including Kobo and Google ePubs downloaded to ADE)
 - Kobo kePubs from the Kobo Desktop application
 - Barnes and Noble ePubs
 - Adobe Digital Editions (v2.0.1) PDFs
 - Scuolabooks (Link to solution by Hex)
 - Mobipocket ebooks
 - eReader PDB ebooks
 - Rocket ebooks (source only)

These tools do NOT work with Apple's iBooks FairPlay DRM (see end of this file.)

* With Kindle for PC/Mac 1.19 and later, Amazon included support for their new KFX format. While the tools now include a first attempt at supporting drm removal for KFX format, we recommend using Kindle for PC/Mac 1.17 or earlier which prevents downloads of the new format, as conversions from the olde KF8 format are likely to be more successful.

** Some later Kindles support Amazon's new KFX format. And some books download in a split azw3/azw6 format. For best results, instead of using files downloaded directly to your Kindle, download from Amazon's web site 'for transfer via USB'. This will give you an single file to import. See also the FAQ entry about this.

*** With Adobe Digital Editions 3.0 and later, Adobe have introduced a new, optional, DRM scheme. To avoid this new scheme, you should use Adobe Digital Editions 2.0.1. Some books are required to use the new DRM scheme and so will not download with ADE 2.0.1. If you still want such a book, you will need to use ADE 3.0 or later to download it, but you should remember that no tools to remove Adobe's new DRM scheme exist as of June 2017.

About the tools
---------------
These tools are updated and maintained by Apprentice Harper and many others. You can find the latest updates at Apprentice Harper's github repository https://github.com/apprenticeharper/DeDRM_tools/ and get support by creating an issue at the repository (github account required) or by posting a comment at Apprentice Alf's blog: http://www.apprenticealf.wordpress.com/

If you re-post these tools, a link to the repository and/or the blog would be appreciated.


DeDRM plugin for calibre (Mac OS X, Windows, and Linux)
-------------------------------------------------------
Calibre is an open source freeware ebook library manager. It is the best tool around for keeping track of your ebooks. The DeDRM plugin for calibre provides the simplest way, especially on Windows, to remove DRM from your Kindle and Adobe DRM ebooks. Just install the DeDRM plugin from the DeDRM_calibre_plugin folder, following the instructions and configuration directions provided in the ReadMe file and the help links in the plugin's configuration dialogs.

Once installed and configured, you can simply add a DRM book to calibre and the DRM-free version will be imported into the calibre database. Note that DRM removal only occurs on IMPORT not on CONVERSION or at any other time. If you have already imported DRM books you'll need to remove them from calibre and re-import them.

For instructions, see the DeDRM_plugin_ReadMe.txt file in the DeDRM_calibre_plugin folder.


Obok plugin for calibre (Mac OS X and Windows)
----------------------------------------------
To import ebooks from the Kobo Desktop app or from a Kobo ebook reader, install the Obok plugin. This works in a different way to the DeDRM plugin, in that it finds your ebooks downloaded using the Kobo Desktop app, or on an attached Kobo ebooks reader, and displays them in a list, so that you can choose the ones you want to import into calibre.

For instructions, see the obok_plugin_ReadMe.txt file in the Obok_calibre_plugin folder.


DeDRM application for Mac OS X users: (Mac OS X 10.6 and above)
---------------------------------------------------------------
This application is a stand-alone DRM removal application for Mac OS X users. It is only needed for people who cannot or will not use the calibre plugin. KFX support has not been tested yet.

For instructions, see the "DeDRM ReadMe.rtf" file in the DeDRM_Macintosh_Application folder.


DeDRM application for Windows users: (Windows XP through Windows 10)
------------------------------------------------------------------
***This program requires that Python and PyCrypto be properly installed.***
***See below for details on recommended versions and how to install them.***

This application is a stand-alone application for Windows users. It is only needed for people who cannot or will not use the calibre plugin. KFX support has not been tested yet.

For instructions, see the DeDRM_App_ReadMe.txt file in the DeDRM_Windows_Applications folder.


Other_Tools
-----------
This is a folder of other tools that may be useful for DRMed ebooks from certain sources or for Linux users. Most users won't need any of these tools.

B_and_N_Download_Helper
A Javascript to enable a download button at the B&N website for ebooks that normally won't download to your PC. Only for the adventurous.

DRM_Key_Scripts
This folder contains python scripts that create or extract or fetch encryption keyfiles for Barnes and Noble, Adobe Digital Editions, Kindle for Mac/PC and old versions of Kindle for Android.

Kindle_for_Android_Patches
Definitely only for the adventurous, this folder contains information on how to modify the Kindle for Android app to b able to get a PID for use with the other Kindle tools (DeDRM apps and calibre plugin).

Kobo
Contains the standalone obok python script for removing DRM from kePubs downloaded using the kobo desktop application.

Rocket_ebooks
Information about the now-obsolete Rocket ebook format and DRM, along with source for a tool to remove the DRM.

Scuolabook_DRM
A link to the tool for removing DRM from ScuolaBooks PDFs, created by "Hex".


Windows and Python
------------------
We **strongly** recommend using calibre and the plugin.

If you really want to use the WIndows app or the individual scripts, you'll need to install python.
ActiveState's Active Python 2.7 Community Edition for Windowscan be downloaded for free from:

http://www.activestate.com/activepython/downloads

In addition, Windows Users need PyCrypto:

    There are many places to get PyCrypto installers for Windows. One such place is:

    http://www.voidspace.org.uk/python/modules.shtml

    Please get the latest (currently 2.6) PyCrypto meant for Windows Python version 2.7. Note that the PyCrypto binaries have two version numbers. The first is the PyCrypto version, and the second is the python version that they work with. This can be confusing.

Once Windows users have installed Python 2.7, and the matching PyCrypto, they are ready to run the DeDRM application or individual scripts.

For (experimental) KFX support, you also need LZMA support. LZMA is built-in
in Python 3.3+ but not present in Python 2. Choices are backports.lzma and
pylzma, both of which need compiling. Compiling Python extensions on Windows
requires Visual Studio and is a PITA. The recommended way is to install wheels
(binary) directly.

Windows binary wheels for backports.lzma and pylzma could be found here:

https://www.lfd.uci.edu/~gohlke/pythonlibs/


Apple's iBooks FairPlay DRM
---------------------------

The only tool that removes Apple's iBooks Fairplay DRM is Requiem by Brahms version 3.3.6 and works with iTunes 10.5. Requiem 4.0 and later do not remove DRM from ebooks.

Requiem is no longer developed as of 2012, with the last version 4.1.

You can download it from these download links:

Requiem 3.3.6 for Windows: http://www.datafilehost.com/download-f7916922.html
MD5: 10ab191f2d86c692d57f6a07b4622cf8

Requiem 3.3.6 for Mac OS X: http://www.datafilehost.com/download-47fce8b7.html
MD5: 6d4167d47e6982ddbb8528212198b520

Requiem 3.3.6 source code: http://www.datafilehost.com/download-172920e9.html
MD5: 1636862796d573c693d56bcc526b60bd

No support for requiem is provided at Apprentice Alf's blog or Apprentice Harper's github repository.


Credits
-------
The original inept and ignoble scripts were by i♥cabbages
The original mobidedrm and erdr2pml scripts were by The Dark Reverser
The original topaz DRM removal script was by CMBDTC
The original topaz format conversion scripts were by some_updates, clarknova and Bart Simpson
The original KFX format decryption was by lulzkabulz, converted to python by Apprentice Naomi and integrated into the tools by tomthumb1997

The original obok script was by Physisticated

The alfcrypto library is by some_updates
The ePub encryption detection script is by Apprentice Alf, adapted from a script by Paul Durrant
The ignoblekey script is by Apprentice Harper
The DeDRM plugin was based on plugins by DiapDealer and is maintained by Apprentice Alf and Apprentice Harper
The DeDRM AppleScript was by Paul Durrant and is maintained by Apprentice Alf and Apprentice Harper
The DeDRM python GUI was by some_updates and is maintained by Apprentice Alf and Apprentice Harper

The Scuolabooks tool is by Hex

Many fixes, updates and enhancements to the scripts and applicatons have been made by many other people. For more details, see the comments in the individual scripts.
