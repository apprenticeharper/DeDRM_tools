K4MobiDeDRM_v04.7_plugin.zip

Credit given to The Dark Reverser for the original standalone script. Credit also to the many people who have updated and expanded that script since then.

Plugin for K4PC, K4Mac, eInk Kindles and Mobipocket.

This plugin supersedes MobiDeDRM, K4DeDRM, and K4PCDeDRM and K4X plugins. If you install this plugin, those plugins should be removed.

This plugin is meant to remove the DRM from .prc, .mobi, .azw, .azw1, .azw3, .azw4 and .tpz ebooks. Calibre can then convert them to whatever format you desire. It is meant to function without having to install any dependencies except for Calibre being on your same machine and in the same account as your "Kindle for PC" or "Kindle for Mac" application if you are going to remove the DRM from those types of books.


Installation:

Go to calibre's Preferences page.  Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (K4MobiDeDRM_v04.7_plugin.zip) and click the 'Add' button. Click 'Yes' in the the "Are you sure?" dialog. Click OK in the "Success" dialog.

Make sure that you delete any old versions of the plugin. They might interfere with the operation of the new one.


Configuration:

Highlight the plugin (K4MobiDeDRM under the "File type plugins" category) and click the "Customize Plugin" button on Calibre's Preferences->Plugins page.

If you have an eInk Kindle enter the 16 character serial number (these all begin a "B") in the serial numbers field. The easiest way to make sure that you have the serial number right is to copy it from your Amazon account pages (the "Manage Your Devices" page). If you have more than one eInk Kindle, you can enter multiple serial numbers separated by commas.

If you have Mobipocket books, enter your 8 or 10 digit PID in the Mobipocket PIDs field. If you have more than one PID, separate them with commas.

These configuration steps are not needed if you only want to decode "Kindle for PC" or "Kindle for Mac" books.


Linux Systems Only:

If you install Kindle for PC in Wine, the plugin should be able to decode files from that Kindle for PC installation under Wine. You might need to enter a Wine Prefix if it's not already set in your Environment variables.


Troubleshooting:

If you find that it's not working for you (imported ebooks still have DRM), you can save a lot of time and trouble by first deleting the DRMed ebook from calibre and then trying to add the ebook to calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might as well get used to it. ;)

On Macintosh only you must first run calibre, open Preferences, open Miscellaneous, and click on the “Install command line tools” button. (On Windows and Linux the command line tools are installed automatically.)

On Windows, open a terminal/command window. (Start/Run… and then type 'cmd' (without the 's) as the program to run).
On Macintosh, open the Terminal application (in your Utilities folder).
On Linux open a command window. Hopefully all Linux users know how to do this, as I do not.

You should now have a text-based command-line window open. Also have open the folder containing the ebook to be imported. Make sure that book isn’t already in calibre, and that calibre isn’t running.

Now type in "calibredb add " (without the " but don’t miss that final space) and now drag the book to be imported onto the window. The full path to the book should be inserted into the command line. Now press the return/enter key. The import routines will run and produce some logging information.

Now copy the output from the terminal window.
On Windows, you must use the window menu (little icon at left of window bar) to select all the text and then to copy it.
On Macintosh and Linux, just use the normal text select and copy commands.

Paste the information into a comment at my blog, describing your problem.


