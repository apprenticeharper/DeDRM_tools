The Topaz Tools work for "Kindle for PC" books, "Kindle for Mac" books, original standalone Kindles that have never been updated to firmware 2.5 or later, and Kindle for iPhone/iPad/iPodTouch (where the PID is known).


For Topaz:

1. Make sure you have Python 2.X installed (32 bit) and properly set as part of your SYSTEM PATH environment variable (On Windows I recommend ActivePython. See their web pages for instructions on how to install and how to properly set your PATH). On Mac OSX 10.6 everything you need is already installed.

2. Simply download the latest tools_vX.X.zip file (see the comments after the first post on this blog) and extract the entire archive. Do not move or rename anything after extracting the entire archive.

3. move to tools\Topaz_Tools\

4. double-click on TopazExtract.pyw

Hit the first “…” button to select the Topaz book with DRM that you want to convert

Hit the second “…” to select an entirely new directory to extract the many book pieces into

And add info for your PID (or extra PIDs) if needed (should not be needed for Kindle For PC or Kindle for Mac).  This field is useful if you have Kindle for iPad/iPhone/iPodTouch or an old Kindle V1 and know your device PID.

Hit the Start button

3. Next double-click on TopazFiles2SVG.pyw
(use the “…” button to select the new directory you created from the previous step, and hit Start)

4. Finally double-click on TopazFiles2HTML.pyw
(use the “…” button to slect the new directory you created in step 2, and hit Start)

5. After all of this you should have book.html inside the directory you created with its own image directory and css style sheet. This file is created from the ocr that is done by Amazon and stored in the Topaz file. All errors belong to Amazon.

Inside of that same directory, you should have an svg directory which has an exact image of each page of the book. To see it, simply open the .xhtml page which has the embedded svg image in a good browser (Firefox, Safari, etc)

If you run into any problems – and there can be problems because the format has not been completely reversed engineered, simply copy the entire contents of the Conversion Log window and paste them in a post here or on the Dark Reverser’s New Blog and I will find it and try to help

