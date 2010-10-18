#
#   pubkey.py : Internal functions for public key operations
#
#  Part of the Python Cryptography Toolkit
#
#  Written by Andrew Kuchling, Paul Swartz, and others
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
#

__revision__ = "$Id$"

import types, warnings
from Crypto.Util.number import *

# Basic public key class
class pubkey:
    def __init__(self):
        pass

    def __getstate__(self):
        """To keep key objects platform-independent, the key data is
        converted to standard Python long integers before being
        written out.  It will then be reconverted as necessary on
        restoration."""
        d=self.__dict__
        for key in self.keydata:
            if d.has_key(key): d[key]=long(d[key])
        return d

    def __setstate__(self, d):
        """On unpickling a key object, the key data is converted to the big
number representation being used, whether that is Python long
integers, MPZ objects, or whatever."""
        for key in self.keydata:
            if d.has_key(key): self.__dict__[key]=bignum(d[key])

    def encrypt(self, plaintext, K):
        """encrypt(plaintext:string|long, K:string|long) : tuple
        Encrypt the string or integer plaintext.  K is a random
        parameter required by some algorithms.
        """
        wasString=0
        if isinstance(plaintext, types.StringType):
            plaintext=bytes_to_long(plaintext) ; wasString=1
        if isinstance(K, types.StringType):
            K=bytes_to_long(K)
        ciphertext=self._encrypt(plaintext, K)
        if wasString: return tuple(map(long_to_bytes, ciphertext))
        else: return ciphertext

    def decrypt(self, ciphertext):
        """decrypt(ciphertext:tuple|string|long): string
        Decrypt 'ciphertext' using this key.
        """
        wasString=0
        if not isinstance(ciphertext, types.TupleType):
            ciphertext=(ciphertext,)
        if isinstance(ciphertext[0], types.StringType):
            ciphertext=tuple(map(bytes_to_long, ciphertext)) ; wasString=1
        plaintext=self._decrypt(ciphertext)
        if wasString: return long_to_bytes(plaintext)
        else: return plaintext

    def sign(self, M, K):
        """sign(M : string|long, K:string|long) : tuple
        Return a tuple containing the signature for the message M.
        K is a random parameter required by some algorithms.
        """
        if (not self.has_private()):
            raise TypeError('Private key not available in this object')
        if isinstance(M, types.StringType): M=bytes_to_long(M)
        if isinstance(K, types.StringType): K=bytes_to_long(K)
        return self._sign(M, K)

    def verify (self, M, signature):
        """verify(M:string|long, signature:tuple) : bool
        Verify that the signature is valid for the message M;
        returns true if the signature checks out.
        """
        if isinstance(M, types.StringType): M=bytes_to_long(M)
        return self._verify(M, signature)

    # alias to compensate for the old validate() name
    def validate (self, M, signature):
        warnings.warn("validate() method name is obsolete; use verify()",
                      DeprecationWarning)

    def blind(self, M, B):
        """blind(M : string|long, B : string|long) : string|long
        Blind message M using blinding factor B.
        """
        wasString=0
        if isinstance(M, types.StringType):
            M=bytes_to_long(M) ; wasString=1
        if isinstance(B, types.StringType): B=bytes_to_long(B)
        blindedmessage=self._blind(M, B)
        if wasString: return long_to_bytes(blindedmessage)
        else: return blindedmessage

    def unblind(self, M, B):
        """unblind(M : string|long, B : string|long) : string|long
        Unblind message M using blinding factor B.
        """
        wasString=0
        if isinstance(M, types.StringType):
            M=bytes_to_long(M) ; wasString=1
        if isinstance(B, types.StringType): B=bytes_to_long(B)
        unblindedmessage=self._unblind(M, B)
        if wasString: return long_to_bytes(unblindedmessage)
        else: return unblindedmessage


    # The following methods will usually be left alone, except for
    # signature-only algorithms.  They both return Boolean values
    # recording whether this key's algorithm can sign and encrypt.
    def can_sign (self):
        """can_sign() : bool
        Return a Boolean value recording whether this algorithm can
        generate signatures.  (This does not imply that this
        particular key object has the private information required to
        to generate a signature.)
        """
        return 1

    def can_encrypt (self):
        """can_encrypt() : bool
        Return a Boolean value recording whether this algorithm can
        encrypt data.  (This does not imply that this
        particular key object has the private information required to
        to decrypt a message.)
        """
        return 1

    def can_blind (self):
        """can_blind() : bool
        Return a Boolean value recording whether this algorithm can
        blind data.  (This does not imply that this
        particular key object has the private information required to
        to blind a message.)
        """
        return 0

    # The following methods will certainly be overridden by
    # subclasses.

    def size (self):
        """size() : int
        Return the maximum number of bits that can be handled by this key.
        """
        return 0

    def has_private (self):
        """has_private() : bool
        Return a Boolean denoting whether the object contains
        private components.
        """
        return 0

    def publickey (self):
        """publickey(): object
        Return a new key object containing only the public information.
        """
        return self

    def __eq__ (self, other):
        """__eq__(other): 0, 1
        Compare us to other for equality.
        """
        return self.__getstate__() == other.__getstate__()

    def __ne__ (self, other):
        """__ne__(other): 0, 1
        Compare us to other for inequality.
        """
        return not self.__eq__(other)
