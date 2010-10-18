# -*- coding: utf-8 -*-
#
# ===================================================================
# The contents of this file are dedicated to the public domain.  To
# the extent that dedication to the public domain is not available,
# everyone is granted a worldwide, perpetual, royalty-free,
# non-exclusive license to exercise all rights associated with the
# contents of this file for any purpose whatsoever.
# No rights are reserved.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ===================================================================

"""Secret-key encryption algorithms.

Secret-key encryption algorithms transform plaintext in some way that
is dependent on a key, producing ciphertext. This transformation can
easily be reversed, if (and, hopefully, only if) one knows the key.

The encryption modules here all support the interface described in PEP
272, "API for Block Encryption Algorithms".

If you don't know which algorithm to choose, use AES because it's
standard and has undergone a fair bit of examination.

Crypto.Cipher.AES         Advanced Encryption Standard
Crypto.Cipher.ARC2        Alleged RC2
Crypto.Cipher.ARC4        Alleged RC4
Crypto.Cipher.Blowfish
Crypto.Cipher.CAST
Crypto.Cipher.DES         The Data Encryption Standard.  Very commonly used
                          in the past, but today its 56-bit keys are too small.
Crypto.Cipher.DES3        Triple DES.
Crypto.Cipher.XOR         The simple XOR cipher.
"""

__all__ = ['AES', 'ARC2', 'ARC4',
           'Blowfish', 'CAST', 'DES', 'DES3',
           'XOR'
           ]

__revision__ = "$Id$"


