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

#ifndef __SKINUTILS_H
#define __SKINUTILS_H

typedef struct _PidList {
   unsigned int numPids;
   char *pidList[1];  //extra pids to try from command line
} PidList;

typedef struct _MapList {
   char *key;
   char *value;
   struct _MapList *next;
} MapList;

extern MapList *kindleMap;

unsigned int base64(unsigned char *inbuf, unsigned int len, unsigned char *outbuf);

unsigned short bswap_s(unsigned short s);
unsigned int bswap_l(unsigned int s);

char *translateKindleKey(char *key);
MapList *findNode(MapList *map, char *key);
MapList *findKindleNode(char *key);

//don't free the result of getNodeValue;
char *getNodeValue(MapList *map, char *key);
char *getKindleValue(char *key);

MapList *addMapNode(MapList *map, char *key, char *value);
void dumpMap(MapList *m);

void freeMap(MapList *m);

int buildKindleMap(char *infoFile);
void dumpKindleMap();

//void png_crc_table_init(unsigned int *crc_table);
unsigned int do_crc(unsigned char *input, unsigned int len);
void doPngDecode(unsigned char *input, unsigned int len, unsigned char *output);

char *mazamaEncode(unsigned char *input, unsigned int len, unsigned char choice);
char *mazamaEncode32(unsigned char *input, unsigned int len);
char *mazamaEncode64(unsigned char *input, unsigned int len);

unsigned char *mazamaDecode(char *input, int *outlen);

int verifyPidChecksum(char *pid);

//If you prefer to use openssl uncomment the following
//#include <openssl/sha.h>
//#include <openssl/md5.h>

#ifndef HEADER_MD5_H
#include "md5.h"

#define MD5_DIGEST_LENGTH 16

#define MD5_CTX md5_state_t
#define MD5_Init md5_init
#define MD5_Update md5_append
#define MD5_Final(x, y) md5_finish(y, x)
#define MD5 md5

void md5(unsigned char *in, int len, unsigned char *md);
#endif

#ifndef HEADER_SHA_H

#include "sha1.h"

#define SHA_DIGEST_LENGTH 20
#define SHA_CTX sha1_state_s
#define SHA1_Init sha1_init
#define SHA1_Update sha1_update
#define SHA1_Final(x, y) sha1_finish(y, x)
#define SHA1 sha1

void sha1(unsigned char *in, int len, unsigned char *md);
#endif

char *getBookPid(unsigned char *keys, unsigned int klen, unsigned char *keysValue, unsigned int kvlen);

#endif
