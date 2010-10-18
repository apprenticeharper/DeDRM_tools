From Apprentice Alf's Blog

Adobe Adept ePub and PDF, .epub, .pdf

The wonderful I♥CABBAGES has produced scripts that will remove the DRM from ePubs and PDFs encryped with Adobe’s DRM. Installing these scripts is a little more complex that the Mobipocket and eReader decryption tools, as they require installation of the PyCrypto package for Windows Boxes.  For Mac OS X and Linux boxes, these scripts use the already installed OpenSSL libcrypto so there is no additional requirements for these platforms.

For more info, see the author's blog:
http://i-u2665-cabbages.blogspot.com/2009_02_01_archive.html

There are two scripts:

The first is called ineptkey_v5.pyw.  Simply double-click to launch it and it will create a key file that is needed later to actually remove the DRM.  This script need only be run once unless you change your ADE account information.

The second is called in ineptepub_v5.pyw.  Simply double-click to launch it.  It will ask for your previously generated key file and the path to the book you want to remove the DRM from.


Both of these scripts are gui python programs.   Python 2.X (32 bit) is already installed in Mac OSX.  We recommend ActiveState's Active Python Version 2.X (32 bit) for Windows users.

The latest version of ineptpdf to use is version 8.4.42, which improves support for some PDF files. 

ineptpdf version 8.4.42 can be found here: 

http://pastebin.com/kuKMXXsC

It is not included in the tools archive.

If that link is down, please check out the following website for some of the latest releases of these tools:

http://ainept.freewebspace.com/
