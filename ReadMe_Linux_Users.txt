ReadMe for Linux Users and the Tools


Linux and Kindle for PC (KindleBooks.pyw)
------------------------------------------

Here are the instructions for using Kindle for PC and KindleBooks.pyw on Linux under Wine. (Thank you Eyeless and Pete)

1. upgrade to very recent versions of Wine; This has been tested with Wine 1.3.15 – 1.3.2X. It may work with earlier versions but no promises.  It does not work with wine 1.2.X versions.

If you have not already installed Kindle for PC under wine, follow steps 2 and 3 otherwise jump to step 4

2. Some versions of winecfg have a bug in setting the volume serial number, so create a .windows-serial file at root of drive_c to set a proper windows volume serial number (8 digit hex value for unsigned integer).
cd ~
cd .wine
cd drive_c
echo deadbeef > .windows-serial 

Replace "deadbeef" with whatever hex value you want but I would stay away from the default setting of "ffffffff" which does not seem to work.  BTW: deadbeef is itself a valid possible hex value if you want to use it

3. Only ***after*** setting the volume serial number properly – download and install under wine K4PC version for Windows. Register it and download from your Archive one of your Kindle ebooks. Versions known to work are K4PC 1.7.1 and earlier. Later version may work but no promises.

4. Download and install under wine ActiveState Active Python 2.7 for Windows 32bit

5. Download and unzip tools_v4.X.zip

6. Now make sure the executable bit is NOT set for KindleBooks.pyw as Linux will actually keep trying to ignore wine and launch it under Linux python which will cause it to fail.

cd tools_v4.7/KindleBooks/
chmod ugo-x KindleBooks.pyw

7. Then run KindleBook.pyw ***under python running on wine*** using the Linux shell as follows:

wine python KindleBooks.pyw

Select the ebook file directly from your “My Kindle Content” folder, select a new/unused directory for the output. You should not need to enter any PID or Serial Number for Kindle for PC.






Linux and Adobe Digital Editions ePubs
--------------------------------------

Here are the instructions for using the tools with ePub books and Adobe Digital Editions on Linux under Wine. (Thank you mclien!)


1. download the most recent version of wine from winehq.org (1.3.29 in my case)

For debian users: 

to get a recent version of wine I decited to use aptosid (2011-02, xfce)
(because I’m used to debian)
install aptosid and upgrade it (see aptosid site for detaild instructions)


2. properly install Wine (see the Wine site for details)

For debian users:

cd to this dir and install the packages as root:
‘dpkg -i *.deb’ 
you will get some error messages, which can be ignored.
again as root use
‘apt-get -f install’ to correct this errors

3. python 2.7 should already be installed on your system but you may need the following additional python package

'apt-get install python-tk’

4. all programms need to be installed as normal user. All these programm are installed the same way:
‘wine ‘
we need:
a) Adobe Digital Edition 1.7.2(from: http://kb2.adobe.com/cps/403/kb403051.html)
(there is a “can’t install ADE” site, where the setup.exe hides)
b) ActivePython-2.7.2.5-win32-x86.msi (from: http://www.activestate.com/activepython/downloads)
c) Win32OpenSSL_Light-0_9_8r.exe (from: http://www.slproweb.com/)
d) pycrypto-2.3.win32-py2.7.msi (from: http://www.voidspace.org.uk/python/modules.shtml)

5. now get and unpack the very latest tools_v4.X (from Apprentice Alf) in the users drive_c of wine
(~/.wine/drive_c/)

6.  start ADE with:
‘wine digitaleditions.exe’ or from the start menue wine-adobe-digital..

7. register this instance of ADE with your adobeID and close it
 change to the tools_v4.X dir:
cd ~/.wine/drive_c/tools_v4.X/Adobe_ePub_Tools

8. create the adeptkey.der with:
‘wine python ineptkey_v5.4.pyw’ (only need once!)
(key will be here: ~/.wine/drive_c/tools_v4.X/Adobe_ePub_Tools/adeptkey.der)

9. Use ADE running under Wine to dowload all of your purchased ePub ebooks

10. for each book you have downloaded via Adobe Digital Editions
There is no need to use Wine for this step!

'python ineptpub_v5.6.pyw’
this will launch a window with 3 lines
1. key: (allready filled in, otherwise it’s in the path where you did step 8.
2. input file: drmbook.epub
3. output file: name-ypu-want_for_free_book.epub

Also… once you successfully generate your adept.der keyfile using WINE, you can use the regular ineptepub plugin with the standard Linux calibre. Just put the *.der file(s) in your calibre configuration directory.
so if you want you can use calibre in Linux:

11.  install the plugins from the tools as discribed in the readmes for win

12.  copy the adeptkey.der into the config dir of calibre (~/.config/calibre in debian). Every book imported to calibre will automaticly freed from DRM.


