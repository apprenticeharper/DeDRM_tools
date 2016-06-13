obok_plugin.zip
================

This plugin will remove the DRM from Kobo ebooks download on Mac or Windows using the Kobo desktop application, or from Kobo ebooks on an attached E-Ink Kobo reader (but not a Kobo Arc or Kobo Vox). If both are available, ebooks will be read from the attached E-Ink Kobo reader. To import from the desktop application, unplug the Kobo reader.


Installation
------------
Open calibre's Preferences dialog.  Click on the "Plugins" button.  Next, click on the button, "Load plugin from file".  Navigate to the unzipped DeDRM_tools folder and, in the folder "obok_calibre_plugin", find the file "obok_plugin.zip".  Click to select the file and select "Open".  Click "Yes" in the "Are you sure?" dialog box. Click the "OK" button in the "Success" dialog box.


Customization
-------------
No customization is required, except choosing which menus will show the plugin. Altough the ability to enter a device serial number is given, this should not need to be filled in, as the serial number should be picked up automatically from the attached Kobo reader.


Using the plugin
----------------

Select the plugin's menu or icon from whichever part of the calibre interface you have chosen to have it. Follow the instructions in the dialog that appears.


Troubleshooting
---------------
If you find that it's not working for you (imported ebooks still have DRM - that is, they won't convert or open in the calibre ebook viewer), you should make a log of import process by deleting the DRMed ebook from calibre and then adding the ebook to calibre when it's running in debug mode. This will generate a lot of helpful debugging info that can be copied into any online help requests. Here's how to do it:

On Windows, open a terminal/command window. (Start/Run… and then type 'cmd.exe' (without the 's) as the program to run).
On Macintosh, open the Terminal application (in your Utilities folder).
On Linux open a command window. Hopefully all Linux users know how to do this.

You should now have a text-based command-line window open.

Type in "calibre-debug -g" (without the "s but with the space before the -g) and press the return/enter key. Calibre will launch and run as normal, but with debugging information output to the terminal window.

Import the DRMed eBook into calibre in any of the the normal ways. (I usually drag&drop onto the calibre window.)

Debug information will be written to the terminal window.

Copy the output from the terminal window.
On Windows, you must use the window menu (little icon at left of window bar) to select all the text and then to copy it.
On Macintosh and Linux, just use the normal text select and copy commands.

Paste the information into a comment at my blog, http://apprenticealf.wordpress.com/ describing your problem.


Credits
-------
The original obok script was by Physisticated
The plugin conversion was done anonymously.
The Kobo reader support was added by norbusan

Additional improvements to the script and the plugin adaption by numerous anonymous people.

