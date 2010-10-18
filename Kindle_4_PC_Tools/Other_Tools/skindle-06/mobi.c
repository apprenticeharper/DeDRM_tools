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

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>

#include "mobi.h"

unsigned char *getExthData(MobiFile *book, unsigned int type, unsigned int *len) {
   unsigned int i;
   unsigned int exthRecords = bswap_l(book->exth->recordCount);
   ExthRecHeader *erh = book->exth->records;

   *len = 0;

   for (i = 0; i < exthRecords; i++) {
      unsigned int recType = bswap_l(erh->type);
      unsigned int recLen = bswap_l(erh->len);

      if (recLen < 8) {
         fprintf(stderr, "Invalid exth record length %d\n", i);
         return NULL;
      }

      if (recType == type) {
         *len = recLen - 8;
         return (unsigned char*)(erh + 1);
      }
      erh = (ExthRecHeader*)(recLen  + (char*)erh);
   }
   return NULL;
}

void enumExthRecords(ExthHeader *eh) {
   unsigned int exthRecords = bswap_l(eh->recordCount);
   unsigned int i;
   unsigned char *data;
   ExthRecHeader *erh = eh->records;

   for (i = 0; i < exthRecords; i++) {
      unsigned int recType = bswap_l(erh->type);
      unsigned int recLen = bswap_l(erh->len);

      fprintf(stderr, "%d: type - %d, len %d\n", i, recType, recLen);

      if (recLen < 8) {
         fprintf(stderr, "Invalid exth record length %d\n", i);
         return;
      }

      data = (unsigned char*)(erh + 1);
      switch (recType) {
         case 1: //drm_server_id
            fprintf(stderr, "drm_server_id: %s\n", data);
            break;
         case 2: //drm_commerce_id
            fprintf(stderr, "drm_commerce_id: %s\n", data);
            break;
         case 3: //drm_ebookbase_book_id
            fprintf(stderr, "drm_ebookbase_book_id: %s\n", data);
            break;
         case 100: //author
            fprintf(stderr, "author: %s\n", data);
            break;
         case 101: //publisher
            fprintf(stderr, "publisher: %s\n", data);
            break;
         case 106: //publishingdate
            fprintf(stderr, "publishingdate: %s\n", data);
            break;
         case 113: //asin
            fprintf(stderr, "asin: %s\n", data);
            break;
         case 208: //book unique drm key
            fprintf(stderr, "book drm key: %s\n", data);
            break;
         case 503: //updatedtitle
            fprintf(stderr, "updatedtitle: %s\n", data);
            break;
         default:
            break;
      }
      erh = (ExthRecHeader*)(recLen  + (char*)erh);
   }

}

//implementation of Pukall Cipher 1
unsigned char *PC1(unsigned char *key, unsigned int klen, unsigned char *src,
                   unsigned char *dest, unsigned int len, int decryption) {
    unsigned int sum1 = 0;
    unsigned int sum2 = 0;
    unsigned int keyXorVal = 0;
    unsigned short wkey[8];
    unsigned int i;
    if (klen != 16) {
        fprintf(stderr, "Bad key length!\n");
        return NULL;
    }
    for (i = 0; i < 8; i++) {
        wkey[i] = (key[i * 2] << 8) | key[i * 2 + 1];
    }
    for (i = 0; i < len; i++) {
        unsigned int temp1 = 0;
        unsigned int byteXorVal = 0;
        unsigned int j, curByte;
        for (j = 0; j < 8; j++) {
            temp1 ^= wkey[j];
            sum2 = (sum2 + j) * 20021 + sum1;
            sum1 = (temp1 * 346) & 0xFFFF;
            sum2 = (sum2 + sum1) & 0xFFFF;
            temp1 = (temp1 * 20021 + 1) & 0xFFFF;
            byteXorVal ^= temp1 ^ sum2;
        }
        curByte = src[i];
        if (!decryption) {
            keyXorVal = curByte * 257;
        }
        curByte = ((curByte ^ (byteXorVal >> 8)) ^ byteXorVal) & 0xFF;
        if (decryption) {
            keyXorVal = curByte * 257;
        }
        for (j = 0; j < 8; j++) {
            wkey[j] ^= keyXorVal;
        }
        dest[i] = curByte;
    }
    return dest;
}

unsigned int getSizeOfTrailingDataEntry(unsigned char *ptr, unsigned int size) {
   unsigned int bitpos = 0;
   unsigned int result = 0;
   if (size <= 0) {
      return result;
   }
   while (1) {
      unsigned int v = ptr[size - 1];
      result |= (v & 0x7F) << bitpos;
      bitpos += 7;
      size -= 1;
      if ((v & 0x80) != 0 || (bitpos >= 28) || (size == 0)) {
         return result;
      }
   }
}

unsigned int getSizeOfTrailingDataEntries(unsigned char *ptr, unsigned int size, unsigned int flags) {
   unsigned int num = 0;
   unsigned int testflags = flags >> 1;
   while (testflags) {
      if (testflags & 1) {
         num += getSizeOfTrailingDataEntry(ptr, size - num);
      }
      testflags >>= 1;
   }
   if (flags & 1) {
      num += (ptr[size - num - 1] & 0x3) + 1;
   }
   return num;
}

unsigned char *parseDRM(unsigned char *data, unsigned int count, unsigned char *pid, unsigned int pidlen) {
   unsigned int i;
   unsigned char temp_key_sum = 0;
   unsigned char *found_key = NULL;
   unsigned char *keyvec1 = "\x72\x38\x33\xB0\xB4\xF2\xE3\xCA\xDF\x09\x01\xD6\xE2\xE0\x3F\x96";
   unsigned char temp_key[16];

   memset(temp_key, 0, 16);
   memcpy(temp_key, pid, 8);
   PC1(keyvec1, 16, temp_key, temp_key, 16, 0);

   for (i = 0; i < 16; i++) {
      temp_key_sum += temp_key[i];
   }

   for (i = 0; i < count; i++) {
      unsigned char kk[32];
      vstruct *v = (vstruct*)(data + i * 0x30);
      kstruct *k = (kstruct*)PC1(temp_key, 16, v->cookie, kk, 32, 1);

      if (v->verification == k->ver && v->cksum[0] == temp_key_sum &&
          (bswap_l(k->flags) & 0x1F) == 1) {
         found_key = (unsigned char*)malloc(16);
         memcpy(found_key, k->finalkey, 16);
         break;
      }
   }
   return found_key;
}

void freeMobiFile(MobiFile *book) {
   free(book->hr);
   free(book->record0);
   free(book);
}

MobiFile *parseMobiHeader(FILE *f) {
   unsigned int numRecs, i, magic;
   MobiFile *book = (MobiFile*)calloc(sizeof(MobiFile), 1);
   book->f = f;
   if (fread(&book->pdb, sizeof(PDB), 1, f) != 1) {
      fprintf(stderr, "Failed to read Palm headers\n");
      free(book);
      return NULL;
   }

   //do BOOKMOBI check
   if (book->pdb.type != 0x4b4f4f42 || book->pdb.creator != 0x49424f4d) {
      fprintf(stderr, "Invalid header type or creator\n");
      free(book);
      return NULL;
   }

   book->recs = bswap_s(book->pdb.numRecs);

   book->hr = (HeaderRec*)malloc(book->recs * sizeof(HeaderRec));
   if (fread(book->hr, sizeof(HeaderRec), book->recs, f) != book->recs) {
      fprintf(stderr, "Failed read of header record\n");
      freeMobiFile(book);
      return NULL;
   }

   book->record0_offset = bswap_l(book->hr[0].offset);
   book->record0_size = bswap_l(book->hr[1].offset) - book->record0_offset;

   if (fseek(f, book->record0_offset, SEEK_SET) == -1) {
      fprintf(stderr, "bad seek to header record offset\n");
      freeMobiFile(book);
      return NULL;
   }

   book->record0 = (unsigned char*)malloc(book->record0_size);

   if (fread(book->record0, book->record0_size, 1, f) != 1) {
      fprintf(stderr, "bad read of record0\n");
      freeMobiFile(book);
      return NULL;
   }

   book->pdh = (PalmDocHeader*)(book->record0);
   if (bswap_s(book->pdh->encryptionType) != 2) {
      fprintf(stderr, "MOBI BOOK is not encrypted\n");
      freeMobiFile(book);
      return NULL;
   }

   book->textRecs = bswap_s(book->pdh->recordCount);

   book->mobi = (MobiHeader*)(book->pdh + 1);
   if (book->mobi->id != 0x49424f4d) {
      fprintf(stderr, "MOBI header not found\n");
      freeMobiFile(book);
      return NULL;
   }

   book->mobiLen = bswap_l(book->mobi->hdrLen);
   book->extra_data_flags = 0;
   
   if (book->mobiLen >= 0xe4) {
      book->extra_data_flags = bswap_s(book->mobi->extra_flags);
   }

   if ((bswap_l(book->mobi->exthFlags) & 0x40) == 0) {
      fprintf(stderr, "Missing exth header\n");
      freeMobiFile(book);
      return NULL;
   }

   book->exth = (ExthHeader*)(book->mobiLen + (char*)(book->mobi));
   if (book->exth->id != 0x48545845) {
      fprintf(stderr, "EXTH header not found\n");
      freeMobiFile(book);
      return NULL;
   }
  
   //if you want a list of EXTH records, uncomment the following
//   enumExthRecords(exth);

   book->drmCount = bswap_l(book->mobi->drmCount);

   if (book->drmCount == 0) {
      fprintf(stderr, "no PIDs found in this file\n");
      freeMobiFile(book);
      return NULL;
   }

   return book;
}

int writeMobiOutputFile(MobiFile *book, FILE *out, unsigned char *key, 
                        unsigned int drmOffset, unsigned int drm_len) {
   int i;
   struct stat statbuf;

   fstat(fileno(book->f), &statbuf);

   // kill the drm keys
   memset(book->record0 + drmOffset, 0, drm_len);
   // kill the drm pointers
   book->mobi->drmOffset = 0xffffffff;
   book->mobi->drmCount = book->mobi->drmSize = book->mobi->drmFlags = 0;
   // clear the crypto type
   book->pdh->encryptionType = 0;

   fwrite(&book->pdb, sizeof(PDB), 1, out);
   fwrite(book->hr, sizeof(HeaderRec), book->recs, out);
   fwrite("\x00\x00", 1, 2, out);
   fwrite(book->record0, book->record0_size, 1, out);

   //need to zero out exth 209 data
   for (i = 1; i < book->recs; i++) {
      unsigned int offset = bswap_l(book->hr[i].offset);
      unsigned int len, extra_size = 0;
      unsigned char *rec;
      if (i == (book->recs - 1)) {  //last record extends to end of file
         len = statbuf.st_size - offset;
      }
      else {
         len = bswap_l(book->hr[i + 1].offset) - offset;
      }
      //make sure we are at proper offset
      while (ftell(out) < offset) {
         fwrite("\x00", 1, 1, out);
      }
      rec = (unsigned char *)malloc(len);
      if (fseek(book->f, offset, SEEK_SET) != 0) {
         fprintf(stderr, "Failed record seek on input\n");
         freeMobiFile(book);
         free(rec);
         return 0;
      }
      if (fread(rec, len, 1, book->f) != 1) {
         fprintf(stderr, "Failed record read on input\n");
         freeMobiFile(book);
         free(rec);
         return 0;
      }

      if (i <= book->textRecs) { //decrypt if necessary
         extra_size = getSizeOfTrailingDataEntries(rec, len, book->extra_data_flags);
         PC1(key, 16, rec, rec, len - extra_size, 1);
      }
      fwrite(rec, len, 1, out);
      free(rec);
   }
   return 1;
}
