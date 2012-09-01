Inept Epub DeDRM - ineptepub_vXX_plugin.zip
Requires Calibre version 0.6.44 or higher.

All credit given to I <3 Cabbages for the original standalone scripts.
I had the much easier job of converting them to a Calibre plugin.

This plugin is meant to decrypt Adobe Digital Edition Epubs that are protected with Adobe's Adept encryption. It is meant to function without having to install any dependencies... other than having Calibre installed, of course. It will still work if you have Python and PyCrypto already installed, but they aren't necessary.

Installation:

Go to Calibre's Preferences page. Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Cahnge calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file (ineptepub_vXX_plugin.zip) and click the 'Add' button. you're done.

Please note:  Calibre does not provide any immediate feedback to indicate that adding the plugin was a success. You can always click on the File-Type plugins to see if the plugin was added.


Configuration:

When first run, the plugin will attempt to find your Adobe Digital Editions installation (on Windows and Mac OS's). If successful, it will create an 'adeptkey.der' file and save it in Calibre's configuration directory. It will use that file on subsequent runs. If there are already '*.der' files in the directory, the plugin won't attempt to
find the Adobe Digital Editions installation installation.

So if you have Adobe Digital Editions installation installed on the same machine as Calibre... you are ready to go. If not... keep reading.

If you already have keyfiles generated with I <3 Cabbages' ineptkey.pyw script, you can put those keyfiles in Calibre's configuration directory. The easiest way to find the correct directory is to go to Calibre's Preferences page... click on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre configuration directory' button. Paste your keyfiles in there. Just make sure that
they have different names and are saved with the '.der' extension (like the ineptkey script produces). This directory isn't touched when upgrading Calibre, so it's quite safe to leave them there.

Since there is no Linux version of Adobe Digital Editions, Linux users will have to obtain a keyfile through other methods and put the file in Calibre's configuration directory.

All keyfiles with a '.der' extension found in Calibre's configuration directory will be used to attempt to decrypt a book.

** NOTE ** There is no plugin customization data for the Inept Epub DeDRM plugin.

Troubleshooting:

If you find that it's not working for you (imported epubs still have DRM), you can save a lot of time and trouble by trying to add the epub to Calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might
as well get used to it. ;)

Open a command prompt (terminal) and change to the directory where the ebook you're trying to import resides. Then type the command "calibredb add your_ebook.epub". Don't type the quotes and obviously change the 'your_ebook.epub' to whatever the filename of your book is. Copy the resulting output and paste it into any online help request you make.

** Note: the Mac version of Calibre doesn't install the command line tools by default. If you go to the 'Preferences' page and click on the miscellaneous button, you'll see the option to install the command line tools.
