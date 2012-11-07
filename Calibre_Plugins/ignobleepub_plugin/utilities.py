#!/usr/bin/env python

from __future__ import with_statement
__license__ = 'GPL v3'

import hashlib

from ctypes import CDLL, POINTER, c_void_p, c_char_p, c_int, c_long, \
						Structure, c_ulong, create_string_buffer, cast
from ctypes.util import find_library

from PyQt4.Qt import (Qt, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit,
                      QGroupBox, QDialog, QDialogButtonBox)

from calibre.gui2 import error_dialog
from calibre.constants import iswindows

from calibre_plugins.ignoble_epub.__init__ import PLUGIN_NAME, PLUGIN_VERSION

DETAILED_MESSAGE = \
'You have personal information stored in this plugin\'s customization '+ \
'string from a previous version of this plugin.\n\n'+ \
'This new version of the plugin can convert that info '+ \
'into key data that the new plugin can then use (which doesn\'t '+ \
'require personal information to be stored/displayed in an insecure '+ \
'manner like the old plugin did).\n\nIf you choose NOT to migrate this data at this time '+ \
'you will be prompted to save that personal data to a file elsewhere; and you\'ll have '+ \
'to manually re-configure this plugin with your information.\n\nEither way... ' + \
'this new version of the plugin will not be responsible for storing that personal '+ \
'info in plain sight any longer.'

class IGNOBLEError(Exception):
    pass

def normalize_name(name): # Strip spaces and convert to lowercase.
    return ''.join(x for x in name.lower() if x != ' ')

# These are the key ENCRYPTING aes crypto functions
def generate_keyfile(name, ccn):
	# Load the necessary crypto libs.
	AES = _load_crypto()
	name = normalize_name(name) + '\x00'
	ccn = ccn + '\x00'
	name_sha = hashlib.sha1(name).digest()[:16]
	ccn_sha = hashlib.sha1(ccn).digest()[:16]
	both_sha = hashlib.sha1(name + ccn).digest()
	aes = AES(ccn_sha, name_sha)
	crypt = aes.encrypt(both_sha + ('\x0c' * 0x0c))
	userkey = hashlib.sha1(crypt).digest()

	return userkey.encode('base64')

def _load_crypto_libcrypto():
    if iswindows:
        libcrypto = find_library('libeay32')
    else:
        libcrypto = find_library('crypto')
    if libcrypto is None:
        raise IGNOBLEError('libcrypto not found')
    libcrypto = CDLL(libcrypto)

    AES_MAXNR = 14
    
    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)

    class AES_KEY(Structure):
        _fields_ = [('rd_key', c_long * (4 * (AES_MAXNR + 1))),
                    ('rounds', c_int)]
    AES_KEY_p = POINTER(AES_KEY)
    
    def F(restype, name, argtypes):
        func = getattr(libcrypto, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    
    AES_set_encrypt_key = F(c_int, 'AES_set_encrypt_key',
                            [c_char_p, c_int, AES_KEY_p])
    AES_cbc_encrypt = F(None, 'AES_cbc_encrypt',
                        [c_char_p, c_char_p, c_ulong, AES_KEY_p, c_char_p,
                         c_int])
    
    class AES(object):
        def __init__(self, userkey, iv):
            self._blocksize = len(userkey)
            self._iv = iv
            key = self._key = AES_KEY()
            rv = AES_set_encrypt_key(userkey, len(userkey) * 8, key)
            if rv < 0:
                raise IGNOBLEError('Failed to initialize AES Encrypt key')
    
        def encrypt(self, data):
            out = create_string_buffer(len(data))
            rv = AES_cbc_encrypt(data, out, len(data), self._key, self._iv, 1)
            if rv == 0:
                raise IGNOBLEError('AES encryption failed')
            return out.raw
    return AES

def _load_crypto_pycrypto():
    from Crypto.Cipher import AES as _AES

    class AES(object):
        def __init__(self, key, iv):
            self._aes = _AES.new(key, _AES.MODE_CBC, iv)

        def encrypt(self, data):
            return self._aes.encrypt(data)
    return AES
    
def _load_crypto():
    _aes = None
    cryptolist = (_load_crypto_libcrypto, _load_crypto_pycrypto)
    if iswindows:
        cryptolist = (_load_crypto_pycrypto, _load_crypto_libcrypto)
    for loader in cryptolist:
        try:
            _aes = loader()
            break
        except (ImportError, IGNOBLEError):
            pass
    return _aes

def caselessStrCmp(s1, s2):
    """
    A function to case-insensitively compare strings. Python's .lower() function
    isn't always very accurate when it comes to unicode. Using the standard C lib's
    strcasecmp instead. Maybe a tad slower, but we're not scouring scads of string lists here.
    """
    str1 = unicode(s1)
    str2 = unicode(s2)
    
    c_char_pp = POINTER(c_char_p)
    c_int_p = POINTER(c_int)
    
    if iswindows:
        libc = find_library('msvcrt')
    else:
        libc = find_library('c')
    if libc is None:
        raise IgnobleError('libc not found')
    libc = CDLL(libc)
    
    def F(restype, name, argtypes):
        func = getattr(libc, name)
        func.restype = restype
        func.argtypes = argtypes
        return func
    
    if iswindows:
        _stricmp = F(c_int, '_stricmp', [c_char_p, c_char_p])
        return _stricmp(str1, str2)
    strcasecmp = F(c_int, 'strcasecmp', [c_char_p, c_char_p])
    return strcasecmp(str1, str2)

class AddKeyDialog(QDialog):
	def __init__(self, parent=None,):
		QDialog.__init__(self, parent)
		self.parent = parent
		self.setWindowTitle('Create New Ignoble Key')
		layout = QVBoxLayout(self)
		self.setLayout(layout)

		data_group_box = QGroupBox('', self)
		layout.addWidget(data_group_box)
		data_group_box_layout = QVBoxLayout()
		data_group_box.setLayout(data_group_box_layout)
		
		key_group = QHBoxLayout()
		data_group_box_layout.addLayout(key_group)
		key_group.addWidget(QLabel('Unique Key Name:', self))
		self.key_ledit = QLineEdit('', self)
		self.key_ledit.setToolTip(_('<p>Enter an identifying name for this new Ignoble key.</p>' +
								'<p>It should be something that will help you remember ' +
								'what personal information was used to create it.'))
		key_group.addWidget(self.key_ledit)
		key_label = QLabel(_(''), self)
		key_label.setAlignment(Qt.AlignHCenter)
		data_group_box_layout.addWidget(key_label)

		name_group = QHBoxLayout()
		data_group_box_layout.addLayout(name_group)
		name_group.addWidget(QLabel('Your Name:', self))
		self.name_ledit = QLineEdit('', self)
		self.name_ledit.setToolTip(_('<p>Enter your name as it appears in your B&N ' +
								'account and/or on your credit card.</p>' +
								'<p>It will only be used to generate this ' +
								'one-time key and won\'t be stored anywhere ' +
								'in calibre or on your computer.</p>' +
								'<p>(ex: Jonathan Smith)'))
		name_group.addWidget(self.name_ledit)
		name_disclaimer_label = QLabel(_('Will not be stored/saved in configuration data:'), self)
		name_disclaimer_label.setAlignment(Qt.AlignHCenter)
		data_group_box_layout.addWidget(name_disclaimer_label)
	
		ccn_group = QHBoxLayout()
		data_group_box_layout.addLayout(ccn_group)
		ccn_group.addWidget(QLabel('Credit Card#:', self))
		self.cc_ledit = QLineEdit('', self)
		self.cc_ledit.setToolTip(_('<p>Enter the full credit card number on record ' +
								'in your B&N account.</p>' +
								'<p>No spaces or dashes... just the numbers. ' +
								'This CC# will only be used to generate this ' +
								'one-time key and won\'t be stored anywhere in ' +
								'calibre or on your computer.'))
		ccn_group.addWidget(self.cc_ledit)
		ccn_disclaimer_label = QLabel(_('Will not be stored/saved in configuration data:'), self)
		ccn_disclaimer_label.setAlignment(Qt.AlignHCenter)
		data_group_box_layout.addWidget(ccn_disclaimer_label)
		layout.addSpacing(20)

		self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
		self.button_box.accepted.connect(self.accept)
		self.button_box.rejected.connect(self.reject)
		layout.addWidget(self.button_box)

		self.resize(self.parent.sizeHint())

	def accept(self):
		match = False
		if (self.key_ledit.text().isEmpty() or self.name_ledit.text().isEmpty()
								or self.cc_ledit.text().isEmpty()):
			errmsg = '<p>All fields are required!'
			return error_dialog(None, PLUGIN_NAME + 'error_dialog',
									_(errmsg), show=True, show_copy_button=False)
		for k in self.parent.plugin_keys.keys():
			if caselessStrCmp(self.key_ledit.text(), k) == 0:
				match = True
				break
		if match:
			errmsg = '<p>The key name <strong>%s</strong> is already being used.' % self.key_ledit.text()
			return error_dialog(None, PLUGIN_NAME + 'error_dialog',
									_(errmsg), show=True, show_copy_button=False)
		else:
			QDialog.accept(self)

	@property
	def user_name(self):
		return unicode(self.name_ledit.text()).strip().lower().replace(' ', '')
		
	@property
	def cc_number(self):
		return unicode(self.cc_ledit.text()).strip().replace(' ', '').replace('-','')
		
	@property
	def key_name(self):
		return unicode(self.key_ledit.text())

def parseCustString(keystuff):
	userkeys = []
	ar = keystuff.split(':')
	for i in ar:
		try:
			name, ccn = i.split(',')
		except:
			return False
		# Generate Barnes & Noble EPUB user key from name and credit card number.
		userkeys.append(generate_keyfile(name, ccn))
	return userkeys