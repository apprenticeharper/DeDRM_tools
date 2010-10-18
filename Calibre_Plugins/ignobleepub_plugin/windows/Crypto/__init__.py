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

"""Python Cryptography Toolkit

A collection of cryptographic modules implementing various algorithms
and protocols.

Subpackages:
Crypto.Cipher             Secret-key encryption algorithms (AES, DES, ARC4)
Crypto.Hash               Hashing algorithms (MD5, SHA, HMAC)
Crypto.Protocol           Cryptographic protocols (Chaffing, all-or-nothing
                          transform).   This package does not contain any
                          network protocols.
Crypto.PublicKey          Public-key encryption and signature algorithms
                          (RSA, DSA)
Crypto.Util               Various useful modules and functions (long-to-string
                          conversion, random number generation, number
                          theoretic functions)
"""

__all__ = ['Cipher', 'Hash', 'Protocol', 'PublicKey', 'Util']

__version__ = '2.3'     # See also below and setup.py
__revision__ = "$Id$"

# New software should look at this instead of at __version__ above.
version_info = (2, 1, 0, 'final', 0)    # See also above and setup.py

