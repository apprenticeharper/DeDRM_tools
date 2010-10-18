#include <cstdlib>
#include <iostream>
#include <conio.h>
#include <fstream>

using namespace std;

int main(int argc, char *argv[])
{
// Variables
	int  TopazTrue    = 0;
	int  strlength    = 0;
	char uinfile[80];
 	char outfile[80];
	char command[80];
	char buffer[80];

// String initialization
	strcpy(uinfile,"");
	strcpy(outfile,"");
	strcpy(buffer,"");
	strcpy(command,"skindle ");          // string preloaded with "skindle "
	
	
    cout << "\n\n\n     Please enter the name of the book to be converted:\n\n     ";
    cout << "     Don't forget the prc file extension!\n\n     ";
    cout << "     Watch out for zeros and Os. Zeros are skinny and Os are fat.\n\n\n     ";

      cin >> uinfile;                             // get file name of the book to be converted from user


	  ifstream infile(uinfile);
	  infile.getline(buffer,4);


	  if (strncmp (buffer,"TPZ",3)==0)      // open file and test first 3 char if TPZ then book is topaz
	  { 
		 TopazTrue = 1;                             // This is a Topaz file
	  }


	  strlength = strlen(uinfile);

	  if(strlength > 13)
	    {
         strncat(outfile,uinfile,10);                // Create output file name using first 10 char of input file name
	    }
	  else
	    {
	       strncat(outfile,uinfile, (strlength - 4));  // If file name is less than 10 characters
	    }
	  if(TopazTrue == 1)                         // This is Topaz Book
	         {
				 strcat(command,"-d ");          // Add the topaz switch to the command line

				 strcat(outfile,".tpz");         // give tpz file extension to topaz output file
	         } // end of TopazTrue
	  else
	  {
		  strcat(outfile,".azw"); 
	  } // if not Topaz make it azw

	  strcat(command,"-i ");                     // Add the input switch to the command line
	  strcat(command,uinfile);                    // add the input file name to the command line
	  strcat(command," -o ");                    // add the output switch to the command line
	  strcat(command,outfile);                   // Add the output file name to the command line

	cout << "\n\n   The skindle program is called here.\n";
	cout << "   Any errors reported between here and \"The command line used was:\"\n";
	cout << "   Are errors from the skindle program. Not EZskindle4PC.\n\n";
	  

	 system(command);                            // call skindle program to convert the book
	  
	  
	cout << "\n\n   The command line used was:\n\n";
	cout << " " << command << "\n";
	cout << "\n\n\n   Please note the output file is created from the input";
	cout << "\n   file name. The file extension is changed to tpz for Topaz";
	cout << "\n   files and to azw for non-Topaz files. Also, _EBOK is removed ";
	cout << "\n   from the file name.  This is to make it eaiser to identify ";
    cout << "\n   the file with no DRM.";

	

    system("PAUSE");
    return EXIT_SUCCESS;
}
