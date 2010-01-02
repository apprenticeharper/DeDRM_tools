
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
 * Dependencies: none
 * build on cygwin: 
 *     gcc -o skindle skindle.c md5.c sha1.c b64.c -lCrypt32
 * or  gcc -o skindle skindle.c md5.c sha1.c b64.c -lCrypt32 -mno-cygwin
 * Under cygwin, you can just type make to build it.
 * The code should compile with Visual Studio, just add all the files to
 * a project and add the Crypt32.lib dependency and it should build as a
 * Win32 console app.
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

#include <windows.h>
#include <Wincrypt.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>

#include "skinutils.h"
#include "cbuf.h"
#include "mobi.h"
#include "tpz.h"

#include "zlib.h"

int processTopaz(FILE *in, char *outFile, int explode, PidList *extraPids) {
   //had to pile all these up here to please VS2009
   cbuf *tpzHeaders, *tpzBody;
   struct stat statbuf;
   FILE *out;
   unsigned int i;
   char *keysRecord, *keysRecordRecord;
   TopazFile *topaz;
   char *pid;
   
   fstat(fileno(in), &statbuf);

   topaz = parseTopazHeader(in);
   if (topaz == NULL) {
      fprintf(stderr, "Failed to parse topaz headers\n");
      return 0;
   }
   topaz->pids = extraPids;
   
   tpzHeaders = b_new(topaz->bodyOffset);
   tpzBody = b_new(statbuf.st_size);
   
   parseMetadata(topaz);
   
//   dumpMap(bookMetadata);

   keysRecord = getMetadata(topaz, "keys");
   if (keysRecord == NULL) {
      //fail
   }
   keysRecordRecord = getMetadata(topaz, keysRecord);
   if (keysRecordRecord == NULL) {
      //fail
   }

   pid = getBookPid(keysRecord, strlen(keysRecord), keysRecordRecord, strlen(keysRecordRecord));

   if (pid == NULL) {
      fprintf(stderr, "Failed to extract pid automatically\n");
   }
   else {
      char *title = getMetadata(topaz, "Title");   
      fprintf(stderr, "PID for %s is: %s\n", title ? title : "UNK", pid);
   }
   
/*
   unique pid is computed as:
   base64(sha1(idArray . kindleToken . 209_data . 209_tokens))
*/

   //
   //  Decrypt book key
   //
 
   Payload *dkey = getBookPayloadRecord(topaz, "dkey", 0, 0);
   
   if (dkey == NULL) {
      fprintf(stderr, "No dkey record found\n");
      freeTopazFile(topaz);
      return 0;
   }
   
   if (pid) {
      topaz->bookKey = decryptDkeyRecords(dkey, pid);     
      free(pid);
   }
   if (topaz->bookKey == NULL) {
      if (extraPids) {
         int p;
         freePayload(dkey);
         for (p = 0; p < extraPids->numPids; p++) {
            dkey = getBookPayloadRecord(topaz, "dkey", 0, 0);
            topaz->bookKey = decryptDkeyRecords(dkey, extraPids->pidList[p]);
            if (topaz->bookKey) break;
         }
      }
      if (topaz->bookKey == NULL) {
         fprintf(stderr, "No valid pids available, failed to find DRM key\n");
         freeTopazFile(topaz);
         freePayload(dkey);
         return 0;
      }
   }
      
   fprintf(stderr, "Found a DRM key!\n");
   for (i = 0; i < 8; i++) {
      fprintf(stderr, "%02x", topaz->bookKey[i]);
   }
   fprintf(stderr, "\n");

   out = fopen(outFile, "wb");
   if (out == NULL) {
      fprintf(stderr, "Failed to open output file, quitting\n");
      freeTopazFile(topaz);
      freePayload(dkey);
      return 0;
   }

   writeTopazOutputFile(topaz, out, tpzHeaders, tpzBody, explode);
   fwrite(tpzHeaders->buf, tpzHeaders->idx, 1, out);
   fwrite(tpzBody->buf, tpzBody->idx, 1, out);
   fclose(out);
   b_free(tpzHeaders);
   b_free(tpzBody);

   freePayload(dkey);

   freeTopazFile(topaz);
   return 1;
}

int processMobi(FILE *prc, char *outFile, PidList *extraPids) {
   //had to pile all these up here to please VS2009
   PDB header;
   cbuf *keyBuf;
   char *pid;
   FILE *out;
   unsigned int i, keyPtrLen;
   unsigned char *keyPtr;
   unsigned int drmOffset, drm_len;
   unsigned char *drm, *found_key = NULL;
   MobiFile *book;
   int result;
   
   book = parseMobiHeader(prc);

   if (book == NULL) {
      fprintf(stderr, "Failed to read mobi headers\n");
      return 0;
   }

   book->pids = extraPids;
   keyPtr = getExthData(book, 209, &keyPtrLen);

   keyBuf = b_new(128);
   if (keyPtr != NULL) {
      unsigned int idx;
      for (idx = 0; idx < keyPtrLen; idx += 5) {
         unsigned char *rec;
         unsigned int dlen;
         unsigned int rtype = bswap_l(*(unsigned int*)(keyPtr + idx + 1));
         rec = getExthData(book, rtype, &dlen);
         if (rec != NULL) {
            b_add_buf(keyBuf, rec, dlen);
         }
      }
   }

   pid = getBookPid(keyPtr, keyPtrLen, keyBuf->buf, keyBuf->idx);

   b_free(keyBuf);

   if (pid == NULL) {
      fprintf(stderr, "Failed to extract pid automatically\n");
   }
   else {
      fprintf(stderr, "PID for %s is: %s\n", book->pdb.name, pid);
   }

/*
   unique pid is computed as:
   base64(sha1(idArray . kindleToken . 209_data . 209_tokens))
*/

   drmOffset = bswap_l(book->mobi->drmOffset);

   drm_len = bswap_l(book->mobi->drmSize);
   drm = book->record0 + drmOffset;

   if (pid) {
      found_key = parseDRM(drm, book->drmCount, pid, 8);
      free(pid);
   }
   if (found_key == NULL) {
      if (extraPids) {
         int p;
         for (p = 0; p < extraPids->numPids; p++) {
            found_key = parseDRM(drm, book->drmCount, extraPids->pidList[p], 8);
            if (found_key) break;
         }
      }
      if (found_key == NULL) {
         fprintf(stderr, "No valid pids available, failed to find DRM key\n");
         freeMobiFile(book);
         return 0;
      }
   }
   fprintf(stderr, "Found a DRM key!\n");

   out = fopen(outFile, "wb");
   if (out == NULL) {
      fprintf(stderr, "Failed to open output file, quitting\n");
      freeMobiFile(book);
      free(found_key);
      return 0;
   }

   result = writeMobiOutputFile(book, out, found_key, drmOffset, drm_len);

   fclose(out);
   if (result == 0) {
      _unlink(outFile);
   }
   freeMobiFile(book);
   free(found_key);
   return result;
}

enum {
   FileTypeUnk,
   FileTypeMobi,
   FileTypeTopaz
};

int getFileType(FILE *in) {
   PDB p;
   int type = FileTypeUnk;
   fseek(in, 0, SEEK_SET);
   fread(&p, sizeof(p), 1, in);
   if (p.type == 0x4b4f4f42 && p.creator == 0x49424f4d) {
      type = FileTypeMobi;
   }
   else if (strncmp(p.name, "TPZ0", 4) == 0) {
      type = FileTypeTopaz;
   }
   fseek(in, 0, SEEK_SET);
   return type;
}

void usage() {
   fprintf(stderr, "usage: ./skindle [-d] [-v] -i <ebook file> -o <output file> [-k kindle.info file] [-p pid]\n");
   fprintf(stderr, "    -d optional, for topaz files only, produce a decompressed output file\n");
   fprintf(stderr, "    -i required name of the input mobi or topaz file\n");
   fprintf(stderr, "    -o required name of the output file to generate\n");
   fprintf(stderr, "    -k optional kindle.info path\n");   
   fprintf(stderr, "    -v dump the contents of kindle.info\n");   
   fprintf(stderr, "    -p additional PID values to attempt (can specifiy multiple times)\n");   
}

extern char *optarg;
extern int optind;

int main(int argc, char **argv) {
   //had to pile all these up here to please VS2009
   FILE *in;
   int type, explode = 0;
   int result = 0;
   int firstArg = 1;
   int opt;
   PidList *pids = NULL;
   char *infile = NULL, *outfile = NULL, *kinfo = NULL;
   int dump = 0;
   
   while ((opt = getopt(argc, argv, "vdp:i:o:k:")) != -1) {
      switch (opt) {
         case 'v':
            dump = 1;
            break;
         case 'd':
            explode = 1;
            break;
         case 'p': {
            int l = strlen(optarg);
            if (l == 10) {
               if (!verifyPidChecksum(optarg)) {
                  fprintf(stderr, "Invalid pid %s, skipping\n", optarg);
                  break;
               }
               optarg[8] = 0;
            }
            else if (l != 8) {
               fprintf(stderr, "Invalid pid length for %s, skipping\n", optarg);
               break;
            }
            if (pids == NULL) {
               pids = (PidList*)malloc(sizeof(PidList));
               pids->numPids = 1;
               pids->pidList[0] = optarg;
            }
            else {
               pids = (PidList*)realloc(pids, sizeof(PidList) + pids->numPids * sizeof(unsigned char*));
               pids->pidList[pids->numPids++] = optarg;
            }
            break;
         }
         case 'k':
            kinfo = optarg;
            break;
         case 'i':
            infile = optarg;
            break;
         case 'o':
            outfile = optarg;
            break;
         default: /* '?' */
            usage();
            exit(1);
      }
   }

   if (optind != argc) {
      fprintf(stderr, "Extra options ignored\n");
   }

   if (!buildKindleMap(kinfo)) {
      fprintf(stderr, "buildKindleMap failed\n");
      usage();
      exit(1);
   }

   //The following loop dumps the contents of your kindle.info file
   if (dump) {
      MapList *ml;
//     dumpKindleMap();
      fprintf(stderr, "\nDumping kindle.info contents:\n");
      for (ml = kindleMap; ml; ml = ml->next) {
         DATA_BLOB DataIn;
         DATA_BLOB DataOut;
         DataIn.pbData = mazamaDecode(ml->value, (int*)&DataIn.cbData);
         if (CryptUnprotectData(&DataIn, NULL, NULL, NULL, NULL, 1, &DataOut)) {
            fprintf(stderr, "%s ==> %s\n", ml->key, translateKindleKey(ml->key));
            fwrite(DataOut.pbData, DataOut.cbData, 1, stderr);
            fprintf(stderr, "\n\n");
            LocalFree(DataOut.pbData);
         }
         else {
            fprintf(stderr, "CryptUnprotectData failed\n");
         }
         free(DataIn.pbData);
      }
   }

   if (infile == NULL && outfile == NULL) {
      //special case, user just wants to see kindle.info
      freeMap(kindleMap);
      exit(1);
   }

   if (infile == NULL) {
      fprintf(stderr, "Missing input file name\n");
      usage();
      freeMap(kindleMap);
      exit(1);
   }

   if (outfile == NULL) {
      fprintf(stderr, "Missing output file name\n");
      usage();
      freeMap(kindleMap);
      exit(1);
   }
   
   in = fopen(infile, "rb");
   if (in == NULL) {
      fprintf(stderr, "%s bad open, quitting\n", infile);
      freeMap(kindleMap);
      exit(1);
   }

   type = getFileType(in);
   if (type == FileTypeTopaz) {
      result = processTopaz(in, outfile, explode, pids);
   }
   else if (type == FileTypeMobi) {
      result = processMobi(in, outfile, pids);
   }
   else {
      fprintf(stderr, "%s file type unknown, quitting\n", infile);
      fclose(in);
      freeMap(kindleMap);
      exit(1);
   }

   fclose(in);
   if (result) {
      fprintf(stderr, "Success! Enjoy!\n");
   }
   else {
      fprintf(stderr, "An error occurred, unable to process input file!\n");
   }
   
   freeMap(kindleMap);
   return 0;
}
