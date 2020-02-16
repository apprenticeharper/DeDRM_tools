Welcome to the tools!
=====================

This file is to give users a quick overview of what is available and how to get started. This document is part of the DeDRM Tools archive from Apprentice Harper's github repository: https://github.com/apprenticeharper/DeDRM_tools/

This archive includes calibre plugins to remove DRM from:

 - Kindle ebooks (files from Kindle for Mac/PC and eInk Kindles).
 - Adobe Digital Editions (v2.0.1***) ePubs (including Kobo and Google ePubs downloaded to ADE)
 - Adobe Digital Editions (v2.0.1) PDFs
 - Kobo kePubs from the Kobo Desktop application and attached Kobo readers.

These tools do NOT work with Apple's iBooks FairPlay DRM. Use iBook Copy from TunesKit.
These tools no longer work well with books from Barnes & Noble.

For limitations and work-arounds, see the FAQ at https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md

About the tools
---------------
These tools are updated and maintained by Apprentice Harper and many others. You can find the latest updates at Apprentice Harper's github repository https://github.com/apprenticeharper/DeDRM_tools/ and get support by creating an issue at the repository (github account required) or by posting a comment at Apprentice Alf's blog: http://www.apprenticealf.wordpress.com/

If you re-post these tools, a link to the repository and/or the blog would be appreciated.

The tools are provided in the form of plugins for calibre. Calibre is an open source freeware ebook library manager. It is the best tool around for keeping track of your ebooks.


DeDRM plugin for calibre (Mac OS X, Windows)
-------------------------------------------------------
The DeDRM plugin for calibre removes DRM from your Kindle and Adobe DRM ebooks when they are imported to calibre. Just install the DeDRM plugin (DeDRM_plugin.zip), following the instructions and configuration directions provided in the ReadMe file and the help links in the plugin's configuration dialogs.

Once installed and configured, you can simply add a DRM book to calibre and a DRM-free version will be imported into the calibre database. Note that DRM removal only occurs on IMPORT not on CONVERSION or at any other time. If you have already imported DRMed books you'll need to remove the books from calibre and re-import them.


Obok plugin for calibre (Mac OS X and Windows)
----------------------------------------------
To import ebooks from the Kobo Desktop app or from a Kobo ebook reader, install the Obok plugin. This works in a different way to the DeDRM plugin, in that it finds your ebooks downloaded using the Kobo Desktop app, or on an attached Kobo ebooks reader, and displays them in a list, so that you can choose the ones you want to import into calibre.

For instructions, see the obok_plugin_ReadMe.txt file.


DeDRM application for Mac OS X users: (Mac OS X 10.6 and above)
---------------------------------------------------------------
DeDRM application for Windows users: (Windows XP through Windows 10)
------------------------------------------------------------------
As of Version 6.7 of the tools, these are no longer provided or supported.


Linux support
-------------
It may be possible to use the plugins on a Linux system, but no support is given at this time.


Credits
-------
The original inept and ignoble scripts were by i♥cabbages
The original mobidedrm and erdr2pml scripts were by The Dark Reverser
The original topaz DRM removal script was by CMBDTC
The original topaz format conversion scripts were by some_updates, clarknova and Bart Simpson
The original KFX format decryption was by lulzkabulz, converted to python by Apprentice Naomi and integrated into the tools by tomthumb1997
The alfcrypto library is by some_updates
The DeDRM plugin was based on plugins by DiapDealer and is maintained by Apprentice Alf and Apprentice Harper

The original obok script was by Physisticated
The plugin conversion was done anonymously.
The Kobo reader support was added by norbusan

Fixes, updates and enhancements to the scripts and applicatons have been made by many other anonymous people.
