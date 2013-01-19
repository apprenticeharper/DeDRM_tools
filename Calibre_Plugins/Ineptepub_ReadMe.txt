Inept Epub DeDRM - ineptepub_v02.1_plugin.zip
=============================================

All credit given to i♥cabbages for the original standalone scripts. I had the much easier job of converting them to a Calibre plugin.

This plugin is meant to decrypt Adobe Digital Edition Epubs that are protected with Adobe's Adept encryption. It is meant to function without having to install any dependencies... other than having Calibre installed, of course. It will still work if you have Python and PyCrypto already installed, but they aren't necessary.


Installation
------------

Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior" to go to Calibre's Preferences page.  Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (ineptepub_v02.1_plugin.zip) and click the 'Add' button. Click 'Yes' in the the "Are you sure?" dialog. Click OK in the "Success" dialog.



Customization
-------------

When first run, the plugin will attempt to find your Adobe Digital Editions installation (on Windows and Mac OS). If successful, it will create 'calibre-adeptkey[number].der' file(s) and save them in Calibre's configuration directory. It will use those files and any other '*.der' files in any decryption attempts. If there is already at least one 'calibre-adept*.der' file in the directory, the plugin won't attempt to find the Adobe Digital Editions installation keys again.

So if you have Adobe Digital Editions installation installed on the same machine as Calibre... you are ready to go. If not... keep reading.

If you already have keyfiles generated with i♥cabbages' ineptkey.pyw script, you can put those keyfiles in Calibre's configuration directory. The easiest way to find the correct directory is to go to Calibre's Preferences page... click on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre configuration directory' button. Paste your keyfiles in there. Just make sure that they have different names and are saved with the '.der' extension (like the ineptkey script produces). This directory isn't touched when upgrading Calibre, so it's quite safe to leave them there.

Since there is no Linux version of Adobe Digital Editions, Linux users will have to obtain a keyfile through other methods and put the file in Calibre's configuration directory.

All keyfiles with a '.der' extension found in Calibre's configuration directory will be used to attempt to decrypt a book.


** NOTE ** There is no plugin customization data for the Inept Epub DeDRM plugin.


Troubleshooting
---------------

If you find that it's not working for you (imported ebooks still have DRM), you can save a lot of time and trouble by first deleting the DRMed ebook from calibre and then trying to add the ebook to calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might as well get used to it. ;)

On Macintosh only you must first run calibre, open Preferences, open Miscellaneous, and click on the “Install command line tools” button. (On Windows and Linux the command line tools are installed automatically.)

On Windows, open a terminal/command window. (Start/Run… and then type ‘cmd’ (without the ‘s) as the program to run).
On Macintosh, open the Terminal application (in your Utilities folder).
On Linux open a command window. Hopefully all Linux users know how to do this, as I do not.

You should now have a text-based command-line window open. Also have open the folder containing the ebook to be imported. Make sure that book isn’t already in calibre, and that calibre isn’t running.

Now type in "calibredb add " (without the " but don’t miss that final space) and now drag the book to be imported onto the window. The full path to the book should be inserted into the command line. Now press the return/enter key. The import routines will run and produce some logging information.

Now copy the output from the terminal window.
On Windows, you must use the window menu (little icon at left of window bar) to select all the text and then to copy it.
On Macintosh and Linux, just use the normal text select and copy commands.

Paste the information into a comment at my blog, http://apprenticealf.wordpress.com/ describing your problem.


Linux and Adobe Digital Editions ePubs
--------------------------------------

Here are the instructions for using the tools with ePub books and Adobe Digital Editions on Linux under Wine. (Thank you mclien and Fadel!)


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

4. all programms need to be installed as normal user. The .exe files are installed using ‘wine <filename>’ but .msi files must be installed using ‘wine start <filename>’
we need:
a) Adobe Digital Edition 1.7.2(from: http://kb2.adobe.com/cps/403/kb403051.html)
(there is a “can’t install ADE” site, where the setup.exe hides)

b) ActivePython-2.7.2.5-win32-x86.msi (from: http://www.activestate.com/activepython/downloads)

c) Win32OpenSSL_Light-0_9_8r.exe (from: http://www.slproweb.com/)

d) pycrypto-2.3.win32-py2.7.msi (from: http://www.voidspace.org.uk/python/modules.shtml)

5. now get and unpack the very latest tools_vX.X (from Apprentice Alf) in the users drive_c of wine
(~/.wine/drive_c/)

6. start ADE with:
‘wine digitaleditions.exe’ or from the start menue wine-adobe-digital..

7. register this instance of ADE with your adobeID and close it
 change to the tools_vX.X dir:
cd ~/.wine/drive_c/tools_vX.X/Other_Tools/

8. create the adeptkey.der with:
‘wine python ineptkey.py’ (only need once!)
(key will be here: ~/.wine/drive_c/tools_vX.X/Other_Tools/adeptkey.der)

9. Use ADE running under Wine to dowload all of your purchased ePub ebooks

10. install the ineptepub and ineptpdf plugins from the tools as discribed in the readmes.

11. copy the adeptkey.der into the config dir of calibre (~/.config/calibre in debian). Your ADE books imported to calibre will automatically be freed from DRM.

