From Apprentice Alf's Blog

Adobe Adept PDF, .pdf

This directory includes modified versions of the I♥CABBAGES Adobe Adept inept scripts for pdfs.  These scripts have been modified to work with OpenSSL on Windows as well as Linux and Mac OS X.  If a Windows User has OpenSSL installed, these scripts will make use of it in place of PyCrypto.

The wonderful I♥CABBAGES has produced scripts that will remove the DRM from ePubs and PDFs encryped with Adobe’s DRM. These scripts require installation of the PyCrypto python package *or* the OpenSSL library on Windows.  For Mac OS X and Linux boxes, these scripts use the already installed OpenSSL libcrypto so there is no additional requirements for these platforms.

For more info, see the author's blog:
http://i-u2665-cabbages.blogspot.com/2009_02_01_archive.html

There are two scripts:

The first is called ineptkey_vX.X.pyw.  Simply double-click to launch it and it will create a key file that is needed later to actually remove the DRM.  This script need only be run once unless you change your ADE account information.

The second is called in ineptpdf_vX.X.pyw.  Simply double-click to launch it.  It will ask for your previously generated key file and the path to the book you want to remove the DRM from.

Both of these scripts are gui python programs.   Python 2.X (32 bit) is already installed in Mac OSX.  We recommend ActiveState's Active Python Version 2.X (32 bit) for Windows users.
