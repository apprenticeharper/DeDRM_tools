# [Guide] How to remove DRM
Refer to [Wiki Page](https://github.com/apprenticeharper/DeDRM_tools/wiki/Exactly-how-to-remove-DRM)

# DeDRM_tools
DeDRM tools for ebooks

This is a repository that tracks all the scripts and other tools for removing DRM from ebooks that I could find, committed in date order as best as I could manage. (Except for the Requiem tools for Apple's iBooks, and Convert LIT for Microsoft's .lit ebooks.) This includes the tools from a time before Apprentice Alf had a blog, and continues through to when Apprentice Harper (with help) took over maintenance of the tools.

The individual scripts are now released as two plugins for calibre: DeDRM and Obok. 
The DeDRM plugin handles books that use Amazon DRM, Adobe Digital Editions DRM (version 1), Barnes & Noble DRM, and some historical formats.
The Obok plugin handles Kobo DRM.

Users with calibre 5.x or later should use release 7.2.0 or later of the tools.
Users with calibe 4.x or earlier should use release 6.8.x of the tools.

For the latest Amazon KFX format, users of the calibre plugin should also install the KFX Input plugin from the standard calibre plugin menu. It's also available from the MobileRead thread here: https://www.mobileread.com/forums/showthread.php?t=291290

Note that Amazon changes the DRM for KFX files frequently. What works for KFX today might not work tomorrow.

I welcome contributions from others to improve these tools, from expanding the range of books handled, improving key retrieval,  to just general bug fixes, speed improvements and UI enhancements.

I urge people to read the FAQs. But to cover the most common: Use ADE 2.0.1 to be sure not to get the new DRM scheme that these tools can't handle. Do remember to unzip the downloaded archive to get the plugin (beta versions may be just the plugin  don't unzip that). You can't load the whole tools archive into calibre.

My special thanks to all those developers who have done the hard work of reverse engineering to provide the initial tools.

Apprentice Harper.
