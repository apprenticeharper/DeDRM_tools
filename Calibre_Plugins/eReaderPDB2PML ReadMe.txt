eReader PDB2PML - eReaderPDB2PML_v07_plugin.zip

All credit given to The Dark Reverser for the original standalone script. I had the much easier job of converting it to a Calibre plugin.

This plugin is meant to convert secure Ereader files (PDB) to unsecured PMLZ files. Calibre can then convert it to whatever format you desire. It is meant to function without having to install any  dependencies... other than having Calibre installed, of course. I've included the psyco libraries (compiled for each platform) for speed. If your system can use them, great! Otherwise, they won't be used and things will just work slower.


Installation:

Go to Calibre's Preferences page. Do **NOT** select "Get Plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file  (eReaderPDB2PML_v07_plugin.zip) and click the 'Add' button. You're done.


Please note:  Calibre does not provide any immediate feedback to indicate that adding the plugin was a success. You can always click on the File-Type plugins to see if the plugin was added.


Configuration:

Highlight the plugin (eReader PDB 2 PML under the "File type plugins" category) and click the "Customize Plugin" button on Calibre's Preferences->Plugins page. Enter your name and last 8 digits of the credit card number separated by a comma: Your Name,12341234

If you've purchased books with more than one credit card, separate the info with a colon: Your Name,12341234:Other Name,23452345


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