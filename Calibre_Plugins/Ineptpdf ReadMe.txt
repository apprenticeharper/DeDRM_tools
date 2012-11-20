Inept PDF Plugin - ineptpdf_v01.8_plugin.zip

All credit given to I♥Cabbages for the original standalone scripts.
I had the much easier job of converting them to a Calibre plugin.

This plugin is meant to decrypt Adobe Digital Edition PDFs that are protected with Adobe's Adept encryption. It is meant to function without having to install any dependencies... other than having Calibre installed, of course. It will still work if you have Python, PyCrypto and/or OpenSSL already installed, but they aren't necessary.


Installation:

Go to calibre's Preferences page.  Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (ineptpdf_v01.8_plugin.zip) and click the 'Add' button. Click 'Yes' in the the "Are you sure?" dialog. Click OK in the "Success" dialog.


Configuration:

When first run, the plugin will attempt to find your Adobe Digital Editions installation (on Windows and Mac OS). If successful, it will create 'calibre-adeptkey[number].der' file(s) and save them in Calibre's configuration directory. It will use those files and any other '*.der' files in any decryption attempts. If there is already at least one 'calibre-adept*.der' file in the directory, the plugin won't attempt to find the Adobe Digital Editions installation keys again.

So if you have Adobe Digital Editions installation installed on the same machine as Calibre... you are ready to go. If not... keep reading.

If you already have keyfiles generated with I♥Cabbages' ineptkey.pyw script, you can put those keyfiles in Calibre's configuration directory. The easiest way to find the correct directory is to go to Calibre's Preferences page... click on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre configuration directory' button. Paste your keyfiles in there. Just make sure that
they have different names and are saved with the '.der' extension (like the ineptkey script produces). This directory isn't touched when upgrading Calibre, so it's quite safe to leave them there.

Since there is no Linux version of Adobe Digital Editions, Linux users will have to obtain a keyfile through other methods and put the file in Calibre's configuration directory.

All keyfiles with a '.der' extension found in Calibre's configuration directory will be used to attempt to decrypt a book.

** NOTE ** There is no plugin customization data for the Inept PDF plugin.


Troubleshooting:

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

Paste the information into a comment at my blog, describing your problem.
