From Apprentice Alf's Blog

Barnes & Noble/Fictionwise eReader, .pdb

Barnes & Noble’s .pdb eReader format is one of the survivors from the early days of ebooks. Internally, text is marked up in PML – Palm Markup Language. This makes conversion to other formats more difficult.

Barnes and Noble .pdb ebooks use a form of Social DRM which requires information on your Credit Card Number (last 8 digits only) and the Name on the Credit card to unencrypt the book that was purchased with that credit card.

There are three scripts used to decrypt and convert eReader ebooks.

The first, eReaderPDB2PML.pyw removes the DRM and extracts the PML and images from the ebook into a folder. It’s then possible to use the free DropBook (available for Mac or Windows) to compile the PML back into a DRM-free eReader file.

The second script, Pml2HTML.pyw, converts the PML file extracted by the first script into xhtml, which can then be converted into your preferred ebook format with a variety of tools.

The last script is eReaderPDB2PMLZ.pyw and it removes the DRM and extracts the PML and images from the ebook into a zip archive that can be directly imported into Calibre.

All of these scripts are gui python programs.   Python 2.5 or later (32 bit) is already installed in Mac OSX 10.5 and later.  We recommend ActiveState's Active Python Version 2.5 or later (32 bit) for Windows users.

Simply double-click to launch these applications and follow along.


