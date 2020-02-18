# DeDRM_tools
DeDRM tools for ebooks

This is a repository of all the scripts and other tools for removing DRM from ebooks that I could find, committed in date order as best as I could manage. (Except for the Requiem tools for Apple's iBooks, and Convert LIT for Microsoft's .lit ebooks.)

Mostly it tracks the tools releases by Apprentice Alf, athough it also includes the individual tools and their histories from before Alf had a blog.

Users should download the latest zip archive.
Developers might be interested in forking the repository, as it contains unzipped versions of those tools that are zipped, and text versions of the AppleScripts, to make the changes over time easier to follow.

For the latest Amazon KFX format, users of the calibre plugin should also install the KFX Input plugin from the standard calibre plugin menu. It's also available from the MobileRead thread here: https://www.mobileread.com/forums/showthread.php?t=291290

I welcome contributions from others to improve these tools, from expanding the range of books handled, improving key retrieval,  to just general bug fixes, speed improvements and UI enhancements.

I urge people to read the FAQs. But to cover the most common: Use ADE 2.0.1 whenever possible to be sure not to get the new DRM scheme that these tools can't handle. Use Kindle for Mac/PC 1.24 or earlier whenever possible; these tools don't currently work with Kindle for PC 1.25 or later, and there are issues with Kindle for Mac 1.25 and later [(more info here)](https://www.mobileread.com/forums/showpost.php?p=3819708&postcount=508). Do remember to unzip the downloaded archive to get the plugin. You can't load the whole archive into calibre.

For macOS Catalina users: You will have no choice but to use ADE 4.x and Kindle for Mac 1.25 or later since Catalina requires 64-bit apps and earlier versions of ADE and Kindle for Mac are 32-bit. ADE 4.x *will* work with these tools provided the book vendor is not using hardened DRM. To get Kindle for Mac 1.25+ working, read [this post](https://www.mobileread.com/forums/showpost.php?p=3819708&postcount=508) before you update to Catalina.

My special thanks to all those developers who have done the hard work of reverse engineering to provide the initial tools.

Apprentice Harper.
