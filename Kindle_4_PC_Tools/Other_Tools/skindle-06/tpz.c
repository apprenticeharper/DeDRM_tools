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

#include "skinutils.h"
#include "cbuf.h"
#include "tpz.h"
#include "zlib.h"

//
// Context initialisation for the Topaz Crypto
//
void topazCryptoInit(TpzCtx *ctx, unsigned char *key, int klen) {
   int i = 0; 
   ctx->v[0] = 0x0CAFFE19E;
    
   for (i = 0; i < klen; i++) {
      ctx->v[1] = ctx->v[0]; 
      ctx->v[0] = ((ctx->v[0] >> 2) * (ctx->v[0] >> 7)) ^  
                  (key[i] * key[i] * 0x0F902007);
   }
}

//
// decrypt data with the context prepared by topazCryptoInit()
//
    
void topazCryptoDecrypt(TpzCtx *ctx, unsigned char *in, unsigned char *out, int len) {
   unsigned int ctx1 = ctx->v[0];
   unsigned int ctx2 = ctx->v[1];
   int i;
   for (i = 0; i < len; i++) {
      unsigned char m = in[i] ^ (ctx1 >> 3) ^ (ctx2 << 3);
      ctx2 = ctx1;
      ctx1 = ((ctx1 >> 2) * (ctx1 >> 7)) ^ (m * m * 0x0F902007);
      out[i] = m;
   }
}

int bookReadEncodedNumber(FILE *f) {
   int flag = 0;
   int data = fgetc(f);
   if (data == 0xFF) {  //negative number flag
      flag = 1;
      data = fgetc(f);
   }
   if (data >= 0x80) {
      int datax = data & 0x7F;
      while (data >= 0x80) {
         data = fgetc(f);
         datax = (datax << 7) + (data & 0x7F);
      }
      data = datax;
   }
   
   if (flag) {
      data = -data;
   }
   return data;
}

//
// Encode a number in 7 bit format
//

int encodeNumber(int number, unsigned char *out) {
   unsigned char *b = out;
   unsigned char flag = 0;
   int len;
   int neg = number < 0;
   
   if (neg) {
      number = -number + 1;
   }
   
   do {
      *b++ = (number & 0x7F) | flag;
      number >>= 7;
      flag = 0x80;
   } while (number);  

   if (neg) {
      *b++ = 0xFF;
   }
   len = b - out;
   b--;
   while (out < b) {
      unsigned char v = *out;
      *out++ = *b;
      *b-- = v;
   } 
   return len;
}

//
// Get a length prefixed string from the file 
//

char *bookReadString(FILE *f) {
   int len = bookReadEncodedNumber(f);
   char *s = (char*)malloc(len + 1);
   s[len] = 0;
   if (fread(s, 1, len, f) != len) {
      fprintf(stderr, "String read failed at filepos %x\n", ftell(f));
      free(s);
      s = NULL;
   }
   return s;
}
    
//
// Read and return the data of one header record at the current book file position [[offset,compressedLength,decompressedLength],...]
//

Record *bookReadHeaderRecordData(FILE *f) {
   int nbValues = bookReadEncodedNumber(f);
   Record *result = NULL;
   Record *tail = NULL;
   unsigned int i;
   if (nbValues == -1) {
      fprintf(stderr, "Parse Error : EOF encountered\n");
      return NULL;
   }
   for (i = 0; i < nbValues; i++) {
      Record *r = (Record*)malloc(sizeof(Record));
      r->offset = bookReadEncodedNumber(f);
      r->length = bookReadEncodedNumber(f);
      r->compressed = bookReadEncodedNumber(f);
      r->next = NULL;
      if (result == NULL) {
         result = r;
      }
      else {
         tail->next = r;
      }
      tail = r;
   }
   return result;
}

//
// Read and parse one header record at the current book file position and return the associated data [[offset,compressedLength,decompressedLength],...]
//

void freeRecordList(Record *r) {
   Record *n;
   while (r) {
      n = r;
      r = r->next;
      free(n);
   }
}

void freeHeaderList(HeaderRecord *r) {
   HeaderRecord *n;
   while (r) {
      free(r->tag);
      freeRecordList(r->rec);
      n = r;
      r = r->next;
      free(n);
   }
}

void freeTopazFile(TopazFile *t) {
   freeHeaderList(t->hdrs);
   freeMap(t->metadata);
   free(t);
}

HeaderRecord *parseTopazHeaderRecord(FILE *f) {
   char *tag;
   Record *record;
   if (fgetc(f) != 0x63) {
      fprintf(stderr, "Parse Error : Invalid Header at 0x%x\n", ftell(f) - 1);
      return NULL;
   }
    
   tag = bookReadString(f);
   record = bookReadHeaderRecordData(f);
   if (tag && record) {
      HeaderRecord *r = (HeaderRecord*)malloc(sizeof(Record));
      r->tag = tag;
      r->rec = record;
      r->next = NULL;
      return r;
   }
   return NULL;
}

//
// Parse the header of a Topaz file, get all the header records and the offset for the payload
//
 
HeaderRecord *addRecord(HeaderRecord *head, HeaderRecord *r) {
   HeaderRecord *i;
   for (i = head; i; i = i->next) {
      if (i->next == NULL) {
         i->next = r;
         return head;
      }
   }
   return r;
}

TopazFile *parseTopazHeader(FILE *f) {
   unsigned int numRecs, i, magic;
   TopazFile *tpz;
   if (fread(&magic, sizeof(magic), 1, f) != 1) {
      fprintf(stderr, "Failed to read file magic\n");
      return NULL;
   }
   
   if (magic != 0x305a5054) {
      fprintf(stderr, "Parse Error : Invalid Header, not a Topaz file");
      return NULL;
   }
   
   numRecs = fgetc(f);

   tpz = (TopazFile*)calloc(sizeof(TopazFile), 1);
   tpz->f = f;

   for (i = 0; i < numRecs; i++) {
      HeaderRecord *result = parseTopazHeaderRecord(f);
      if (result == NULL) {
         break;
      }
      tpz->hdrs = addRecord(tpz->hdrs, result);
   }
   
   if (fgetc(f) != 0x64) {
      fprintf(stderr, "Parse Error : Invalid Header end at pos 0x%x\n", ftell(f) - 1);
      //empty list
      freeTopazFile(tpz);
      return NULL;
   }
   
   tpz->bodyOffset = ftell(f);
   return tpz;
}

HeaderRecord *findHeader(TopazFile *tpz, char *tag) {
   HeaderRecord *hr;
   for (hr = tpz->hdrs; hr; hr = hr->next) {
      if (strcmp(hr->tag, tag) == 0) {
         break;
      }
   }
   return hr;
}

void freePayload(Payload *p) {
   free(p->blob);
   free(p);
}

//
//Get a record in the book payload, given its name and index. If necessary the record is decrypted. The record is not decompressed
//
Payload *getBookPayloadRecord(TopazFile *t, char *name, int index, int explode) {   
   int encrypted = 0;
   int recordOffset, i, recordIndex;
   Record *r;
   int fileSize;
   char *tag;
   Payload *p;
   off_t fileOffset;
   HeaderRecord *hr = findHeader(t, name);

   if (hr == NULL) {
      fprintf(stderr, "Parse Error : Invalid Record, record %s not found\n", name);
      return NULL;
   }
   r = hr->rec;
   for (i = 0; r && i < index; i++) {
      r = r->next;
   }
   if (r == NULL) {
      fprintf(stderr, "Parse Error : Invalid Record, record %s:%d not found\n", name, index);
      return NULL;
   }
   recordOffset = r->offset;
    
   if (fseek(t->f, t->bodyOffset + recordOffset, SEEK_SET) == -1) {
      fprintf(stderr, "Parse Error : Invalid Record offset, record %s:%d\n", name, index);
      return NULL;
   }
    
   tag = bookReadString(t->f);
   if (strcmp(tag, name)) {
      fprintf(stderr, "Parse Error : Invalid Record offset, record %s:%d name doesn't match\n", name, index);
      return NULL;
   }    
   recordIndex = bookReadEncodedNumber(t->f);
    
   if (recordIndex < 0) {
      encrypted = 1;
      recordIndex = -recordIndex - 1;
   }
    
   if (recordIndex != index) {
      fprintf(stderr, "Parse Error : Invalid Record offset, record %s:%d index doesn't match\n", name, index);
      return NULL;
   }
   
   fileSize = r->compressed ? r->compressed : r->length;
   p = (Payload*)malloc(sizeof(Payload));
   p->blob = (unsigned char*)malloc(fileSize);
   p->len = fileSize;
   p->name = name;
   p->index = index;
   fileOffset = ftell(t->f);
   if (fread(p->blob, fileSize, 1, t->f) != 1) {
      freePayload(p);
      fprintf(stderr, "Parse Error : Failed payload read of record %s:%d offset 0x%x:0x%x\n", name, index, fileOffset, fileSize);
      return NULL;
   }     
   
   if (encrypted) {
      TpzCtx ctx;
      topazCryptoInit(&ctx, t->bookKey, 8);
      topazCryptoDecrypt(&ctx, p->blob, p->blob, p->len);
   }
   
   if (r->compressed && explode) {
      unsigned char *db = (unsigned char *)malloc(r->length);
      uLongf dl = r->length;
      switch (uncompress(db, &dl, p->blob, p->len)) {
         case Z_OK:
            free(p->blob);
            p->blob = db;
            p->len = dl;
            break;
         case Z_MEM_ERROR:
            free(db);
            fprintf(stderr, "out of memory\n");
            break;         
         case Z_BUF_ERROR:
            free(db);
            fprintf(stderr, "output buffer wasn't large enough!\n");
            break;
      }
   }
   
   return p;
}

//
// Parse the metadata record from the book payload and return a list of [key,values]
//

char *getMetadata(TopazFile *t, char *key) {
   return getNodeValue(t->metadata, key);
}

void parseMetadata(TopazFile *t) {
   char *tag;
   int flags, nbRecords, i;
   HeaderRecord *hr = findHeader(t, "metadata");
    
   fseek(t->f, t->bodyOffset + hr->rec->offset, SEEK_SET);
   tag = bookReadString(t->f);
   if (strcmp(tag, "metadata")) {
      //raise CMBDTCFatal("Parse Error : Record Names Don't Match")
      return;
   }
    
   flags = fgetc(t->f);
   nbRecords = bookReadEncodedNumber(t->f);
    
   for (i = 0; i < nbRecords; i++) {
      char *key = bookReadString(t->f);
      char *value = bookReadString(t->f);
      t->metadata = addMapNode(t->metadata, key, value);
   }
}

//
// Decrypt a payload record with the PID
//

void decryptRecord(unsigned char *in, int len, unsigned char *out, unsigned char *PID) {
   TpzCtx ctx;
   topazCryptoInit(&ctx, PID, 8);  //is this length correct
   topazCryptoDecrypt(&ctx, in, out, len);
}

//
// Try to decrypt a dkey record (contains the book PID)
//
unsigned char *decryptDkeyRecord(unsigned char *data, int len, unsigned char *PID) {
   decryptRecord(data, len, data, PID);
   //fields = unpack("3sB8sB8s3s",record);
    
   if (strncmp(data, "PID", 3) || strncmp(data + 21, "pid", 3)) {
      fprintf(stderr, "Didn't find PID magic numbers in record\n");
      return NULL;
   }
   else if (data[3] != 8 || data[12] != 8) {
      fprintf(stderr, "Record didn't contain correct length fields\n");
      return NULL;
   }
   else if (strncmp(data + 4, PID, 8)) {
      fprintf(stderr, "Record didn't contain PID\n");
      return NULL;
   }
   return data + 13;
}
    
//
// Decrypt all the book's dkey records (contain the book PID)
//
 
unsigned char *decryptDkeyRecords(Payload *data, unsigned char *PID) {
   int nbKeyRecords = data->blob[0];  //is this encoded number?
   int i, idx;
   idx = 1;
   unsigned char *key = NULL;
//   records = []
   for (i = 0; i < nbKeyRecords && idx < data->len; i++) {
      int length = data->blob[idx++];
      key = decryptDkeyRecord(data->blob + idx, length, PID);
      if (key) break;    //???
      idx += length;
   }
   return key;
}

void bufEncodeInt(cbuf *b, int i) {
   unsigned char encoded[16];
   int len = encodeNumber(i, encoded);
   b_add_buf(b, encoded, len);
}

void bufEncodeString(cbuf *b, char *s) {
   bufEncodeInt(b, strlen(s));
   b_add_str(b, s);
}

void writeTopazOutputFile(TopazFile *t, FILE *out, cbuf *tpzHeaders, 
                          cbuf *tpzBody, int explode) {
   int i, numHdrs = 0;
   HeaderRecord *h;
   b_add_str(tpzHeaders, "TPZ0");
   for (h = t->hdrs; h; h = h->next) {
      if (strcmp(h->tag, "dkey")) {
         numHdrs++;
      }
   }
   bufEncodeInt(tpzHeaders, numHdrs);

   b_add_byte(tpzBody, 0x40);

   for (h = t->hdrs; h; h = h->next) {
      Record *r;
      int nr = 0, idx = 0;
      if (strcmp(h->tag, "dkey") == 0) continue;
      b_add_byte(tpzHeaders, 0x63);
      bufEncodeString(tpzHeaders, h->tag);
      for (r = h->rec; r; r = r->next) nr++;
      bufEncodeInt(tpzHeaders, nr);
      for (r = h->rec; r; r = r->next) {
         Payload *p;
         int b, e;
         bufEncodeInt(tpzHeaders, tpzBody->idx);         
         bufEncodeString(tpzBody, h->tag);
         bufEncodeInt(tpzBody, idx);
         b = tpzBody->idx;
         p = getBookPayloadRecord(t, h->tag, idx++, explode);
         b_add_buf(tpzBody, p->blob, p->len);
         e = tpzBody->idx;

         bufEncodeInt(tpzHeaders, r->length);   //this is length of blob portion after decompression
         if (explode) {
            bufEncodeInt(tpzHeaders, 0); //this is the length in the file if compressed
         }
         else {
            bufEncodeInt(tpzHeaders, r->compressed); //this is the length in the file if compressed
         }
         
         freePayload(p);
      }
   }
   
   b_add_byte(tpzHeaders, 0x64);
}

