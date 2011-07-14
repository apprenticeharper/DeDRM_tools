eReader PDB2PML - eReaderPDB2PML_vXX_plugin.zip

All credit given to The Dark Reverser for the original standalone script. I had the much easier job of converting it to a Calibre plugin.

This plugin is meant to convert secure Ereader files (PDB) to unsecured PMLZ files. Calibre can then convert it to whatever format you desire. It is meant to function without having to install any  dependencies... other than having Calibre installed, of course. I've included the psyco libraries (compiled for each platform) for speed. If your system can use them, great! Otherwise, they won't be used and things will just work slower.

Installation:
Go to Calibre's Preferences page. Do **NOT** select "Get Plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file  (eReaderPDB2PML_vXX_plugin.zip) and click the 'Add' button. You're done.

Please note:  Calibre does not provide any immediate feedback to indicate that adding the plugin was a success. You can always click on the File-Type plugins to see if the plugin was added.

Configuration:
Highlight the plugin (eReader PDB 2 PML under the "File type plugins" category) and click the "Customize Plugin" button on Calibre's Preferences->Plugins page. Enter your name and last 8 digits of the credit card number separated by a comma: Your Name,12341234

If you've purchased books with more than one credit card, separate the info with a colon: Your Name,12341234:Other Name,23452345 (NOTE: Do NOT put quotes around your name like you do with the original script!!)

Troubleshooting:
If you find that it's not working for you (imported pdb's are not converted to pmlz format), you can save a lot of time and trouble by trying to add the pdb to Calibre with the command line tools. This will print out a lot of helpful debugging info that can be copied into any online help requests. I'm going to ask you to do it first, anyway, so you might
as well get used to it. ;)

Open a command prompt (terminal) and change to the directory where the ebook you're trying to import resides. Then type the command "calibredb add your_ebook.pdb". Don't type the quotes and obviously change the 'your_ebook.pdb' to whatever the filename of your book is. Copy the resulting output and paste it into any online help request you make.

** Note: the Mac version of Calibre doesn't install the command line tools by default. If you go to the 'Preferences' page and click on the miscellaneous button, you'll see the option to install the command line tools.
