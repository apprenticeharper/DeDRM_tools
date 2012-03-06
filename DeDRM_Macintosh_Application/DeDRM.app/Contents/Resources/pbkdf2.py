# A simple implementation of pbkdf2 using stock python modules. See RFC2898
# for details. Basically, it derives a key from a password and salt.

# Copyright 2004 Matt Johnston <matt @ ucc asn au>
# Copyright 2009 Daniel Holth <dholth@fastmail.fm>
# This code may be freely used and modified for any purpose.

# Revision history
# v0.1  October 2004    - Initial release
# v0.2  8 March 2007    - Make usable with hashlib in Python 2.5 and use
# v0.3  ""                 the correct digest_size rather than always 20
# v0.4  Oct 2009        - Rescue from chandler svn, test and optimize.

import sys
import hmac
from struct import pack
try:
    # only in python 2.5
    import hashlib
    sha = hashlib.sha1
    md5 = hashlib.md5
    sha256 = hashlib.sha256
except ImportError: # pragma: NO COVERAGE
    # fallback
    import sha
    import md5

# this is what you want to call.
def pbkdf2( password, salt, itercount, keylen, hashfn = sha ):
    try:
        # depending whether the hashfn is from hashlib or sha/md5
        digest_size = hashfn().digest_size
    except TypeError: # pragma: NO COVERAGE
        digest_size = hashfn.digest_size
    # l - number of output blocks to produce
    l = keylen / digest_size
    if keylen % digest_size != 0:
        l += 1

    h = hmac.new( password, None, hashfn )

    T = ""
    for i in range(1, l+1):
        T += pbkdf2_F( h, salt, itercount, i )

    return T[0: keylen]

def xorstr( a, b ):
    if len(a) != len(b):
        raise ValueError("xorstr(): lengths differ")
    return ''.join((chr(ord(x)^ord(y)) for x, y in zip(a, b)))

def prf( h, data ):
    hm = h.copy()
    hm.update( data )
    return hm.digest()

# Helper as per the spec. h is a hmac which has been created seeded with the
# password, it will be copy()ed and not modified.
def pbkdf2_F( h, salt, itercount, blocknum ):
    U = prf( h, salt + pack('>i',blocknum ) )
    T = U

    for i in range(2, itercount+1):
        U = prf( h, U )
        T = xorstr( T, U )

    return T
