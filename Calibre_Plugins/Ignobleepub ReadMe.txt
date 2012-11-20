Ignoble Epub DeDRM - ignobleepub_v02.4_plugin.zip

All credit given to I♥Cabbages for the original standalone scripts.
I had the much easier job of converting them to a calibre plugin.

This plugin is meant to decrypt Barnes & Noble Epubs that are protected with Adobe's Adept encryption. It is meant to function without having to install any dependencies... other than having calibre installed, of course. It will still work if you have Python and PyCrypto already installed, but they aren't necessary.


Installation:

Go to calibre's Preferences page.  Do **NOT** select "Get plugins to enhance calibre" as this is reserved for "official" calibre plugins, instead select "Change calibre behavior". Under "Advanced" click on the Plugins button. Use the "Load plugin from file" button to select the plugin's zip file  (ignobleepub_v02.4_plugin.zip) and click the 'Add' button. Click 'Yes' in the the "Are you sure?" dialog. Click OK in the "Success" dialog.


Configuration:

Upon first installing the plugin (or upgrading from a version earlier than 0.2.0), the plugin will be unconfigured. Until you create at least one B&N key—or migrate your existing key(s)/data from an earlier version of the plugin—the plugin will not function. When unconfigured (no saved keys)... an error message will occur whenever ePubs are imported to calibre. To eliminate the error message, open the plugin's customization dialog and create/import/migrate a key (or disable/uninstall the plugin). You can get to the plugin's customization dialog by opening calibre's Preferences dialog, and clicking Plugins (under the Advanced section). Once in the Plugin Preferences, expand the "File type plugins" section and look for the "Ignoble Epub DeDRM" plugin. Highlight that plugin and click the "Customize plugin" button.

Upgrading from old keys

If you are upgrading from an earlier version of this plugin and have provided your name(s) and credit card number(s) as part of the old plugin's customization string, you will be prompted to migrate this data to the plugin's new, more secure, key storage method when you open the customization dialog for the first time. If you choose NOT to migrate that data, you will be prompted to save that data as a text file in a location of your choosing. Either way, this plugin will no longer be storing names and credit card numbers in plain sight (or anywhere for that matter) on your computer or in calibre. If you don't choose to migrate OR save the data, that data will be lost. You have been warned!!

Upon configuring for the first time, you may also be asked if you wish to import your existing *.b64 keyfiles (if you use them) to the plugin's new key storage method. The new plugin no longer looks for keyfiles in calibre's configuration directory, so it's highly recommended that you import any existing keyfiles when prompted ... but you always have the ability to import existing keyfiles anytime you might need/want to.

If you have upgraded from an earlier version of the plugin, the above instructions may be all you need to do to get the new plugin up and running. Continue reading for new-key generation and existing-key management instructions.

Creating New Keys:

On the right-hand side of the plugin's customization dialog, you will see a button with an icon that looks like a green plus sign (+). Clicking this button will open a new dialog for entering the necessary data to generate a new key.

* Unique Key Name: this is a unique name you choose to help you identify the key after it's created. This name will show in the list of configured keys. Choose something that will help you remember the data (name, cc#) it was created with.
* Your Name: Your name as set in your Barnes & Noble account, My Account page, directly under PERSONAL INFORMATION. It is usually just your first name and last name separated by a space. This name will not be stored anywhere on your computer or in calibre. It will only be used in the creation of the one-way hash/key that's stored in the preferences.
* Credit Card number: this is the credit card number that was set as default with Barnes & Noble at the time of download. Nothing fancy here; no dashes or spaces ... just the 16 (15?) digits. Again... this number will not be stored anywhere on your computer or in calibre. It will only be used in the creation of the one-way hash/key that's stored in the preferences.
Click the 'OK" button to create and store the generated key. Or Cancel if you didn't want to create a key.

Deleting Keys:

On the right-hand side of the plugin's customization dialog, you will see a button with an icon that looks like a red "X". Clicking this button will delete the highlighted key in the list. You will be prompted once to be sure that's what you truly mean to do. Once gone, it's permanently gone.

Exporting Keys:

On the right-hand side of the plugin's customization dialog, you will see a button with an icon that looks like a computer's hard-drive. Use this button to export the highlighted key to a file (*.b64). Used for backup purposes or to migrate key data to other computers/calibre installations. The dialog will prompt you for a place to save the file.

Importing Existing Keyfiles:

At the bottom-left of the plugin's customization dialog, you will see a button labeled "Import Existing Keyfiles". Use this button to import existing *.b64 keyfiles. Used for migrating keyfiles from older versions of the plugin (or keys generated with the original I <3 Cabbages script), or moving keyfiles from computer to computer, or restoring a backup. Some very basic validation is done to try to avoid overwriting already configured keys with incoming, imported keyfiles with the same base file name, but I'm sure that could be broken if someone tried hard. Just take care when importing.

Once done creating/importing/exporting/deleting decryption keys; click "OK" to exit the customization dialogue (the cancel button will actually work the same way here ... at this point all data/changes are committed already, so take your pick).

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
