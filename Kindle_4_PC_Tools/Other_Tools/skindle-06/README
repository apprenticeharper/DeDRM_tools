
/*
   Copyright 2010 BartSimpson aka skindle
   
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
*/

/*
 * Dependencies: zlib (included)
 * build on cygwin using make and the included make file
 * A fully functionaly windows executable is included
 */

/*
 * MUST be run on the computer on which KindleForPC is installed
 * under the account that was used to purchase DRM'ed content.
 * Requires your kindle.info file which can be found in something like:
 * <User home>\...\Amazon\Kindle For PC\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}
 * where ... varies by platform but is "Local Settings\Application Data" on XP
 * skindle will attempt to find this file automatically.
 */

/*
  What: KindleForPC DRM removal utility to preserve your fair use rights!
  Why: Fair use is a well established doctrine, and I am no fan of vendor
       lockin.
  How: This utility implements the PID extraction, DRM key generation and
       decryption algorithms employed by the KindleForPC application. This
       is a stand alone app that does not require you to determine a PID on
       your own, and it does not need to run KindleForPC in order to extract
       any data from memory.
  
  Shoutz: The DarkReverser - thanks for mobidedrm!  The last part of this
       is just a C port of mobidedrm.
       labba and I<3cabbages for motivating me to do this the right way.
       You guys shouldn't need to spend all your time responding to all the
       changes Amazon is going to force you to make in unswindle each time
       the release a new version.
       CMBDTC - nice work on the topaz break!
       Lawrence Lessig - You are my hero. 'Nuff said.
       Cory Doctorow - A voice of reason in a sea of insanity
   Thumbs down: Disney, MPAA, RIAA - you guys suck.  Making billions off 
       of the exploitation of works out of copyright while vigourously
       pushing copyright extension to prevent others from doing the same
       is the height of hypocrasy.
       Congress - you guys suck too.  Why you arrogant pricks think you
       are smarter than the founding fathers is beyond me.
 */

Rationale:
Need a tool to enable fair use of purchased ebook content.
Need a tool that is not dependent on any particular version of
KindleForPC and that does not need to run KindleForPC in order to
extract a PID. The tool documents the structure of the kindle.info
file and the data and algorthims that are used to derive per book
PID values.

Installing:
A compiled binary is included.  Though it was built using cygwin, it
should not require a cygwin installation in order to run it.  To build
from source, you will need cygwin with gcc and make.  
This has not been tested with Visual Studio, though you may be able to
pile all the files into a project and add the Crypt32.lib, Advapi32 and
zlib1 dependencies to build it.

usage: ./skindle [-d] [-v] -i <ebook file> -o <output file> [-k kindle.info file] [-p pid]
    -d optional, for topaz files only, produce a decompressed output file
    -i required name of the input mobi or topaz file
    -o required name of the output file to generate
    -k optional kindle.info path
    -v dump the contents of kindle.info
    -p additional PID values to attempt (can specifiy multiple times)

You only need to specify a kindle.info path if skindle can't find
your kindle.info file automatically