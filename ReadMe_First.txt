Welcome to the tools!
=====================

This ReadMe_First.txt is meant to give users a quick overview of what is available and how to get started. This document is part of the Tools v6.3.4 archive from Apprentice Alf's Blog: http://apprenticealf.wordpress.com/

The is archive includes tools to remove DRM from:

 - Kindle ebooks (from Kindle for Mac/PC, eInk Kindles and Kindle for Android).
 - Barnes and Noble ePubs
 - Adobe Digital Editions ePubs (including Kobo and Google ePubs downloaded to ADE)
 - Kobo kePubs from the Kobo Desktop application
 - Adobe Digital Editions PDFs
 - Mobipocket ebooks
 - eReader PDB books
 - Scuolabooks (Windows only solution by Hex)

These tools do NOT work with Apple's iBooks FairPlay DRM (see end of this file.)


About the tools
---------------
These tools are updated and maintained by Apprentice Alf and Apprentice Harper. You can find links to the latest updates and get support at Apprentice Alf's blog: http://www.apprenticealf.wordpress.com/
If you re-post these tools, a link to the blog would be appreciated.


DeDRM plugin for calibre (Mac OS X, Windows, and Linux)
-------------------------------------------------------
Calibre is an open source freeware ebook library manager. It is the best tool around for keeping track of your ebooks. The DeDRM plugin for calibre provides the simplest way, especially on Windows, to remove DRM from your ebooks. Just install the DeDRM plugin from the DeDRM_calibre_plugin folder, following the instructions and configuration directions provided in the ReadMe and the help links.

Once installed and configured, you can simply add a DRM book to calibre and the DeDRMed version will be imported into the calibre database. Note that DRM removal only occurs on IMPORT not on CONVERSION or at any other time, not even conversion to other formats. If you have already imported DRM books you'll need to remove them from calibre and re-import them.

Linux users should read the section at the end the DeDRM_plugin_ReadMe.txt file.


DeDRM application for Mac OS X users: (Mac OS X 10.4 and above)
---------------------------------------------------------------
This application is a stand-alone DRM removal application for Mac OS X users.

For instructions, see the "DeDRM ReadMe.rtf" file in the DeDRM_Macintosh_Application folder.

N.B. Mac OS X 10.4 users need to take extra steps before using the application, see the ReadMe.


DeDRM application for Windows users: (Windows XP through Windows 8)
------------------------------------------------------------------
***This program requires that Python and PyCrypto be properly installed.***
***See below for details on recommended versions and how to install them.***

This application is a stand-alone application for Windows users.

For instructions, see the DeDRM_App_ReadMe.txt file in the DeDRM_Windows_Applications folder.


Obok plugin for calibre (Mac OS X, Windows)
-------------------------------------------
This plugin allows you to import kePub ebooks from your kobo desktop application. It is separate from the DeDRM application because it has to work in a different way. It will find all the books downloaded to your kobo desktop application, and let you choose which ones to import, removing the DRM as they are imported.

For instructions, see the obok_plugin_ReadMe.txt file in the Obok_calibre_plugin folder.


Other_Tools
-----------
This is a folder of other tools that may be useful for DRMed ebooks from certain sources or for Linux users. Most users won't need any of these tools.

B_and_N_Download_Helper
A Javascript to enable a download button at the B&N website for ebooks that normally won't download to your PC. Only for the adventurous.

DRM_Key_Scripts
This folder contains python scripts that create or extract or fetch encryption keyfiles for Barnes and Noble ePubs, Adobe Digital Editions ePubs, Kindle for Mac/PC and Kindle for Android ebooks.

Kindle_for_Android_Patches
Definitely only for the adventurous, this folder contains information on how to modify the Kindle for Android app to b able to get a PID for use with the other Kindle tools (DeDRM apps and calibre plugin). This is now of historical interest only, as Android support has now been added to the tools more simply.

Kobo
Contains the standalone obok python script for removing DRM from kePubs downloaded using the kobo desktop application.

Rocket_ebooks
Information about the now-obsolete Rocket ebook format and DRM, along with source for a tool to remove the DRM.

Scuolabook_DRM
A windows-only application (including source code) for removing DRM from ScuolaBooks PDFs, created by "Hex" and included with permission.


Windows and Python
------------------
We **strongly** recommend ActiveState's Active Python 2.7 Community Edition for Windows. This can be downloaded for free from:

http://www.activestate.com/activepython/downloads

We do **NOT** recommend the version of Python from python.org as it is missing various Windows specific libraries, does not install the Tk Widget kit (for graphical user interfaces) by default, and does not properly update the system PATH environment variable. Therefore using the default python.org build on Windows is simply an exercise in frustration for most Windows users.

In addition, Windows Users need one of PyCrypto OR OpenSSL. Because of potential conflicts with other software, we recommend using PyCrypto.

For PyCrypto:

    There are many places to get PyCrypto installers for Windows. One such place is:

    http://www.voidspace.org.uk/python/modules.shtml

    Please get the latest (currently 2.6) PyCrypto meant for Windows Python version 2.7

For OpenSSL:

    Win32 OpenSSL v0.9.8o (8Mb)
    http://www.slproweb.com/download/Win32OpenSSL-0_9_8o.exe
    (if you get an error message about missing Visual C++
    redistributables... cancel the install and install the
    below support program from Microsoft, THEN install OpenSSL)

    Visual C++ 2008 Redistributables (1.7Mb)
    http://www.microsoft.com/downloads/details.aspx?familyid=9B2DA534-3E03-4391-8A4D-074B9F2BC1BF

Once Windows users have installed Python 2.7, and the matching OpenSSL OR PyCrypto pieces, they are ready to run the DeDRM application or individual scripts.



Apple's iBooks FairPlay DRM
---------------------------

The only tool that removes Apple's iBooks Fairplay DRM is Requiem by Brahms version 3.3.6 and works with iTunes 10.5. Requiem 4.0 and later do not remove DRM from ebooks.

Requiem has a Tor website: http://tag3ulp55xczs3pn.onion. To reach the site using Tor, you will need to install Tor (http://www.torproject.org). If you're willing to sacrifice your anonymity, you can use the regular web with tor2web. Just go to http://tag3ulp55xczs3pn.tor2web.com.

Alternatively, you can download it from these download links:

Requiem 3.3.6 for Windows: http://www.datafilehost.com/download-f7916922.html
MD5: 10ab191f2d86c692d57f6a07b4622cf8

Requiem 3.3.6 for Mac OS X: http://www.datafilehost.com/download-47fce8b7.html
MD5: 6d4167d47e6982ddbb8528212198b520

Requiem 3.3.6 source code: http://www.datafilehost.com/download-172920e9.html
MD5: 1636862796d573c693d56bcc526b60bd

If you have any problems with Requiem, I suggest you contact Brahms directly through their Tor website.

No support for requiem is provided at Apprentice Alf's blog.


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
The DeDRM AppleScript was by Paul Durrant and is maintained by Apprentice Alf and Apprentice Harper
The DeDRM python GUI was by some_updates and is maintained by Apprentice Alf and Apprentice Harper

The Scuolabooks tool is by Hex

Many fixes, updates and enhancements to the scripts and applicatons have been made by many other people. For more details, see the commments in the individual scripts.
