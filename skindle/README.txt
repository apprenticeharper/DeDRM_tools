
/*
   Copyright 2010 BartSimpson
   
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
 * Dependencies: none
 * build on cygwin: gcc -o skindle skindle.c md5.c sha1.c b64.c -lCrypt32
 * Under cygwin, you can just type make to build it.
 * While the binary builds if you use the -mno-cygwin switch, it fails to
 * work for some reason.  The code should compile with Visual Studio, just
 * add all the files to a project and add the Crypt32.lib dependency and
 * it should build as a Win32 console app.
 */

/*
 * MUST be run on the computer on which KindleForPC is installed
 * under the account that was used to purchase DRM'ed content.
 * Requires your kindle.info file which can be found in something like:
 * <User home>\...\Amazon\Kindle For PC\{AMAwzsaPaaZAzmZzZQzgZCAkZ3AjA_AY}
 * where ... varies by platform but is "Local Settings\Application Data" on XP
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
       Lawrence Lessig - You are my hero. 'Nuff said.
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
A cygwin compatable binary is included.  You need a minimal cygwin
installation in order to run it.  To build from source, you will need
cygwin with gcc and make.  This has not been tested with Visual Studio.

Usage:
./skindle <drm'ed prc file> <name of output file> <kindle.info path>
You need to locate your kindle.info file somewhere on your system.
You can copy it to a local directory, but you need to refer to it
each time you run skindle.
