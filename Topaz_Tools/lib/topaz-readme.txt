Contributors:
     cmbtc - removal of drm which made all of this possible
     clarknova - for all of the svg and glyph generation and many other bug fixes and improvements
     skindle - for figuing out the general case for the mode loops
     some updates -  for conversion to xml, basic html
     DiapDealer - for extensive testing and feedback, and standalone linux/macosx version of cmbtc_dump
     stewball - for extensive testing and feedback

and many others for posting, feedback and testing
  

This is experimental and it will probably not work for you but...

ALSO:  Please do not use any of this to steal.  Theft is wrong. 
       This is meant to allow conversion of Topaz books for other book readers you own

Here are the steps:

1. Unzip the topazscripts.zip file to get the full set of python scripts.
The files you should have after unzipping are:

cmbtc_dump.py - (author: cmbtc) unencrypts and dumps sections into separate files for Kindle for PC and Mac
decode_meta.py - converts metadata0000.dat to make it available
convert2xml.py - converts page*.dat, other*.dat, and glyphs*.dat files to pseudo xml descriptions
flatxml2html.py - converts a "flattened" xml description to html using the ocrtext
stylexml2css.py - converts stylesheet "flattened" xml into css (as best it can)
getpagedim.py - reads page0000.dat to get the book height and width parameters
genxml.py - main program to convert everything to xml
genhtml.py - main program to generate "book.html"
gensvg.py - (author: clarknova) main program to create an xhmtl page with embedded svg graphics
k4mutils.py - Mac OSX support routines for cmbtc_dump.py
k4pcutils.py - Windows support routines for cmbtc_dump.py



Please note, these scripts all import code from each other so please
keep all of these python scripts together in the same place.



2. Remove the DRM from the Topaz book and build a directory 
of its contents as files

All Thanks go to CMBTC who broke the DRM for Topaz - without it nothing else 
would be possible

If you purchased the book for Kindle for PC or Kindle for Mac, you must do the following:

   cmbtc_dump.py -d -o TARGETDIR [-p pid] YOURTOPAZBOOKNAMEHERE


If you purchased the book for a standalone Kindle 1 or ipod/iphone/ipad 
and you know your pid (at least the first 8 characters) then you should 
add that using -p 12345678 switch as indicated above, replacing the 
12345678 with the 8 characters of your pid


This should create a directory called "TARGETDIR" in your current directory.  
It should have the following files in it:

metadata0000.dat - metadata info
other0000.dat - information used to create a style sheet
dict0000.dat - dictionary of words used to build page descriptions
page - directory filled with page*.dat files
glyphs - directory filled with glyphs*.dat files
img - directory filled with images
color_img - directory used for color images

3. REQUIRED: Create xhtml page descriptions with embedded svg
that show the exact representation of each page as an image
with proper glyphs and positioning.

The step must NOW be done BEFORE attempting conversion to html

   gensvg.py TARGETDIR

When complete, use a web-browser to open the page*.xhtml files
in TARGETDIR/svg/ to see what the book really looks like.

If you would prefer pure svg pages, then use the -r option
as follows:

   gensvg.py -r TARGETDIR


All thanks go to CLARKNOVA for this program.  This program is 
needed to actually see the true image of each page and so that
the next step can properly create images from glyphs for 
monograms, dropcaps and tables.


4. Create "book.html" which can be found in "TARGETDIR" after 
completion.  

   genhtml.py TARGETDIR


***IMPORTANT NOTE***  This html conversion can not fully capture 
all of the layouts and styles actually used in the book
and the resulting html will need to be edited by hand to 
properly set bold and/or italics, handle font size changes,
and to fix the sometimes horiffic mistakes in the ocrText
used to create the html.  

If there critical pages that need fixed layout in your book
you might want to consider forcing these fixed regions to
become svg images using the command instead

    genhtml.py --fixed-image TARGETDIR

This will convert all fixed regions into svg images at the 
expense of increased book size, slower loading speed, and 
a loss of the ability to search for words in those regions

FYI: Sigil is a wonderful, free cross-
platform program that can be used to edit the html and 
create an epub if you so desire.


5. Optional Step:  Convert the files in "TARGETDIR" to their 
xml descriptions which can be found in TARGETDIR/xml/ 
upon completion.

   genxml.py TARGETDIR


These conversions are important for allowing future (and better)
conversions to come later.

