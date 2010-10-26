Plugin for K4PC, K4Mac and Mobi Books

Will work on Linux (standard DRM Mobi books only), Mac OS X (standard DRM Mobi books and "Kindle for Mac" books, and Windows (standard DRM Mobi books and "Kindle for PC" books.

This plugin supersedes MobiDeDRM, K4DeDRM, and K4PCDeDRM plugins.  If you install this plugin, those plugins can be safely removed.

This plugin is meant to convert "Kindle for PC", "Kindle for Mac" and "Mobi" ebooks with DRM to unlocked Mobi files. Calibre can then convert them to whatever format you desire. It is meant to function without having to install any  dependencies except for Calibre being on your same machine and in the same account as your "Kindle for PC" or "Kindle for Mac" application if you are going to remove the DRM from those types of books.

Installation:
Go to Calibre's Preferences page... click on the Plugins button. Use the file dialog button to select the plugin's zip file  (k4mobidedrm_vXX_plugin.zip) and click the 'Add' button. You're done.

Configuration:
Highlight the plugin (K4MobiDeDRM under the "File type plugins" category) and click the "Customize Plugin" button on Calibre's Preferences->Plugins page. Enter a comma separated list of your 10 digit PIDs. This is not needed if you only want to decode "Kindle for PC" or "Kindle for Mac" books. 


Troubleshooting:
If you find that it's not working for you (imported azw's are not converted to mobi format), you can save a lot of time and trouble by trying to add the azw file to Calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might
as well get used to it. ;)

Open a command prompt (terminal) and change to the directory where the ebook you're trying to import resides. Then type the command "calibredb add your_ebook.azw". Don't type the quotes and obviously change the 'your_ebook.azw' to whatever the filename of your book is. Copy the resulting output and paste it into any online help request you make.

** Note: the Mac version of Calibre doesn't install the command line tools by default. If you go to the 'Preferences' page and click on the miscellaneous button, you'll see the option to install the command line tools.

