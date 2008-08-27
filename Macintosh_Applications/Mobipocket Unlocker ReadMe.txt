Mobipocket Unlocker AppleScript Version 3

How to get Drag&Drop decryption of DRM-encumbered Mobipocket eBook files.

You'll need the MobiDeDRM.py python script, as well as an installed version 2.4 or later of python. If you have Mac OS X Leopard (10.5) you already have a suitable version of python installed as part of Leopard.

Control-click the script and select "Show Package Contents" from the contextual menu. Copy the python script, which must be called "MobiDeDRM.py" into the Resources folder inside the Contents folder. (NB not into the Scripts folder - that's where the Applescript part is stored.)

Close the package, and you now have a drag&drop Mobipocket decrypter.

You can use the AppleScript ScriptEditor application to put your Mobipocket code into the script to save you having to enter it in the dialog all the time.

If you run the script directly, you'll be asked to select a folder of Mobipocket files, and then your PID. The script will attempt to unlock all Mobipocket files in the folder selected, including files in subfolders.

If you drag and drop files and/or folders onto the script, you will be asked for your PID and then the script will attampt to unlock all the Mobipocket files dragged directly, and all Mobipocket files in the dragged  folders (& subfolders).

If the Python script returns an error, the AppleScript will report it, otherwise it works without any visible feedback.

The MobiDeDRM.py scripts out there don't work perfectly. If you get the 0.02 version of the script, you can fix up a few problems by apply these changes:

After line 63:
[tab][tab]bitpos, result = 0,0

add in the following two lines:
[tab][tab]if size <= 0:
[tab][tab][tab]return result

After line 135:
[tab][tab]records, = struct.unpack('>H', sect[0x8:0x8+2])

add in the following three lines
[tab][tab]mobi_length, = struct.unpack('>L',sect[0x14:0x18])
[tab][tab]extra_data_flags = 0
[tab][tab]if mobi_length >= 0xE4:

(note that tricky comma after the first instance of mobi_length)

Add a tab to line 136:
[tab][tab]extra_data_flags, = struct.unpack('>L', sect[0xF0:0xF4])

to make it
[tab][tab][tab]extra_data_flags, = struct.unpack('>L', sect[0xF0:0xF4])

and change line 165:
print "MobiDeDrm v0.02. Copyright (c) 2008 The Dark Reverser"

to
print "MobiDeDrm v0.04. Copyright (c) 2008 The Dark Reverser"

just so that you don't get confused at the command line.


Oh -- [tab] just means a single tab character - not the five literal characters [tab].


