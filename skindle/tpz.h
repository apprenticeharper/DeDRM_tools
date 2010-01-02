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

#ifndef __TPZ_H
#define __TPZ_H

#include <stdio.h>
#include "skinutils.h"

typedef struct _TpzCtx {
   unsigned int v[2];
} TpzCtx;

void topazCryptoInit(TpzCtx *ctx, unsigned char *key, int klen);
void topazCryptoDecrypt(TpzCtx *ctx, unsigned char *in, unsigned char *out, int len);
int bookReadEncodedNumber(FILE *f);
int encodeNumber(int number, unsigned char *out);
char *bookReadString(FILE *f);

typedef struct _Payload {
   unsigned char *blob;
   unsigned int len;
   char *name;
   int index;
} Payload;

typedef struct _Record {
   int offset;
   int length;
   int compressed;
   struct _Record *next;
} Record;

typedef struct _HeaderRecord {
   char *tag;
   Record *rec;
   struct _HeaderRecord *next;
} HeaderRecord;

typedef struct _TopazFile {
   FILE *f;
   HeaderRecord *hdrs;
   unsigned char *bookKey;
   unsigned int bodyOffset;
   MapList *metadata;
   PidList *pids;    //extra pids to try from command line
} TopazFile;

Record *bookReadHeaderRecordData(FILE *f);
void freeRecordList(Record *r);
void freeHeaderList(HeaderRecord *r);
void freeTopazFile(TopazFile *t);
HeaderRecord *parseTopazHeaderRecord(FILE *f);
HeaderRecord *addRecord(HeaderRecord *head, HeaderRecord *r);
TopazFile *parseTopazHeader(FILE *f);
void freeTopazFile(TopazFile *tpz);
HeaderRecord *findHeader(TopazFile *tpz, char *tag);
void freePayload(Payload *p);
Payload *getBookPayloadRecord(TopazFile *t, char *name, int index, int explode);
char *getMetadata(TopazFile *t, char *key);
void parseMetadata(TopazFile *t);
void decryptRecord(unsigned char *in, int len, unsigned char *out, unsigned char *PID);
unsigned char *decryptDkeyRecord(unsigned char *data, int len, unsigned char *PID);
unsigned char *decryptDkeyRecords(Payload *data, unsigned char *PID);
void writeTopazOutputFile(TopazFile *t, FILE *out, cbuf *tpzHeaders, 
                          cbuf *tpzBody, int explode);


#endif
