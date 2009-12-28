
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

#include <windows.h>
#include <Wincrypt.h>

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/stat.h>

//If you prefer to use openssl uncomment the following
//#include <openssl/sha.h>
//#include <openssl/md5.h>

//If you prefer to use openssl remove the following 2 line
#include "md5.h"
#include "sha1.h"

unsigned int base64(unsigned char *inbuf, unsigned int len, unsigned char *outbuf);

/* The kindle.info file created when you install KindleForPC is a set
 * of key:value pairs delimited by '{'.  The keys and values are encoded
 * in a variety of ways.  Keys are the mazama64 encoded md5 hash of the
 * key name, while values are the mazama64 encoding of the blob returned
 * by the Windows CryptProtectData function.  The use of CryptProtectData
 * is what locks things to a particular user/machine

 * kindle.info layout

 * Key:AbaZZ6z4a7ZxzLzkZcaqauZMZjZ_Ztz6   ("kindle.account.tokens")
 * Value: mazama64Encode(CryptProtectData(some sha1 hash))

 * Key:AsAWa4ZJAQaCZ7A3zrZSaZavZMarZFAw  ("kindle.cookie.item")
 * Value: mazama64Encode(CryptProtectData(base64(144 bytes of data)))

 * Key:ZHatAla4a-zTzWA-AvaeAvZQzKZ-agAz   ("eulaVersionAccepted")
 * Value: mazama64Encode(CryptProtectData(kindle version?))

 * Key:ZiajZga7Z9zjZRz7AfZ-zRzUANZNZJzP   ("login_date")
 * Value: mazama64Encode(CryptProtectData(registration date))

 * Key:ZkzeAUA-Z2ZYA2Z_ayA_ahZEATaEAOaG  ("kindle.token.item")
 * Value: mazama64Encode(CryptProtectData(multi-field crypto data))
 * {enc:xxx}{iv:xxx}{key:xxx}{name:xxx}{serial:xxx}
 * enc:base64(binary blob)
 * iv:base64(16 bytes)
 * key:base64(256 bytes)
 * name:base64("ADPTokenEncryptionKey")
 * serial:base64("1")

 * Key:aVzrzRAFZ7aIzmASZOzVzIAGAKawzwaU    ("login")
 * Value: mazama64Encode(CryptProtectData(your amazon email))

 * Key:avalzbzkAcAPAQA5ApZgaOZPzQZzaiaO   mazama64Encode(md5("MazamaRandomNumber"))
 * Value: mazama64Encode(CryptProtectData(mazama32Encode(32 bytes random data)))

 * Key:zgACzqAjZ2zzAmAJa6ZFaZALaYAlZrz-   ("kindle.key.item")
 * Value: mazama64Encode(CryptProtectData(RSA private key)) no password

 * Key:zga-aIANZPzbzfZ1zHZWZcA4afZMZcA_   ("kindle.name.info")
 * Value: mazama64Encode(CryptProtectData(your name))

 * Key:zlZ9afz1AfAVZjacaqa-ZHa1aIa_ajz7   ("kindle.device.info");
 * Value: mazama64Encode(CryptProtectData(the name of your kindle))
*/

typedef struct _SimpleMapNode {
   char *key;
   char *value;
} SimpleMapNode;

typedef struct _MapList {
   SimpleMapNode *node;
   struct _MapList *next;
} MapList;

MapList *kindleMap;

#pragma pack(2)
typedef struct _PDB {
   char name[32];
   unsigned short attrib;
   unsigned short version;
   unsigned int created;
   unsigned int modified;
   unsigned int backup;
   unsigned int modNum;
   unsigned int appInfoID;
   unsigned int sortInfoID;
   unsigned int type;
   unsigned int creator;
   unsigned int uniqueIDseed;
   unsigned int nextRecordListID;
   unsigned short numRecs;
} PDB;

typedef struct _HeaderRec {
   unsigned int offset;
   unsigned int attribId;
} HeaderRec;

#define attrib(x) ((x)&0xFF)
#define id(x) (bswap_l((x) & 0xFFFFFF00))

typedef struct _PalmDocHeader {
   unsigned short compression;
   unsigned short reserverd1;
   unsigned int textLength;
   unsigned short recordCount;
   unsigned short recordSize;
   unsigned short encryptionType;
   unsigned short reserved2;
} PalmDocHeader;


//checked lengths are 24, 116, 208, 228
typedef struct _MobiHeader {
   unsigned int id;
   unsigned int hdrLen;
   unsigned int type;
   unsigned int encoding;
   unsigned int uniqueId;
   unsigned int generator;
   unsigned char reserved1[40];
   unsigned int firstNonBookIdx;
   unsigned int nameOffset;
   unsigned int nameLength;
   unsigned int language;
   unsigned int inputLang;
   unsigned int outputLang;
   unsigned int formatVersion;
   unsigned int firstImageIdx;
   unsigned char unknown1[16];
   unsigned int exthFlags;
   unsigned char unknown2[36];
   unsigned int drmOffset;
   unsigned int drmCount;
   unsigned int drmSize;
   unsigned int drmFlags;
   unsigned char unknown3[58];
   unsigned short extra_flags;
} MobiHeader;

typedef struct _ExthRecHeader {
   unsigned int type;
   unsigned int len;
} ExthRecHeader;

typedef struct _ExthHeader {
   unsigned int id;
   unsigned int hdrLen;
   unsigned int recordCount;
   ExthRecHeader records[1];
} ExthHeader;


//#define bswap_l ntohl
//#define bswap_s ntohs

unsigned short bswap_s(unsigned short s) {
   return (s >> 8) | (s << 8);
}

unsigned int bswap_l(unsigned int s) {
   unsigned int u = bswap_s(s);
   unsigned int l = bswap_s(s >> 16);
   return (u << 16) | l;
}

MapList *findNode(char *key) {
   MapList *l;
   for (l = kindleMap; l; l = l->next) {
      if (strcmp(key, l->node->key) == 0) {
         return l;
      }
   }
   return NULL;
}

void addMapNode(char *key, char *value) {
   MapList *ml = findNode(key);
   if (ml) {
      free(ml->node->value);
      ml->node->value = value;
   }
   else {
      SimpleMapNode *smn = (SimpleMapNode*)malloc(sizeof(SimpleMapNode));
      smn->key = key;
      smn->value = value;
      ml = (MapList*)malloc(sizeof(MapList));
      ml->node = smn;
      ml->next = kindleMap;
      kindleMap = ml;
   }
}

void dumpMap() {
   MapList *l;
   for (l = kindleMap; l; l = l->next) {
      fprintf(stderr, "%s:%s\n", l->node->key, l->node->value);
   }
}

void parseLine(char *line) {
   char *colon = strchr(line, ':');
   if (colon) {
      char *key, *value;
      int len = colon - line;
      key = (char*)malloc(len + 1);
      *colon++ = 0;
      strcpy(key, line);
      len = strlen(colon);
      value = (char*)malloc(len + 1);
      strcpy(value, colon);
      value[len] = 0;
      addMapNode(key, value);
   }
}

int buildKindleMap(char *infoFile) {
   int result = 0;
   struct stat statbuf;
   if (stat(infoFile, &statbuf) == 0) {
      FILE *fd = fopen(infoFile, "rb");
      char *infoBuf = (char*)malloc(statbuf.st_size + 1);
      infoBuf[statbuf.st_size] = 0;
      if (fread(infoBuf, statbuf.st_size, 1, fd) == 1) {
         char *end = infoBuf + statbuf.st_size;
         char *b = infoBuf, *e;
         while (e = strchr(b, '{')) {
            *e = 0;
            if ((e - b) > 2) {
               parseLine(b);
            }
            e++;
            b = e;
         }
         if (b < end) {
            parseLine(b);
         }
      }
      else {
         fprintf(stderr, "short read on info file\n");
      }
      free(infoBuf);
      fclose(fd);
      return 1;
   }
   return 0;
}

png_crc_table_init(unsigned int *crc_table) {
   unsigned int i;
   for (i = 0; i < 256; i++) {
      unsigned int n = i;
      unsigned int j;
      for (j = 0; j < 8; j++) {
         if (n & 1) {
            n = 0xEDB88320 ^ (n >> 1);
         }
         else {
            n >>= 1;
         }
      }
      crc_table[i] = n;
   }
}

unsigned int compute_png_crc(unsigned char *input, unsigned int len, unsigned int *crc_table) {
   unsigned int crc = 0;
   unsigned int i;
   for (i = 0; i < len; i++) {
      unsigned int v = (input[i] ^ crc) & 0xff;
      crc = crc_table[v] ^ (crc >> 8);
   }
   return crc;
}

char *decodeString = "ABCDEFGHIJKLMNPQRSTUVWXYZ123456789";

void doPngDecode(unsigned char *input, unsigned int len, unsigned char *output) {
   unsigned int crc_table[256];
   unsigned int crc, i, x = 0;
   unsigned int *out = (unsigned int*)output;
   png_crc_table_init(crc_table);
   crc = bswap_l(compute_png_crc(input, len, crc_table));
   memset(output, 0, 8);
   for (i = 0; i < len; i++) {
      output[x++] ^= input[i];
      if (x == 8) x = 0;
   }
   out[0] ^= crc;
   out[1] ^= crc;
   for (i = 0; i < 8; i++) {
      unsigned char v = output[i];
      output[i] = decodeString[((((v >> 5) & 3) ^ v) & 0x1F) + (v >> 7)];
   }
}

char *string_20 = "n5Pr6St7Uv8Wx9YzAb0Cd1Ef2Gh3Jk4M";
char *string_40 = "AaZzB0bYyCc1XxDdW2wEeVv3FfUuG4g-TtHh5SsIiR6rJjQq7KkPpL8lOoMm9Nn_";

char *mazamaEncode(unsigned char *input, unsigned int len, unsigned char choice) {
   unsigned int i;
   char *enc, *out;
   if (choice == 0x20) enc = string_20;
   else if (choice == 0x40) enc = string_40;
   else return NULL;
   out = (char*)malloc(len * 2 + 1);
   out[len * 2] = 0;
   for (i = 0; i < len; i++) {
      unsigned char v = input[i] + 128;
      unsigned char q = v / choice;
      unsigned char m = v % choice;
      out[i * 2] = enc[q];
      out[i * 2 + 1] = enc[m];
   }
   return out;
}

unsigned char *mazamaDecode(char *input, int *outlen) {
   unsigned char *out;
   int len = strlen(input);
   char *dec = NULL;
   int i, choice = 0x20;
   *outlen = 0;
   for (i = 0; i < 8 && i < len; i++) {
      if (*input == string_20[i]) {
         dec = string_20;
         break;
      }
   }
   if (dec == NULL) {
      for (i = 0; i < 4 && i < len; i++) {
         if (*input == string_40[i]) {
            dec = string_40;
            choice = 0x40;
            break;
         }
      }
   }
   if (dec == NULL) {
      return NULL;
   }
   out = (unsigned char*)malloc(len / 2 + 1);
   out[len / 2] = 0;
   for (i = 0; i < len; i += 2) {
      int q, m, v;
      char *p = strchr(dec, input[i]);
      if (p == NULL) break;
      q = p - dec;
      p = strchr(dec, input[i + 1]);
      if (p == NULL) break;
      m = p - dec;
      v = (choice * q + m) - 128;
      out[(*outlen)++] = (unsigned char)v;
   }
   return out;
}

unsigned char *getExthData(ExthHeader *eh, unsigned int type, unsigned int *len) {
   unsigned int i;
   unsigned int exthRecords = bswap_l(eh->recordCount);
   ExthRecHeader *erh = eh->records;

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

typedef struct _vstruct {
   unsigned int verification;
   unsigned int size;
   unsigned int type;
   unsigned char cksum[4];
   unsigned char cookie[32];
} vstruct;

typedef struct _kstruct {
   unsigned int ver;
   unsigned int flags;
   unsigned char finalkey[16];
   unsigned int expiry;
   unsigned int expiry2;
} kstruct;

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

#ifndef HEADER_MD5_H

#define MD5_DIGEST_LENGTH 16

#define MD5_CTX md5_state_t
#define MD5_Init md5_init
#define MD5_Update md5_append
#define MD5_Final(x, y) md5_finish(y, x)
#define MD5 md5

void md5(unsigned char *in, int len, unsigned char *md) {
   MD5_CTX s;
   MD5_Init(&s);
	MD5_Update(&s, in, len);
	MD5_Final(md, &s);
}
#endif

#ifndef HEADER_SHA_H

#define SHA_DIGEST_LENGTH 20
#define SHA_CTX sha1_state_s
#define SHA1_Init sha1_init
#define SHA1_Update sha1_update
#define SHA1_Final(x, y) sha1_finish(y, x)
#define SHA1 sha1

void sha1(unsigned char *in, int len, unsigned char *md) {
   SHA_CTX s;
   SHA1_Init(&s);
	SHA1_Update(&s, in, len);
	SHA1_Final(md, &s);
}
#endif

int main(int argc, char **argv) {
   //had to pile all these up here to please VS2009
   PDB header;
   struct stat statbuf;
   FILE *prc, *out;
   HeaderRec *hr;
   PalmDocHeader *pdh;
   MobiHeader *mobi;
   ExthHeader *exth;
   long record0_offset;
   unsigned int record0_size, mobiLen, extra_data_flags;
   unsigned int recs, i, drmCount, len209;
   unsigned char *record0, *d209;
   unsigned char *vsn, *username, *mrn_key, *kat_key;
   char drive[256];
   char name[256];
   DWORD nlen = sizeof(name);
   char *d;
   char volumeName[256];
   DWORD volumeSerialNumber;
   char fileSystemNameBuffer[256];
   char volumeID[32];
   unsigned char md5sum[MD5_DIGEST_LENGTH];
   unsigned char sha1sum[SHA_DIGEST_LENGTH];
   unsigned char pid_base64[SHA_DIGEST_LENGTH * 2];
   unsigned int outl;
   SHA_CTX sha1_ctx;
   MapList *ml;
   unsigned int drmOffset, drm_len;
   unsigned char *drm, *found_key;
      
   if (argc != 4) {
      fprintf(stderr, "usage: %s\n <prc file> <output file> <kindle.info file>", argv[0]);
      exit(1);
   }

   if (stat(argv[1], &statbuf) != 0) {
      fprintf(stderr, "Unable to stat %s, quitting\n", argv[1]);
      exit(1);
   }

   prc = fopen(argv[1], "rb");
   if (prc == NULL) {
      fprintf(stderr, "%s bad open, quitting\n", argv[1]);
      exit(1);
   }

   if (fread(&header, sizeof(header), 1, prc) != 1) {
      fprintf(stderr, "%s bad header read, quitting\n", argv[1]);
      fclose(prc);
      exit(1);
   }

   //do BOOKMOBI check
   if (header.type != 0x4b4f4f42 || header.creator != 0x49424f4d) {
      fprintf(stderr, "Invalid header type or creator, quitting\n");
      fclose(prc);
      exit(1);
   }

   if (!buildKindleMap(argv[3])) {
      fprintf(stderr, "buildMap failed\n");
      fclose(prc);
      exit(1);
   }

   recs = bswap_s(header.numRecs);

   hr = (HeaderRec*)malloc(recs * sizeof(HeaderRec));
   if (fread(hr, sizeof(HeaderRec), recs, prc) != recs) {
      fprintf(stderr, "Failed read of header record, quitting\n");
      fclose(prc);
      exit(1);
   }

   record0_offset = bswap_l(hr[0].offset);
   record0_size = bswap_l(hr[1].offset) - record0_offset;

   if (fseek(prc, record0_offset, SEEK_SET) == -1) {
      fprintf(stderr, "bad seek to header record offset, quitting\n");
      fclose(prc);
      exit(1);
   }

   record0 = (unsigned char*)malloc(record0_size);

   if (fread(record0, record0_size, 1, prc) != 1) {
      fprintf(stderr, "bad read of record0, quitting\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   pdh = (PalmDocHeader*)record0;
   if (bswap_s(pdh->encryptionType) != 2) {
      fprintf(stderr, "MOBI BOOK is not encrypted, quitting\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   mobi = (MobiHeader*)(pdh + 1);
   if (mobi->id != 0x49424f4d) {
      fprintf(stderr, "MOBI header not found, quitting\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   mobiLen = bswap_l(mobi->hdrLen);
   extra_data_flags = 0;
   
   if (mobiLen >= 0xe4) {
      extra_data_flags = bswap_s(mobi->extra_flags);
   }

   if ((bswap_l(mobi->exthFlags) & 0x40) == 0) {
      fprintf(stderr, "Missing exth header, quitting\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   exth = (ExthHeader*)(mobiLen + (char*)mobi);
   if (exth->id != 0x48545845) {
      fprintf(stderr, "EXTH header not found\n");
      free(record0);
      fclose(prc);
      exit(1);
   }
  
   //if you want a list of EXTH records, uncomment the following
//   enumExthRecords(exth);

   drmCount = bswap_l(mobi->drmCount);

   if (drmCount == 0) {
      fprintf(stderr, "no PIDs found in this file, quitting\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   if (GetUserName(name, &nlen) == 0) {
      fprintf(stderr, "GetUserName failed, quitting\n");
      fclose(prc);
      exit(1);
   }
   fprintf(stderr, "Using UserName = \"%s\"\n", name);

   d = getenv("SystemDrive");
   if (d) {
      strcpy(drive, d);
      strcat(drive, "\\");
   }
   else {
      strcpy(drive, "c:\\");
   }
   fprintf(stderr, "Using SystemDrive = \"%s\"\n", drive);
   if (GetVolumeInformation(drive, volumeName, sizeof(volumeName), &volumeSerialNumber,
                        NULL, NULL, fileSystemNameBuffer, sizeof(fileSystemNameBuffer))) {
      sprintf(volumeID, "%u", volumeSerialNumber);
   }
   else {
      strcpy(volumeID, "9999999999");
   }
   fprintf(stderr, "Using VolumeSerialNumber = \"%s\"\n", volumeID);
   MD5(volumeID, strlen(volumeID), md5sum);
   vsn = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x20);

   MD5(name, strlen(name), md5sum);
   username = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x20);

   MD5("MazamaRandomNumber", 18, md5sum);
   mrn_key = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x40);

   MD5("kindle.account.tokens", 21, md5sum);
   kat_key = mazamaEncode(md5sum, MD5_DIGEST_LENGTH, 0x40);

   SHA1_Init(&sha1_ctx);

   ml = findNode(mrn_key);
   if (ml) {
      DATA_BLOB DataIn;
      DATA_BLOB DataOut;
      DataIn.pbData = mazamaDecode(ml->node->value, (int*)&DataIn.cbData);
      if (CryptUnprotectData(&DataIn, NULL, NULL, NULL, NULL, 1, &DataOut)) {
         char *devId = (char*)malloc(DataOut.cbData + 2 * MD5_DIGEST_LENGTH + 1);
         char *finalDevId;
         unsigned char pidbuf[10];
         
//         fprintf(stderr, "CryptUnprotectData success\n");
//         fwrite(DataOut.pbData, DataOut.cbData, 1, stderr);
//         fprintf(stderr, "\n");

         memcpy(devId, DataOut.pbData, DataOut.cbData);
         strcpy(devId + DataOut.cbData, vsn);
         strcat(devId + DataOut.cbData, username);

//         fprintf(stderr, "Computing sha1 over %d bytes\n", DataOut.cbData + 4 * MD5_DIGEST_LENGTH);
         sha1(devId, DataOut.cbData + 4 * MD5_DIGEST_LENGTH, sha1sum);
         finalDevId = mazamaEncode(sha1sum, SHA_DIGEST_LENGTH, 0x20);
//         fprintf(stderr, "finalDevId: %s\n", finalDevId);

         SHA1_Update(&sha1_ctx, finalDevId, strlen(finalDevId));

         pidbuf[8] = 0;
         doPngDecode(finalDevId, 4, (unsigned char*)pidbuf);
//         fprintf(stderr, "Device PID: %s\n", pidbuf);

         LocalFree(DataOut.pbData);
         free(devId);
         free(finalDevId);
      }
      else {
         fprintf(stderr, "CryptUnprotectData failed, quitting\n");
         free(record0);
         fclose(prc);
         exit(1);
      }

      free(DataIn.pbData);
   }

   ml = findNode(kat_key);
   if (ml) {
      DATA_BLOB DataIn;
      DATA_BLOB DataOut;
      DataIn.pbData = mazamaDecode(ml->node->value, (int*)&DataIn.cbData);
      if (CryptUnprotectData(&DataIn, NULL, NULL, NULL, NULL, 1, &DataOut)) {
//         fprintf(stderr, "CryptUnprotectData success\n");
//         fwrite(DataOut.pbData, DataOut.cbData, 1, stderr);
//         fprintf(stderr, "\n");

         SHA1_Update(&sha1_ctx, DataOut.pbData, DataOut.cbData);

         LocalFree(DataOut.pbData);
      }
      else {
         fprintf(stderr, "CryptUnprotectData failed, quitting\n");
         fclose(prc);
         free(record0);
         exit(1);
      }

      free(DataIn.pbData);
   }

   d209 = getExthData(exth, 209, &len209);

   if (d209 != NULL) {
      unsigned char *rec;
      unsigned int idx;
      SHA1_Update(&sha1_ctx, d209, len209);
      for (idx = 0; idx < len209; idx += 5) {
         unsigned int dlen;
         unsigned int rtype = bswap_l(*(unsigned int*)(d209 + idx + 1));
         rec = getExthData(exth, rtype, &dlen);
         if (rec != NULL) {
//            fprintf(stderr, "exth %d: %s\n", rtype, rec);
            SHA1_Update(&sha1_ctx, rec, dlen);
         }
      }
   }

   SHA1_Final(sha1sum, &sha1_ctx);

   outl = base64(sha1sum, SHA_DIGEST_LENGTH, pid_base64);

   pid_base64[8] = 0;
   fprintf(stderr, "PID for %s is: %s\n", header.name, pid_base64);

/*
   unique pid is computed as:
   base64(sha1(idArray . kindleToken . 209_data . 209_tokens))
*/

   free(mrn_key);
   free(kat_key);
   free(vsn);
   free(username);

   drmOffset = bswap_l(mobi->drmOffset);

   drm_len = bswap_l(mobi->drmSize);
   drm = record0 + drmOffset;

   found_key = parseDRM(drm, drmCount, pid_base64, 8);
   if (found_key) {
      fprintf(stderr, "Found a DRM key!\n");
   }
   else {
      fprintf(stderr, "Failed to find DRM key\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   // kill the drm keys
   memset(record0 + drmOffset, 0, drm_len);
   // kill the drm pointers
   mobi->drmOffset = 0xffffffff;
   mobi->drmCount = mobi->drmSize = mobi->drmFlags = 0;
   // clear the crypto type
   pdh->encryptionType = 0;

   out = fopen(argv[2], "wb");
   if (out == NULL) {
      fprintf(stderr, "Failed to open output file, quitting\n");
      free(record0);
      fclose(prc);
      exit(1);
   }

   fwrite(&header, sizeof(header), 1, out);
   fwrite(hr, sizeof(HeaderRec), recs, out);
   fwrite("\x00\x00", 1, 2, out);
   fwrite(record0, record0_size, 1, out);

   //need to zero out exth 209 data
   for (i = 1; i < recs; i++) {
      unsigned int offset = bswap_l(hr[i].offset);
      unsigned int len, extra_size;
      unsigned char *rec;
      if (i == (recs - 1)) {  //last record extends to end of file
         len = statbuf.st_size - offset;
      }
      else {
         len = bswap_l(hr[i + 1].offset) - offset;
      }
      //make sure we are at proper offset
      while (ftell(out) < offset) {
         fwrite("\x00", 1, 1, out);
      }
      rec = (unsigned char *)malloc(len);
      if (fseek(prc, offset, SEEK_SET) != 0) {
         fprintf(stderr, "Failed record seek on input, quitting\n");
         free(record0);
         free(rec);
         fclose(prc);
         fclose(out);
         _unlink(argv[2]);
         exit(1);
      }
      if (fread(rec, len, 1, prc) != 1) {
         fprintf(stderr, "Failed record read on input, quitting\n");
         free(record0);
         free(rec);
         fclose(prc);
         fclose(out);
         _unlink(argv[2]);
         exit(1);
      }

      extra_size = getSizeOfTrailingDataEntries(rec, len, extra_data_flags);
      PC1(found_key, 16, rec, rec, len - extra_size, 1);
      fwrite(rec, len, 1, out);
      free(rec);
   }
   fprintf(stderr, "Done! Enjoy!\n");

/*
   //The following loop dumps the contents of your kindle.info file
   for (ml = kindleMap; ml; ml = ml->next) {
      DATA_BLOB DataIn;
      DATA_BLOB DataOut;
      DataIn.pbData = mazamaDecode(ml->node->value, (int*)&DataIn.cbData);
      if (CryptUnprotectData(&DataIn, NULL, NULL, NULL, NULL, 1, &DataOut)) {
         fprintf(stderr, "CryptUnprotectData success for key: %s\n", ml->node->key);
         fwrite(DataOut.pbData, DataOut.cbData, 1, stderr);
         fprintf(stderr, "\n");
         LocalFree(DataOut.pbData);
      }
      else {
         fprintf(stderr, "CryptUnprotectData failed\n");
      }
      free(DataIn.pbData);
   }
*/

   fclose(prc);
   fclose(out);
   free(record0);
   return 0;
}
