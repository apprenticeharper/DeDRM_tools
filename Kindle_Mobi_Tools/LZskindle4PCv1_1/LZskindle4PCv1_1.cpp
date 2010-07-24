#include <cstdlib>
#include <iostream>
#include <fstream>
//#include <conio.h>

using namespace std;

int main(int argc, char *argv[])
{
    // Variable Declarations ??
    char buffer[80];
    int error = 0;
//    int YesNo = 0;
//    int exit  = 0;
 // Variables  EZskindle4PC 
	int  TopazTrue    = 0;
	int  strlength    = 0;
	char uinfile[80];
 	char outfile[80];
	char command[80];
	char buffer2[20];
	char tempfile[80];
   
  // Initialize strings
	strcpy(uinfile,"");
	strcpy(outfile,"");
	strcpy(buffer,"");
	strcpy(buffer2,"");
	strcpy(command,"skindle ");          // string preloaded with "skindle "

      
   //// Beginning of program code //////////////////////////////////////////////////////////// 

    system("dir /b .\\input\\*.* > books.txt");  // Create txt file with list of books
                                                 // No testing of file type being done
                                                 // I am letting skindle determing if valid 
                                                 // file type
    //  Read in the list of book file names
    
   ifstream infile("books.txt");   

    do  // while not end of file
      {
        infile.getline(buffer,50);  // load the first 50 characters of the line to buffer
        
 
        if(strcmp(buffer, "")!= 0)  // If there is file name in the buffer do this on last loop buffer will be empty
         {
            strcpy(uinfile,buffer);      // load file name from buffer

 	        strcpy(tempfile,".\\input\\");  // load directory name for input files
            strcat(tempfile,buffer);        // load the file name
	        ifstream infile2(tempfile);     // open the book file for reading
	        infile2.getline(buffer2,4);     // load first 4 char from file

            infile2.close();    // close the book file


	        if (strncmp (buffer2,"TPZ",3)==0)      // open file and test first 3 char if TPZ then book is topaz
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
         strcat(command,".\\input\\");              // Add the input directory to the command line
	     strcat(command,uinfile);                   // add the input file name to the command line
	     strcat(command," -o ");                    // add the output switch to the command line
	     strcat(command,".\\output\\");             // Add directory for out files
	     strcat(command,outfile);                   // Add the output file name to the command line

	     cout << "\n\n   The skindle program is called here.\n";
	     cout << "   Any errors reported between here and \"The command line used was:\"\n";
	     cout << "   Are errors from the skindle program. Not EZskindle4PC.\n\n";
	  

	     system(command);                            // call skindle program to convert the book
	  
	  
	     cout << "\n\n   The command line used was:\n\n";
	     cout << " " << command << "\n\n\n\n";


       }// end of file name in the buffer required to prevent execution on EOF


 
 	   strcpy(command,"skindle ");          // reset strings and variables for next book
	   strcpy(outfile,"");
	   strcpy(uinfile,"");
	   strcpy(buffer,"");
	   strcpy(buffer2,"");
	   TopazTrue = 0;
	   strlength = 0;

      }while (! infile.eof() );  // no more books in the file
    
    infile.close();    // close books.txt
      

//    cout << "\n\n\n Do you want to delete all of the books from the input directory?\n\n";  
//    cout << " DO NOT DELETE IF THESE ARE ONLY COPY OF YOUR BOOKS!!!!\n\n";
//    cout << " Y or N: ";


//    do {  // while not yes or no
//          YesNo = getch();           // This is a DOS/Windows console command not standard C may not be
//                                     // Usable under Unix or Mac implementations 
//             
//             if((YesNo == 121)||(YesNo == 89))  // y or Y is true
//               {
//                 exit = 1;  // valid input exit do while loop
//                cout << "\n\n";
//                 system("del .\\input\\*.*");   // delete everything in the input directory      
//                 cout << "\n\n";
//               }
//             if((YesNo == 110)||(YesNo == 78))  // n or N is true
//               {
//                 exit = 1;  // valid input exit do while loop      
//               }
//       
//       }while (exit != 1);
//    cout << "\n\nYesNo = " << YesNo << "\n\n";

    system("PAUSE");
    
    system("del books.txt");  // Delete txt file with list of books
    return EXIT_SUCCESS;
}
