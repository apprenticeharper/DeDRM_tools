DeDRM_plugin.zip
================

This plugin will remove the DRM from:

 - Kindle ebooks (files from Kindle for Mac/PC and eInk Kindles).
 - Adobe Digital Editions (v2.0.1***) ePubs (including Kobo and Google ePubs downloaded to ADE)
 - Adobe Digital Editions (v2.0.1) PDFs

For limitations and work-arounds, see the FAQ at https://github.com/apprenticeharper/DeDRM_tools/blob/master/FAQs.md


Installation
------------
Open calibre's Preferences dialog.  Click on the "Plugins" button.  Next, click on the button, "Load plugin from file".  Navigate to the unzipped DeDRM_tools folder, find the file "DeDRM_plugin.zip".  Click to select the file and select "Open".  Click "Yes" in the "Are you sure?" dialog box. Click the "OK" button in the "Success" dialog box.


Customization
-------------
For Kindle ebooks from an E-Ink based Kindle (e.g. Voyage), or books downloaded from the Amazon web site 'for transfer via USB' to an E-Ink base Kindle, you must enter the Kindle's serial number in the customisation dialog.

When you have finished entering your configuration information, you must click the OK button to save it. If you click the Cancel button, all your changes in all the configuration dialogs will be lost.


Troubleshooting
---------------
If you find that the DeDRM plugin is not working for you (imported ebooks still have DRM - that is, they won't convert or open in the calibre ebook viewer), you should make a log of the import process by deleting the DRMed ebook from calibre and then adding the ebook to calibre when it's running in debug mode. This will generate a lot of helpful debugging info that can be copied into any online help requests. Here's how to do it:

 - Remove the DRMed book from calibre.
 - Click the Preferences drop-down menu and choose 'Restart in debug mode'.
 - Once calibre has re-started, import the problem ebook.
 - Now close calibre.

A log will appear that you can copy and paste into a comment at Apprentice Alf's blog, http://apprenticealf.wordpress.com/ or an issue at Apprentice Harper's repository, https://github.com/apprenticeharper/DeDRM_tools/issues . You should also give details of your computer, and how you obtained the ebook file.
