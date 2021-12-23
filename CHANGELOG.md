# Changelog

List of changes since the fork of Apprentice Harper's repository: 

## Fixes in v10.0.0 (2021-11-17):

- CI testing / linting removed as that always failed anyways. The CI now "just" packages the plugin.
- Support for the Readium LCP DRM (also known as "CARE DRM" or "TEA DRM"). This supports EPUB and PDF files. It does not yet support Readium LCPDF/LPF/LCPA/LCPAU/LCPDI files, as I don't have access to any of these. If you have an LCP-protected file in one of these formats that this plugin does not work with, please open [an issue](https://github.com/noDRM/DeDRM_tools/issues) and attach the file to the report.
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

## Fixes on master (not yet released):

- Fix issue where importing a key from Adobe Digital Editions would fail in Python2 (Calibre < 5) if there were non-ASCII characters in the username.
- Add code to support importing multiple decryption keys from ADE (click the 'plus' button multiple times).
- Improve epubtest.py to also detect Kobo & Apple DRM.
- Small updates to the LCP DRM error messages.
- Merge ignobleepub into ineptepub so there's no duplicate code.
- Support extracting the B&N / Nook key from the NOOK Microsoft Store application (based on [this script](https://github.com/noDRM/DeDRM_tools/discussions/9) by fesiwi).
- Support extracting the B&N / Nook key from a data dump of the NOOK Android application.
- Support adding an existing B&N key base64 string without having to write it to a file first.
