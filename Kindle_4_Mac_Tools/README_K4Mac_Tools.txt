Kindle_4_Mac_Tools version 1.2

Kindle_4_Mac_Tools_v1.2.zip
http://www.mediafire.com/?8nz9rkg6p9nq23r


New in this release:
 - support to identify Topaz Books and print their PID
   so that standard Topaz_Tools can be used later if
   desired (only works with Kindle Version 1.2.0)

Prerequisites:

   - Kindle for Mac.app Version 1.0.0 Beta 1 (27214)
     (this is the original version)

	or

     Kindle.app Version 1.2.0 (30689)
     (this is the current version at Amazon)


   - XCode Developer Tools **must** be Installed 
    (see your latest Mac OS X Install Disk for the installer)


The directions for use are:

1. double-click to unzip the Kindle_4_Mac_Tools_v1.2.zip

2. open the Kindle_4_Mac_Tools folder 

3. double-click on K4Munswindle.pyw

In the window that opens:

– hit the first '...' button to locate your Kindle Application 
     if it is not in /Applications

– hit the second '...' button to select an output directory 
      (defaults to your Desktop)

– hit the 'Start' button

After a short delay, your Kindle application should open up automagically

In Kindle for Mac:

 - hit the  “Home” button to go home. 

 - double-click on ONE of your books.
   This should open the book.

Once the book you want is open

-  hit the “Home” button and then exit the Kindle for Mac application

Once you have exited the Kindle for Mac application you should see one of the following:

  - If the book you selected was a Topaz Book:

      A Warning message will appear in the Conversion Log indicating 
      that the book you opened was Topaz, along with the 8 digit PID 
      needed to convert it using Topaz_Tools

  - If the book you selected was a Mobi book:

      MobiDeDRM will be automagically started in the Conversion Log 
      window and if successful you should find your decoded book in 
      the output directory.

