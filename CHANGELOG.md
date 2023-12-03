# Changelog

List of changes since the fork of Apprentice Harper's repository: 

## Fixes in v10.0.0 (2021-11-17):

- CI testing / linting removed as that always failed anyways. The CI now "just" packages the plugin.
- ~Support for the Readium LCP DRM (also known as "CARE DRM" or "TEA DRM"). This supports EPUB and PDF files. It does not yet support Readium LCPDF/LPF/LCPA/LCPAU/LCPDI files, as I don't have access to any of these. If you have an LCP-protected file in one of these formats that this plugin does not work with, please open [an issue](https://github.com/noDRM/DeDRM_tools/issues) and attach the file to the report.~ (removed due to a DMCA request, see #18 )
- Add new Github issue report form which forces the user to include stuff like their Calibre version to hopefully increase the quality of bug reports.
- Issues with PDF files in Calibre 5 should be fixed (merged [apprenticeharper/DeDRM_tools#1689](https://github.com/apprenticeharper/DeDRM_tools/pull/1689) ).
- Fixed tons of issues with the B&N PDF DRM removal script ignoblepdf.py. It looks like that has never been tested since the move to Python3. I have integrated the B&N-specific code into ineptpdf.py, the original ignoblepdf.py is now unused. Fairly untested as I don't have any PDFs with B&N DRM.
- Issues with Obok key retrieval fixed (merged [apprenticeharper/DeDRM_tools#1691](https://github.com/apprenticeharper/DeDRM_tools/pull/1691) ).
- Issues with obfuscated Adobe fonts fixed (fixes [apprenticeharper/DeDRM_tools#1828](https://github.com/apprenticeharper/DeDRM_tools/issues/1828) ).
- Deobfuscate font files in EPUBs by default (can be disabled in the plugin settings).
- The standalone adobekey.py script now includes the account UUID in the key file name.
- When extracting the default key from an ADE install, include the account UUID in the key name.
- Adobe key management window size increased to account for longer key names due to the UUID.
- Verify that the decrypted book key has the correct format. This makes it way less likely for issue [apprenticeharper/DeDRM_tools#1862](https://github.com/apprenticeharper/DeDRM_tools/issues/1862) to cause trouble.
- If the Adobe owner UUID of a book being imported happens to be included in a particular key's name, try this key first before trying all the others. This completely fixes [apprenticeharper/DeDRM_tools#1862](https://github.com/apprenticeharper/DeDRM_tools/issues/1862), but only if the key name contains the correct UUID (not always the case, especially for keys imported with older versions of the plugin). It also makes DRM removal faster as the plugin no longer has to attempt all possible keys.
- Remove some additional DRM remnants in Amazon MOBI files (merged [apprenticeharper/DeDRM_tools#23](https://github.com/apprenticeharper/DeDRM_tools/pull/23) ).
- Just in case it's necessary, added a setting to the B&N key generation script to optionally allow the user to select the old key generation algorithm. Who knows, they might want to remove DRM from old books with the old key scheme.
- Add a more verbose error message when trying to remove DRM from a book with the new, not-yet-cracked version of the Adobe ADEPT DRM.
- Added back support for Python2 (Calibre 2.0+). Only tested with ADEPT (PDF & EPUB) and Readium LCP so far, please open an issue if there's errors with other book types.
- Begin work on removing some kinds of watermarks from files after DRM removal. This isn't tested a lot, and is disabled by default. You can enable it in the plugin settings.
- If you're using the [ACSM Input Plugin / DeACSM](https://www.mobileread.com/forums/showthread.php?t=341975), the encryption key will automatically be extracted from that plugin if necessary.

## Fixes in v10.0.1 (2021-11-19): 

- Hotfix update to fix broken EPUB DRM removal due to a typo.

## Fixes in v10.0.2 (2021-11-29):

- Fix Kindle for Mac key retrieval (merged [apprenticeharper/DeDRM_tools#1936](https://github.com/apprenticeharper/DeDRM_tools/pull/1936) ), fixing #1. 
- Fix Adobe key retrieval in case the username has been changed (merged [apprenticeharper/DeDRM_tools#1946](https://github.com/apprenticeharper/DeDRM_tools/pull/1946) ). This should fix the error "failed to decrypt user key key".
- Fix small issue with elibri watermark removal.
- Adobe key name will now contain account email.

## Fixes in v10.0.3 (2022-07-13):

- Fix issue where importing a key from Adobe Digital Editions would fail in Python2 (Calibre < 5) if there were non-ASCII characters in the username.
- Add code to support importing multiple decryption keys from ADE.
- Improve epubtest.py to also detect Kobo & Apple DRM.
- ~Small updates to the LCP DRM error messages.~ (removed due to a DMCA request, see #18 ).
- Merge ignobleepub into ineptepub so there's no duplicate code.
- Support extracting the B&N / Nook key from the NOOK Microsoft Store application (based on [this script](https://github.com/noDRM/DeDRM_tools/discussions/9) by fesiwi).
- Support extracting the B&N / Nook key from a data dump of the NOOK Android application.
- Support adding an existing PassHash / B&N key base64 string without having to write it to a file first.
- Support extracting PassHash keys from Adobe Digital Editions.
- Fix a bug that might have stopped the eReader PDB DRM removal from working (untested, I don't have any PDB books)
- Fix a bug where the watermark removal code wouldn't run for DRM-free files.
- ineptpdf: Add code to plugin to support "Standard" (tested) and "Adobe.APS" (untested) encrypted PDFs using the ineptpdf implementation (PDF passwords can be entered in the plugin settings)
- ineptpdf: Support for decrypting PDF with owner password instead of user password.
- ineptpdf: Add function to return Filter name.
- ineptpdf: Support for V=5, R=5 and R=6 PDF files, and for AES256-encrypted PDFs.
- ineptpdf: Disable cross-reference streams in the output file. This may make PDFs slightly larger, but the current code for cross-reference streams seems to be buggy and sometimes creates corrupted PDFs.
- Drop support for importing key data from the ancient, pre "DeDRM" Calibre plugins ("Ignoble Epub DeDRM", "eReader PDB 2 PML" and "K4MobiDeDRM"). These are from 2011, I doubt anyone still has these installed, I can't even find a working link for these to test them. If you still have encryption keys in one of these plugins, you will need to update to DeDRM v10.0.2 or older (to convert the keys) before updating to DeDRM v10.0.3 or newer.
- Some Python3 bugfixes for Amazon books (merged #10 by ableeker).
- Fix a bug where extracting an Adobe key from ADE on Linux through Wine did fail when using the OpenSSL backend (instead of PyCrypto). See #13 and #14 for details, thanks acaloiaro for the bugfix.
- Fix IndexError when DeDRMing some Amazon eBooks.
- Add support for books with the new ADE3.0+ DRM by merging #48 by a980e066a01. Thanks a lot! (Also fixes #96 on MacOS)
- Remove OpenSSL support, now the plugin will always use the Python crypto libraries.
- Obok: Fix issues with invalid UTF-8 characters by merging #26 by baby-bell.
- ineptpdf: Fix broken V=3 key obfuscation algorithm. 
- ineptpdf: (Hopefully) fix issues with some B&N PDF files.
- Fix broken Amazon K4PC key retrieval (fixes #38)
- Fix bug that corrupts output file for Print-Replica Amazon books (fixes #30).
- Fix Nook Study key retrieval code (partially fixes #50).
- Make the plugin work on Calibre 6 (Qt 6). (fixes #54 and #98) If you're running Calibre 6 and you notice any issues, please open a bug report.

## Fixes in v10.0.9 (RC for v10.1.0, 2023-08-02):

Note that versions v10.0.4(s), v10.0.5(s) and v10.0.6(s) were released by other people in various forks, so I have decided to make a larger version jump so there are no conflicting version numbers / different builds with the same version number. 

This is v10.0.9, a release candidate for v10.1.0. I don't expect there to be major issues / bugs, but since a lot of code has changed in the last year I wanted to get some "extended testing" before this becomes v10.1.0. 

- Fix a bug introduced with #48 that breaks DeDRM'ing on Calibre 4 (fixes #101).
- Fix some more Calibre-6 bugs in the Obok plugin (should fix #114).
- Fix a bug where invalid Adobe keys could cause the plugin to stop trying subsequent keys (partially fixes #109).
- Fix DRM removal sometimes resetting the ZIP's internal "external_attr" value on Calibre 5 and newer.
- Fix tons of PDF decryption issues (hopefully fixes #104 and other PDF-related issues).
- Small Python 2 / Calibre 4 bugfix for Obok.
- Removing ancient AlfCrypto machine code libraries, moving all encryption / decryption to Python code.
- General cleanup and removal of dead code.
- Fix a bug where ADE account keys weren't automatically imported from the DeACSM plugin when importing a PDF file.
- Re-enable Xrefs in exported PDF files since the file corruption bug is hopefully fixed. Please open bug reports if you encounter new issues with PDF files.
- Fix a bug that would sometimes cause corrupted keys to be added when adding them through the config dialog (fixes #145, #134, #119, #116, #115, #109).
- Update the README (fixes #136) to indicate that Apprentice Harper's version is no longer being updated.
- Fix a bug where PDFs with empty arrays (`<>`) in a PDF object failed to decrypt, fixes #183.
- Automatically strip whitespace from entered Amazon Kindle serial numbers, should fix #158.
- Obok: Add new setting option "Add new entry" for duplicate books to always add them to the Calibre database as a new book. Fixes #148.
- Obok: Fix where changing the Calibre UI language to some languages would cause the "duplicate book" setting to reset.
- Fix Python3 bug in stylexml2css.php script, fixes #232.
- PDF: Ignore invalid PDF objids unless the script is running in strict mode. Fixes some PDFs, apparently. Fixes #233. 
- Bugfix: EPUBs with remaining content in the encryption.xml after decryption weren't written correctly. 
- Support for Adobe's 'aes128-cbc-uncompressed' encryption method (fixes #242).
- Two bugfixes for Amazon DeDRM from Satuoni ( https://github.com/noDRM/DeDRM_tools/issues/315#issuecomment-1508305428 ) and andrewc12 ( https://github.com/andrewc12/DeDRM_tools/commit/d9233d61f00d4484235863969919059f4d0b2057 ) that might make the plugin work with newer versions.
- Fix font decryption not working with some books (fixes #347), thanks for the patch @bydioeds. 
- Fix a couple unicode errors for Python2 in Kindle and Nook code.

## Fixes on master (not yet released):

- Fix a bug where decrypting a 40-bit RC4 pdf with R=2 didn't work.
- Fix a bug where decrypting a 256-bit AES pdf with V=5 didn't work.
- Fix bugs in kgenpids.py, alfcrypto.py, mobidedrm.py and kindlekey.py that caused it to fail on Python 2 (#380).
- Fix some bugs (Python 2 and Python 3) in erdr2pml.py (untested).
- Fix file lock bug in androidkindlekey.py on Windows with Calibre >= 7 (untested).
- A bunch of updates to the external FileOpen ineptpdf script, might fix #442 (untested).

