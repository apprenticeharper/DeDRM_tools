KindleBooks (Originally called K4MobiDeDRM and Topaz_Tools)

Most users will be better off using the DeDRM applications or the calibre plugin. This script is provided more for historical interest than anything else.


This tools combines functionality of MobiDeDRM with that of K4PCDeDRM, K4MDeDRM, and K4DeDRM.  Effectively, it provides one-stop shopping for all your Mobipocket, Kindle for iPhone/iPad/iPodTouch, Kindle for PC, and Kindle for Mac needs and should work for both Mobi and Topaz ebooks.

Preliminary Steps:

1. Make sure you have Python 2.5, 2.6 or 2.7 installed (32 bit) and properly set as part of your SYSTEM PATH environment variable (On Windows I recommend ActiveState's ActivePython. See their web pages for instructions on how to install and how to properly set your PATH). On Mac OSX 10.5 and later everything you need is already installed.


Instructions:

1. double-click on KindleBooks.pyw

2. In the window that opens:
hit the first '...' button to locate your DRM Kindle-style ebook

3. Then hit the second '...' button to select an output directory for the unlocked file

4. If you have multiple Kindle.Info files and would like to use one specific one, please hit the third "...' button to select it.  Note, if you only have one Kindle.Info file (like most users) this can and should be left blank.

5. Then add in any PIDs you need from KindleV1, Kindle for iPhone/iPad/iPodTouch, or other single PID devices to the provided box as a comma separated list of 10 digit PID numbers.  If this is a Kindle for Mac or a Kindle for PC book then you can leave this box blank


6. If you have standalone Kindles, add in any 16 digit Serial Numbers as a comma separated list.  If this is a Kindle for Mac or a Kindle for PC book then you can leave this box blank

7.  hit the 'Start' button

After a short delay, you should see progress in the Conversion Log window indicating is the unlocking was a success or failure.



If your book was a normal Mobi style ebook:
   If successful, you should see a "_nodrm" named version Mobi ebook.
   If not please examine the Conversion Log window for any errors.



If your book was actually a Topaz book:

Please note that Topaz is most similar to a poor man's image only PDF in style.  It has glyphs and x,y positions, ocrText used just for searching, that describe the image each page all encoded into a binary xml-like set of files.

If successful, you will have 3 zip archives created.

1. The first is BOOKNAME_nodrm.zip.
   You can import this into calibre as is or unzip it and edit the book.html file you find inside.  To create the book.html, Amazon's ocrText is combined with other information to recreate as closely as possible what the original book looked like.  Unfortunately most bolding, italics is lost.  Also, Amazon's ocrText can be absolutely horrible at times.  Much work will be needed to clean up and correct Topaz books.  

2. The second is BOOKNAME_SVG.zip
   You can also import this into calibre or unzip it and open the indexsvg.xhtml file in any good Browser (Safari, Firefox, etc). This zip contains a set of svg images (one for each pages is created) and it shows the page exactly how it appeared.  This zip can be used to create an image only pdf file via post conversion.

3. The third is BOOKNAME_XML.zip
   This is a zip archive of the decrypted and translated xml-like descriptions of each page and can be archived/saved in case later code can do a better job	converting these files.  These are exactly what a Topaz books guts are.  You should take a look at them in any text editor to see what they look like.

If the Topaz book conversion is not successful, a large _DEBUG.zip archive of all of the pieces is created and this can examined along with the Conversion Log window contents to determine the cause of the error and hopefully get it fixed in the next release.


