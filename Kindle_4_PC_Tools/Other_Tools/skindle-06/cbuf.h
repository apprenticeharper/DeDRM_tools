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

#ifndef __CBUF_H
#define __CBUF_H

typedef struct _cbuf {
   unsigned int size;  //current size
   unsigned int idx;   //current position
   unsigned char *buf;
} cbuf;

cbuf *b_new(unsigned int size);
void b_free(cbuf *b);
void b_add_byte(cbuf *b, unsigned char ch);
void b_add_buf(cbuf *b, unsigned char *buf, unsigned int len);
void b_add_str(cbuf *b, const char *buf);

#endif
