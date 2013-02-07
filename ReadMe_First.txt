Welcome to the tools!
=====================

This ReadMe_First.txt is meant to give users a quick overview of what is available and how to get started. This document is part of the Tools v5.6.2 archive.

The is archive includes tools to remove DRM from:

 - Kindle ebooks (Mobi, Topaz, Print Replica and KF8).
 - Barnes and Noble ePubs
 - Adobe Digital Editions ePubs (including Sony and Kobo ePubs downloaded to ADE)
 - Adobe Digital Editions PDFs
 - Mobipocket ebooks
 - eReader PDB books
 - Scuolabooks (Windows only solution by Hex)

These tools do NOT work with Apple's iBooks FairPlay DRM (see end of this file.)


About the tools
---------------
These tools have been updated and maintained by Apprentice Alf, DiapDealer and some_updates.

You can find the latest updates and get support at Apprentice Alf's blog: http://www.apprenticealf.wordpress.com/

If you re-post these tools, a link to the blog would be appreciated.

The original inept and ignoble scripts were by i♥cabbages
The original mobidedrm and erdr2pml scripts were by The Dark Reverser
The original topaz DRM removal script was by CMBDTC
The original topaz format conversion scripts were by some_updates, clarknova and Bart Simpson
The Scuolabooks tool is by Hex

The calibre plugin conversions were originally by DiapDealer
The DeDRM AppleScript application was by Apprentice Alf
The DeDRM python GUI was by some_updates

Many fixes, updates and enhancements to the scripts and applicatons have been by Apprentice Alf, some_updates and DiapDealer.


Calibre Users (Mac OS X, Windows, and Linux)
--------------------------------------------
If you are a calibre user, the quickest and easiest way, especially on Windows, to remove DRM from your ebooks is to install the relevant plugins from the Calibre_Plugins folder, following the instructions and configuration directions provided in each plugin's ReadMe file.

Once installed and configured, you can simply add a DRM book to calibre and the DeDRMed version will be imported into the calibre database. Note that DRM removal ONLY occurs on import. If you have already imported DRM books you'll need to remove them from calibre and re-import them.

These plugins work for Windows, Mac OS X and Linux. For ebooks from Kindle 4 PC and Adobe Digital Editions, Linux users should read the section at the end of this ReadMe.



DeDRM application for Mac OS X users: (Mac OS X 10.4 and above)
----------------------------------------------------------------------
This application combines all the tools into one easy-to-use tool for Mac OS X users.

Drag the "DeDRM 5.6.2.app" application from the DeDRM_Applications/Macintosh folder to your Desktop (or your Applications Folder, or anywhere else you find convenient). Double-click on the application to run it and it will guide you through collecting the data it needs to remove the DRM from any of the kinds of DRMed ebook listed in the first section of this ReadMe.

To use the DeDRM application, simply drag ebooks, or folders containing ebooks, onto the DeDRM application and it will remove the DRM of the kinds listed above.

For more detailed instructions, see the "DeDRM ReadMe.rtf" file in the DeDRM_Applications/Macintosh folder, including details of the extra step that Mac OS X 10.4 users need to take to use the application.




DeDRM application for Windows users: (Windows XP through Windows 8)
------------------------------------------------------------------
***This program requires that Python and PyCrypto be properly installed.***
***See below for details on recommended versions are where to get them.***

This application combines all the tools into one easy-to-use tool for Windows users.

Drag the DeDRM_5.6.2 folder that's in the DeDRM_Applications/Windows folder, to your "My Documents" folder (or anywhere else you find convenient). Make a short-cut on your Desktop of the DeDRM_Drop_Target.bat file that's in the DeDRM_5.6.2 folder. Double-click on the shortcut and the DeDRM application will run and guide you through collecting the data it needs to remove the DRM from any of the kinds of DRMed ebook listed in the first section of this ReadMe.

To use the DeDRM application, simply drag ebooks, or folders containing ebooks, onto the DeDRM_Drop_Target.bat shortcut and it will remove the DRM of the kinds listed above.

For more detailed instructions, see the DeDRM_ReadMe.txt file in the DeDRM_Applications/Windows folder.



Other_Tools
-----------
This folder includes three non-python tools:

Kindle_for_Android_Patches

Definitely only for the adventurous, this folder contains information on how to modify the Kindel for Android app to b able to get a PID for use with the other Kindle tools (DeDRM apps and calibre plugin).

B&N_Download_Helper

A Javascript to enable a download button at the B&N website for ebooks that normally won't download to your PC. Another one only for the adventurous.

Scuolabook_DRM

A windows-only application (including source code) for removing DRM from ScuolaBooks PDFs, created by "Hex" and included with permission.




Windows and Python
------------------
We **strongly** recommend ActiveState's Active Python 2.7 Community Edition for Windows (x86) 32 bits. This can be downloaded for free from:

http://www.activestate.com/activepython/downloads

We do **NOT** recommend the version of Python from python.org.

The version from python.org is not as complete as most normal Python installations on Linux and even Mac OS X. It is missing various Windows specific libraries, does not install the default Tk Widget kit (for graphical user interfaces) unless you select it as an option in the installer, and does not properly update the system PATH environment variable. Therefore using the default python.org build on Windows is simply an exercise in frustration for most Windows users.

In addition, Windows Users need one of PyCrypto OR OpenSSL. Because of potential conflicts with other software, we recommend using PyCrypto.

For PyCrypto:

    There are many places to get PyCrypto installers for Windows. One such place is:

    http://www.voidspace.org.uk/python/modules.shtml

    Please get the latest PyCrypto meant for Windows 32 bit that matches the version of Python you installed (2.7)

For OpenSSL:

    Win32 OpenSSL v0.9.8o (8Mb)
    http://www.slproweb.com/download/Win32OpenSSL-0_9_8o.exe
    (if you get an error message about missing Visual C++
    redistributables... cancel the install and install the
    below support program from Microsoft, THEN install OpenSSL)

    Visual C++ 2008 Redistributables (1.7Mb)
    http://www.microsoft.com/downloads/details.aspx?familyid=9B2DA534-3E03-4391-8A4D-074B9F2BC1BF

Once Windows users have installed Python 2.X for 32 bits, and the matching OpenSSL OR PyCrypto pieces, they too are ready to run a DeDRM application.



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
