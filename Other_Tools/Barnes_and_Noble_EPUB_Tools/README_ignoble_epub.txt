Readme.txt

Barnes and Noble EPUB ebooks use a form of Social DRM which requires information on your Credit Card Number and the Name on the Credit card used to purchase the book to actually unencrypt the book.

For more info, see the author's blog:
http://i-u2665-cabbages.blogspot.com/2009_12_01_archive.html

The original scripts by IHeartCabbages are available here as well.  These scripts have been modified to allow the use of OpenSSL in place of PyCrypto to make them easier to run on Linux and Mac OS X, as well as to fix some minor bugs.

There are 2 scripts:

The first is ignoblekeygen_v2.4.pyw.  Double-click to launch it and provide the required information, and this program will generate a key file needed to remove the DRM from the books. The require information is

* Your Name: Your name as set in your Barnes & Noble account, My Account page, directly under PERSONAL INFORMATION. It is usually just your first name and last name separated by a space.
* Credit Card number: This is the credit card number that was on file with Barnes & Noble at the time of download of the ebooks.

This key file need only be generated once unless either you change the default credit card number or your name on your B&N account.

The second is ignobleepub_vX.X.pyw.  Double-click it and it will ask for your key file and the path to the book to remove the DRM from.

All of these scripts are gui python programs.   Python 2.X (32 bit) is already installed in Mac OSX.  We recommend ActiveState's Active Python Version 2.X (32 bit) for Windows users.

These scripts are based on the IHeartCabbages original scripts that allow the replacement of the requirement for PyCrypto with OpenSSL's libcrypto which is already installed on all Mac OS X machines and Linux Boxes.  Window's Users will still have to install PyCrypto or OpenSSL to get these scripts to work properly.

