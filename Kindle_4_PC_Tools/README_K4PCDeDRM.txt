Readme.txt

From Apprentice Alf's Blog:

When Amazon released Kindle for PC, there was a lot of interest in finding the PID used by an installed copy. Unfortunately, it turned out that Amazon had taken the opportunity to increase the complexity of the DRM applied to ebooks downloaded for use with Kindle for PC. In short, every book has its own PID.

The current best method is a script called K4PCDeDRM.py, which takes code from several previous tools and puts them together, giving a one-script solution to removing the DRM that is not dependent on the exact version of the Kindle for PC software.

To use this script requires Python Version 2.X 32 bit version.  On Windows, we recommend downloading ActiveState's ActivePython for Windows (Version 2.X NOT 3.X (32bit).

We strongly recommend that at the moment people with Kindle for Windows should use K4PCDeDRM.pyw instead of any of the other methods (skindle, unswindle).

K4PCDeDRM is available in the large archive mentioned in the first post.

To run it simply completely extract the tools archive and open the Kindle_4_PC_Tools.  Then double-click on K4PCDeDRM.pyw to run the gui version.

Please note, the tools archive must be on the same machine in the same account as the Kindle for PC application for things to work.

FYI:
Books downloaded to Kindle for PC are stored in a folder called “My Kindle Content” in the current user’s home folder.

IMPORTANT: There are two kinds of Kindle ebooks. Mobipocket and Topaz. For Topaz books it’s really necessary to use the Topaz specific tools mentioned in this post which not only remove the DRM but also convert the Topaz file into a format that can be converted into other formats.

