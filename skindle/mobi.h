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

#ifndef __MOBI_H
#define __MOBI_H

#include <stdio.h>
#include "skinutils.h"

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

typedef struct _MobiFile {
   FILE *f;
   PDB pdb;
   HeaderRec *hr;
   PalmDocHeader *pdh;
   MobiHeader *mobi;
   ExthHeader *exth; 
   unsigned char *record0; 
   unsigned int record0_offset;
   unsigned int record0_size;
   unsigned int mobiLen;
   unsigned int extra_data_flags;
   unsigned int recs;
   unsigned int drmCount;
   unsigned int textRecs;
   PidList *pids;    //extra pids to try from command line
} MobiFile;

unsigned char *getExthData(MobiFile *book, unsigned int type, unsigned int *len);
void enumExthRecords(ExthHeader *eh);
unsigned char *PC1(unsigned char *key, unsigned int klen, unsigned char *src,
                   unsigned char *dest, unsigned int len, int decryption);
unsigned int getSizeOfTrailingDataEntry(unsigned char *ptr, unsigned int size);
unsigned int getSizeOfTrailingDataEntries(unsigned char *ptr, unsigned int size, unsigned int flags);
unsigned char *parseDRM(unsigned char *data, unsigned int count, unsigned char *pid, unsigned int pidlen);

void freeMobiFile(MobiFile *book);
MobiFile *parseMobiHeader(FILE *f);
int writeMobiOutputFile(MobiFile *book, FILE *out, unsigned char *key, 
                        unsigned int drmOffset, unsigned int drm_len);

#endif
