Ignoble Epub DeDRM - ignobleepub_vXX_plugin.zip
Requires Calibre version 0.6.44 or higher.

All credit given to I <3 Cabbages for the original standalone scripts.
I had the much easier job of converting them to a Calibre plugin.

This plugin is meant to decrypt Barnes & Noble Epubs that are protected
with Adobe's Adept encryption. It is meant to function without having to install any dependencies... other than having Calibre installed, of course. It will still work if you have Python and PyCrypto already installed, but they aren't necessary.

Installation:

Go to Calibre's Preferences page.  Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file  (ignobleepub_vXX_plugin.zip) and
click the 'Add' button. you're done.

Please note:  Calibre does not provide any immediate feedback to indicate that adding the plugin was a success. You can always click on the File-Type plugins to see if the plugin was added.

Configuration:

1) The easiest way to configure the plugin is to enter your name (Barnes & Noble account name) and credit card number (the one used to purchase the books) into the plugin's customization window. It's the same info you would enter into the ignoblekeygen script. Highlight the plugin (Ignoble Epub DeDRM) and click the "Customize Plugin" button on
Calibre's Preferences->Plugins page. Enter the name and credit card number separated by a comma: Your Name,1234123412341234

If you've purchased books with more than one credit card, separate that other info with a colon: Your Name,1234123412341234:Other Name,2345234523452345

** NOTE ** The above method is your only option if you don't have/can't run the original I <3 Cabbages scripts on your particular machine.

** NOTE ** Your credit card number will be on display in Calibre's Plugin configuration page when using the above method. If other people have access to your computer, you may want to use the second configuration method below.

2) If you already have keyfiles generated with I <3 Cabbages' ignoblekeygen.pyw script, you can put those keyfiles into Calibre's configuration directory. The easiest way to find the correct directory is to go to Calibre's Preferences page... click on the 'Miscellaneous' button (looks like a gear),  and then click the 'Open Calibre
configuration directory' button. Paste your keyfiles in there. Just make sure that they have different names and are saved with the '.b64' extension (like the ignoblekeygen script produces). This directory isn't touched when upgrading Calibre, so it's quite safe to leave them there.

All keyfiles from method 2 and all data entered from method 1 will be used to attempt to decrypt a book. You can use method 1 or method 2, or a combination of both.

Troubleshooting:

If you find that it's not working for you (imported epubs still have DRM), you can save a lot of time and trouble by trying to add the epub to Calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might
as well get used to it. ;)

Open a command prompt (terminal) and change to the directory where the ebook you're trying to import resides. Then type the command "calibredb add your_ebook.epub". Don't type the quotes and obviously change the 'your_ebook.epub' to whatever the filename of your book is. Copy the resulting output and paste it into any online help request you make.

** Note: the Mac version of Calibre doesn't install the command line tools by default. If you go to the 'Preferences' page and click on the miscellaneous button, you'll see the option to install the command line tools.
