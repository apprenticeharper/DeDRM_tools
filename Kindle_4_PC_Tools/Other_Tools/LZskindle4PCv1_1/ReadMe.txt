Ezskindle4PC.exe 

This executable program makes using skindle easier for people using Windows PC’s.

I do not know if it will work under any other operating system, however, I have included 
the source code should anyone want to port it into other operating systems.

To use this program:

1. Copy the ezskindle4PC.exe into the same directory with the skindle files.
2. Copy the kindle book into the same directory.
3. double click the EZskindle4PCv1_0.exe file.
a. A DOS window will open and you will be asked for the name of the file you want to work with.
4. Type in the book’s file name.  (it will look something like B000WCTBTA_EBOK.prc)
5. The program will then check if it is a Topaz file and then create the output file name using the 
first part of the input file name. It will use “tpz” file extension for Topaz books and will use “azw” 
for non topaz books.  The files with the “azw” format can be converted to other ebook formats using 
Calibre.  If you want to convert Topaz books to other formats you need to use Topaz tools not skindle.
6. The program will then create a command line and call the skindle program to process the book and 
remove the DRM.
7. The program will pause and allow you to see the result of the skindle process.  
8. Press any key to close the program.

version 1.1
Ok

Found a new 32 bit compiler and I think I have worked out the kinks.
