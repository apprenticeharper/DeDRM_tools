Contributors:
     cmbtc - removal of drm which made all of this possible
     clarknova - for all of the svg and glyph generation and many other bug fixes and improvements
     skindle - for figuing out the general case for the mode loops
     some updates -  for conversion to xml, basic html
     DiapDealer - for extensive testing and feeback

and others for posting, feedback and testing
  

This is experimental and it will probably not work for you but...

ALSO:  Please do not use any of this to steal.  Theft is wrong. 
       This is meant to allow conversion of Topaz books for other book readers you own

Here are the steps:

1. Unzip the topazscripts.zip file to get the full set of python scripts.
The files you should have after unzipping are:

cmbtc_dump.py - (author: cmbtc) unencrypts and dumps sections into separate files
decode_meta.py - converts metadata0000.dat to human readable text (for the most part)
convert2xml.py - converts page*.dat, other*.dat, and glyphs*.dat files to pseudo xml descriptions
flatxml2html.py - converts a "flattened" xml description to html using the ocrtext
stylexml2css.py - converts stylesheet "flattened" xml into css (as best it can)
genxml.py - main program to convert everything to xml
genhtml.py - main program to generate "book.html"
gensvg.py - (author: clarknova) main program to create an svg grpahic of each page

Please note, gensvg.py, genhtml.py, and genxml.py import and use
decode_meta.py, convert2xml.py, flatxml2html.py, and stylexml2css.py 
so please keep all of these python scripts together in the same place.



2. Remove the DRM from the Topaz book and build a directory 
of its contents as files

All Thanks go to CMBTC who broke the DRM for Topaz - without it nothing else 
would be possible

   cmbtc_dump.py -d -o TARGETDIR [-p pid] YOURTOPAZBOOKNAMEHERE

This should create a directory called "TARGETDIR" in your current directory.  
It should have the following files in it:

metadata0000.dat - metadata info
other0000.dat - information used to create a style sheet
dict0000.dat - dictionary of words used to build page descriptions
page - directory filled with page*.dat files
glyphs - directory filled with glyphs*.dat files



3. Convert the files in "TARGETDIR" to their xml descriptions
which can be found in TARGETDIR/xml/ upon completion.

   genxml.py TARGETDIR



4. Create book.html which can be found in "TARGETDIR" after 
completion.  This html conversion can not fully capture 
all of the layouts actually used in the book and needs to 
be edited to include special font handling such as bold 
or italics that can not be determined from the ocrText
information or the style information.  If you want to 
see things exactly as they were, see step 5 below.

   genhtml.py TARGETDIR



5. Create an svg description of each page which can
be found in TARGETDIR/svg/ upon completion.

All thanks go to CLARKNOVA for this program.  This program is 
needed to actually see the true image of each page so that hand
editing of the html created by step 4 can be done.  

Or use the resulting svg files to read each page of the book
exactly as it has been laid out originally.

   gensvg.py TARGETDIR

