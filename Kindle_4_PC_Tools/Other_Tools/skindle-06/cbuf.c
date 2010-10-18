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

#include <stdlib.h>
#include <string.h>
#include "cbuf.h"

cbuf *b_new(unsigned int size) {
   cbuf *b = (cbuf*)calloc(sizeof(cbuf), 1);
   if (b) {
      b->buf = (unsigned char *)malloc(size);
      b->size = b->buf ? size : 0;
   }
   return b;
}

void b_free(cbuf *b) {
   if (b) {
      free(b->buf);
      free(b);
   }
}

void b_add_byte(cbuf *b, unsigned char ch) {
   if (b == NULL) return;
   if (b->idx == b->size) {
      unsigned char *p = realloc(b->buf, b->size * 2);
      if (p) {
         b->buf = p;
         b->size = b->size * 2;
      }
   }
   if (b->idx < b->size) {
      b->buf[b->idx++] = ch;
   }
}

void b_add_buf(cbuf *b, unsigned char *buf, unsigned int len) {
   if (b == NULL) return;
   unsigned int new_sz = b->idx + len;
   while (b->size < new_sz) {
      unsigned char *p = realloc(b->buf, b->size * 2);
      if (p) {
         b->buf = p;
         b->size = b->size * 2;
      }
      else break;
   }
   if ((b->idx + len) <= b->size) {
      memcpy(b->buf + b->idx, buf, len);
      b->idx += len;
   }
}

void b_add_str(cbuf *b, const char *buf) {
   if (b == NULL) return;
   unsigned int len = strlen(buf);
   unsigned int new_sz = b->idx + len;
   while (b->size < new_sz) {
      unsigned char *p = realloc(b->buf, b->size * 2);
      if (p) {
         b->buf = p;
         b->size = b->size * 2;
      }
      else break;
   }
   if ((b->idx + len) <= b->size) {
      memcpy(b->buf + b->idx, buf, len);
      b->idx += len;
   }
}

