# DeDRM_tools
DeDRM tools for ebooks

This is a fork of Apprentice Harper's version of the DeDRM tools. Apprentice Harper said that the original version of the plugin [is no longer maintained](https://github.com/apprenticeharper/DeDRM_tools#no-longer-maintained), so I've taken over, merged a bunch of open PRs, and added a ton more features and bugfixes. 

The latest stable (released) version is v10.0.3 which [can be downloaded here](https://github.com/noDRM/DeDRM_tools/releases/tag/v10.0.3). The latest beta is v10.0.9, as a release candidate for v10.1.0. It [can be downloaded here](https://github.com/noDRM/DeDRM_tools/releases/tag/v10.0.9). 

The latest alpha version is available [at this link](https://github.com/noDRM/DeDRM_tools_autorelease/releases). This version is completely untested and will contain the latest code changes in this repository. With each commit in this repository, a new automatic alpha version will be uploaded there. If you want the most up-to-date code to test things and are okay with the plugin occasionally breaking, you can download this version.

Take a look at [the CHANGELOG](https://github.com/noDRM/DeDRM_tools/blob/master/CHANGELOG.md) to see a list of changes since the last version by Apprentice Harper (v7.2.1). 

My version of the plugin should both work with Calibre 5.x/6.x (Python 3) as well as Calibre 4.x and lower (Python 2). If you encounter issues with this plugin in Calibre 4.x or lower, please open a bug report. 

# Original README from Apprentice Harper

This is a repository that tracks all the scripts and other tools for removing DRM from ebooks that I could find, committed in date order as best as I could manage. (Except for the Requiem tools for Apple's iBooks, and Convert LIT for Microsoft's .lit ebooks.) This includes the tools from a time before Apprentice Alf had a blog, and continues through to when Apprentice Harper (with help) took over maintenance of the tools.

The individual scripts are now released as two plugins for calibre: DeDRM and Obok. 
The DeDRM plugin handles books that use Amazon DRM, Adobe Digital Editions DRM, Barnes & Noble DRM, and some historical formats.
The Obok plugin handles Kobo DRM.

Users with calibre 5.x or later should use release 7.2.0 or later of the tools.
Users with calibe 4.x or earlier should use release 6.8.x of the tools.

For the latest Amazon KFX format, users of the calibre plugin should also install the KFX Input plugin from the standard calibre plugin menu. It's also available from the MobileRead thread here: https://www.mobileread.com/forums/showthread.php?t=291290

Note that Amazon changes the DRM for KFX files frequently. What works for KFX today might not work tomorrow.

I welcome contributions from others to improve these tools, from expanding the range of books handled, improving key retrieval,  to just general bug fixes, speed improvements and UI enhancements.

I urge people to read the FAQs. But to cover the most common: Do remember to unzip the downloaded archive to get the plugin (beta versions may be just the plugin  don't unzip that). You can't load the whole tools archive into calibre.

My special thanks to all those developers who have done the hard work of reverse engineering to provide the initial tools.

Apprentice Harper.
