K4MobiDeDRM_v04.5_plugin.zip

Credit given to The Dark Reverser for the original standalone script. Credit also to the many people who have updated and expanded that script since then.

Plugin for K4PC, K4Mac, eInk Kindles and Mobipocket.

This plugin supersedes MobiDeDRM, K4DeDRM, and K4PCDeDRM and K4X plugins.  If you install this plugin, those plugins can be safely removed.

This plugin is meant to remove the DRM from .prc, .mobi, .azw, .azw1, .azw3, .azw4 and .tpz ebooks.   Calibre can then convert them to whatever format you desire. It is meant to function without having to install any  dependencies except for Calibre being on your same machine and in the same account as your "Kindle for PC" or "Kindle for Mac" application if you are going to remove the DRM from those types of books.


Installation:

Go to Calibre's Preferences page.  Do **NOT** select "Get Plugins to enhance calibre" as this is reserved for official calibre plugins", instead select "Change calibre behavior". Under "Advanced" click on the on the Plugins button. Click on the "Load plugin from file" button at the bottom of the screen.  Use the file dialog button to select the plugin's zip file  (K4MobiDeDRM_vXX_plugin.zip) and click the "Add" (or it may say "Open" button.  Then click on the "Yes" button in the warning dialog that appears.  A Confirmation dialog appears that says the plugin has been installed.


Configuration:

Highlight the plugin (K4MobiDeDRM under the "File type plugins" category) and click the "Customize Plugin" button on Calibre's Preferences->Plugins page. If you have an eInk Kindle enter the 16 digit serial number (these typically begin "B0..."). If you have more than one eInk Kindle, you can enter multiple serial numbers separated by commas (no spaces). If you have Mobipocket books, enter your 10 digit PID.  If you have more than one PID, separate them with commax (no spaces).

This configuration step is not needed if you only want to decode "Kindle for PC" or "Kindle for Mac" books. 


Linux Systems Only:

If you install Kindle for PC in Wine, the plugin should be able to decode files from that Kindle for PC installation under Wine. You might need to enter a Wine Prefix if it's not already set in your Environment variables.


Troubleshooting:

If you find that it's not working for you, you can save a lot of time and trouble by trying to add the DRMed ebook to Calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might as well get used to it. ;)

Open a command prompt (terminal) and change to the directory where the ebook you're trying to import resides. Then type the command "calibredb add your_ebook_file". Don't type the quotes and obviously change the 'your_ebook_file' to whatever the filename of your book is (including any file name extension like .azw). Copy the resulting output and paste it into any online help request you make.

** Note: the Mac version of Calibre doesn't install the command line tools by default. If you go to the 'Preferences' page and click on the miscellaneous button, you'll see the option to install the command line tools.


