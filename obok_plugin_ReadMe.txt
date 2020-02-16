obok_plugin.zip
================

This plugin will remove the DRM from Kobo ebooks download on Mac or Windows using the Kobo desktop application, or from Kobo ebooks on an attached E-Ink Kobo reader (but not a Kobo Arc or Kobo Vox). If both are available, ebooks will be read from the attached E-Ink Kobo reader. To import from the desktop application, unplug the Kobo reader.


Installation
------------
Open calibre's Preferences dialog.  Click on the "Plugins" button.  Next, click on the button, "Load plugin from file".  Navigate to the unzipped DeDRM_tools folder, find the file "obok_plugin.zip".  Click to select the file and select "Open".  Click "Yes" in the "Are you sure?" dialog box. Click the "OK" button in the "Success" dialog box.


Customization
-------------
No customization is required, except choosing which menus will show the plugin. Although the ability to enter a device serial number is given, this should not need to be filled in, as the serial number should be picked up automatically from the attached Kobo reader.


Using the plugin
----------------

Select the plugin's menu or icon from whichever part of the calibre interface you have chosen to have it. Follow the instructions in the dialog that appears.


Troubleshooting
---------------
If you find that the DeDRM plugin is not working for you (imported ebooks still have DRM - that is, they won't convert or open in the calibre ebook viewer), you should make a log of the import process by deleting the DRMed ebook from calibre and then adding the ebook to calibre when it's running in debug mode. This will generate a lot of helpful debugging info that can be copied into any online help requests. Here's how to do it:

 - Remove the DRMed book from calibre.
 - Click the Preferences drop-down menu and choose 'Restart in debug mode'.
 - Once calibre has re-started, import the problem ebook.
 - Now close calibre.

A log will appear that you can copy and paste into a comment at Apprentice Alf's blog, http://apprenticealf.wordpress.com/ or an issue at Apprentice Harper's repository, https://github.com/apprenticeharper/DeDRM_tools/issues . You should also give details of your computer, and how you obtained the ebook file.

