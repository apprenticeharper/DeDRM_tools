/*
 sha1.c: Implementation of SHA-1 Secure Hash Algorithm-1

 Based upon: NIST FIPS180-1 Secure Hash Algorithm-1
   http://www.itl.nist.gov/fipspubs/fip180-1.htm

 Non-official Japanese Translation by HIRATA Yasuyuki:
   http://yasu.asuka.net/translations/SHA-1.html

 Copyright (C) 2002 vi@nwr.jp. All rights reserved.

 This software is provided 'as-is', without any express or implied
 warranty. In no event will the authors be held liable for any damages
 arising from the use of this software.

 Permission is granted to anyone to use this software for any purpose,
 including commercial applications, and to alter it and redistribute it
 freely, subject to the following restrictions:

 1. The origin of this software must not be misrepresented; you must not
    claim that you wrote the original software. If you use this software
    in a product, an acknowledgement in the product documentation would be
    appreciated but is not required.
 2. Altered source versions must be plainly marked as such, and must not be
    misrepresented as beging the original software.
 3. This notice may not be removed or altered from any source distribution.

 Note:
   The copyright notice above is copied from md5.h by L. Peter Deutsch
   <ghost@aladdin.com>. Thank him since I'm not a good speaker of English. :)
 */
#include <string.h>
#include "sha1.h"

/*
 * Packing bytes to a word
 *
 * Should not assume p is aligned to word boundary
 */
static sha1_word_t packup(sha1_byte_t *p)
{
  /* Portable, but slow */
  return p[0] << 24 | p[1] << 16 | p[2] << 8 | p[3] << 0;
}

/*
 * Unpacking a word to bytes
 *
 * Should not assume p is aligned to word boundary
 */
static void unpackup(sha1_byte_t *p, sha1_word_t q)
{
  p[0] = (q >> 24) & 0xff;
  p[1] = (q >> 16) & 0xff;
  p[2] = (q >>  8) & 0xff;
  p[3] = (q >>  0) & 0xff;
}

/*
 * Processing a block
 */
static void sha1_update_now(sha1_state_s *pms, sha1_byte_t *bp)
{
  sha1_word_t	tmp, a, b, c, d, e, w[16+16];
  int	i, s;

  /* pack 64 bytes into 16 words */
  for(i = 0; i < 16; i++) {
    w[i] = packup(bp + i * sizeof(sha1_word_t));
  }
  memcpy(w + 16, w + 0, sizeof(sha1_word_t) * 16);

  a = pms->sha1_h[0], b = pms->sha1_h[1], c = pms->sha1_h[2], d = pms->sha1_h[3], e = pms->sha1_h[4];

#define	rot(x,n) (((x) << n) | ((x) >> (32-n)))
#define	f0(b, c, d)	((b&c)|(~b&d))
#define	f1(b, c, d)	(b^c^d)
#define	f2(b, c, d)	((b&c)|(b&d)|(c&d))
#define	f3(b, c, d)	(b^c^d)
#define k0		0x5a827999
#define	k1		0x6ed9eba1
#define	k2		0x8f1bbcdc
#define	k3		0xca62c1d6

  /* t=0-15 */
  s = 0;
  for(i = 0; i < 16; i++) {
    tmp = rot(a, 5) + f0(b, c, d) + e + w[s] + k0;
    e = d; d = c; c = rot(b, 30); b = a; a = tmp;
    s = (s + 1) % 16;
  }

  /* t=16-19 */
  for(i = 16; i < 20; i++) {
    w[s] = rot(w[s+13] ^ w[s+8] ^ w[s+2] ^ w[s], 1);
    w[s+16] = w[s];
    tmp = rot(a, 5) + f0(b, c, d) + e + w[s] + k0;
    e = d; d = c; c = rot(b, 30); b = a; a = tmp;
    s = (s + 1) % 16;
  }

  /* t=20-39 */
  for(i = 0; i < 20; i++) {
    w[s] = rot(w[s+13] ^ w[s+8] ^ w[s+2] ^ w[s], 1);
    w[s+16] = w[s];
    tmp = rot(a, 5) + f1(b, c, d) + e + w[s] + k1;
    e = d; d = c; c = rot(b, 30); b = a; a = tmp;
    s = (s + 1) % 16;
  }

  /* t=40-59 */
  for(i = 0; i < 20; i++) {
    w[s] = rot(w[s+13] ^ w[s+8] ^ w[s+2] ^ w[s], 1);
    w[s+16] = w[s];
    tmp = rot(a, 5) + f2(b, c, d) + e + w[s] + k2;
    e = d; d = c; c = rot(b, 30); b = a; a = tmp;
    s = (s + 1) % 16;
  }

  /* t=60-79 */
  for(i = 0; i < 20; i++) {
    w[s] = rot(w[s+13] ^ w[s+8] ^ w[s+2] ^ w[s], 1);
    w[s+16] = w[s];
    tmp = rot(a, 5) + f3(b, c, d) + e + w[s] + k3;
    e = d; d = c; c = rot(b, 30); b = a; a = tmp;
    s = (s + 1) % 16;
  }

  pms->sha1_h[0] += a, pms->sha1_h[1] += b, pms->sha1_h[2] += c, pms->sha1_h[3] += d, pms->sha1_h[4] += e;
}

/*
 * Increment sha1_size1, sha1_size2 field of sha1_state_s
 */
static void incr(sha1_state_s *pms, int v)
{
  sha1_word_t	q;

  q = pms->sha1_size1 + v * BITS;
  if(q < pms->sha1_size1) {
    pms->sha1_size2++;
  }
  pms->sha1_size1 = q;
}

/*
 * Initialize sha1_state_s as FIPS specifies
 */
void	sha1_init(sha1_state_s *pms)
{
  memset(pms, 0, sizeof(*pms));
  pms->sha1_h[0] = 0x67452301;	/* Initialize H[0]-H[4] */
  pms->sha1_h[1] = 0xEFCDAB89;
  pms->sha1_h[2] = 0x98BADCFE;
  pms->sha1_h[3] = 0x10325476;
  pms->sha1_h[4] = 0xC3D2E1F0;
}

/*
 * Fill block and update output when needed
 */
void	sha1_update(sha1_state_s *pms, sha1_byte_t *bufp, int length)
{
  /* Is the buffer partially filled? */
  if(pms->sha1_count != 0) {
    if(pms->sha1_count + length >= (signed) sizeof(pms->sha1_buf)) {	/* buffer is filled enough */
      int fil = sizeof(pms->sha1_buf) - pms->sha1_count;		/* length to copy */

      memcpy(pms->sha1_buf + pms->sha1_count, bufp, fil);
      sha1_update_now(pms, pms->sha1_buf);
      length -= fil;
      bufp += fil;
      pms->sha1_count = 0;
      incr(pms, fil);
    } else {
      memcpy(pms->sha1_buf + pms->sha1_count, bufp, length);
      pms->sha1_count += length;
      incr(pms, length);
      return;
    }
  }

  /* Loop to update state */
  for(;;) {
    if(length < (signed) sizeof(pms->sha1_buf)) {		/* Short to fill up the buffer */
      if(length) {
        memcpy(pms->sha1_buf, bufp, length);
      }
      pms->sha1_count = length;
      incr(pms, length);
      break;
    }
    sha1_update_now(pms, bufp);
    length -= sizeof(pms->sha1_buf);
    bufp += sizeof(pms->sha1_buf);
    incr(pms, sizeof(pms->sha1_buf));
  }
}

void	sha1_finish(sha1_state_s *pms, sha1_byte_t output[SHA1_OUTPUT_SIZE])
{
  int i;
  sha1_byte_t buf[1];

  /* fill a bit */
  buf[0] = 0x80;
  sha1_update(pms, buf, 1);

  /* Decrement sha1_size1, sha1_size2 */
  if((pms->sha1_size1 -= BITS) == 0) {
    pms->sha1_size2--;
  }

  /* fill zeros */
  if(pms->sha1_count > (signed) (sizeof(pms->sha1_buf) - 2 * sizeof(sha1_word_t))) {
    memset(pms->sha1_buf + pms->sha1_count, 0, sizeof(pms->sha1_buf) - pms->sha1_count);
    sha1_update_now(pms, pms->sha1_buf);
    pms->sha1_count = 0;
  }
  memset(pms->sha1_buf + pms->sha1_count, 0,
    sizeof(pms->sha1_buf) - pms->sha1_count - sizeof(sha1_word_t) * 2);

  /* fill last length */
  unpackup(pms->sha1_buf + sizeof(pms->sha1_buf) - sizeof(sha1_word_t) * 2, pms->sha1_size2);
  unpackup(pms->sha1_buf + sizeof(pms->sha1_buf) - sizeof(sha1_word_t) * 1, pms->sha1_size1);

  /* final update */
  sha1_update_now(pms, pms->sha1_buf);

  /* move hash value to output byte array */
  for(i = 0; i < (signed) (sizeof(pms->sha1_h)/sizeof(sha1_word_t)); i++) {
    unpackup(output + i * sizeof(sha1_word_t), pms->sha1_h[i]);
  }
}
