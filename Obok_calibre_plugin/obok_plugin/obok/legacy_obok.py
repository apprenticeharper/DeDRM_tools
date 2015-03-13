# vim:fileencoding=UTF-8:ts=4:sw=4:sta:et:sts=4:ai

__license__   = 'GPL v3'
__docformat__ = 'restructuredtext en'

import os, sys
import binascii, hashlib, re, string

class legacy_obok(object):
    def __init__(self):
        self._userkey = ''

    @property
    def get_legacy_cookie_id(self):
        if self._userkey != '':
            return self._userkey
        self._userkey = self.__oldcookiedeviceid()
        return self._userkey
        
    def __bytearraytostring(self, bytearr):
        wincheck = re.match('@ByteArray\\((.+)\\)', bytearr)
        if wincheck:
            return wincheck.group(1)
        return bytearr
    
    def plist_to_dictionary(self, filename):
        from subprocess import Popen, PIPE
        from plistlib import readPlistFromString
        'Pipe the binary plist through plutil and parse the xml output'
        with open(filename, 'rb') as f:
            content = f.read()
        args = ['plutil', '-convert', 'xml1', '-o', '-', '--', '-']
        p = Popen(args, stdin=PIPE, stdout=PIPE)
        p.stdin.write(content)
        out, err = p.communicate()
        return readPlistFromString(out)
    
    def __oldcookiedeviceid(self):
        '''Optionally attempt to get a device id using the old cookie method.
        Must have _winreg installed on Windows machines for successful key retrieval.'''
        wsuid = ''
        pwsdid = ''
        try:
            if sys.platform.startswith('win'):
                import _winreg
                regkey_browser = _winreg.OpenKey(_winreg.HKEY_CURRENT_USER, 'Software\\Kobo\\Kobo Desktop Edition\\Browser')
                cookies = _winreg.QueryValueEx(regkey_browser, 'cookies')
                bytearrays = cookies[0]
            elif sys.platform.startswith('darwin'):
                prefs = os.path.join(os.environ['HOME'], 'Library/Preferences/com.kobo.Kobo Desktop Edition.plist')
                cookies = self.plist_to_dictionary(prefs)
                bytearrays = cookies['Browser.cookies']
            for bytearr in bytearrays:
                cookie = self.__bytearraytostring(bytearr)
                wsuidcheck = re.match("^wsuid=([0-9a-f-]+)", cookie)
                if(wsuidcheck):
                    wsuid = wsuidcheck.group(1)
                pwsdidcheck = re.match('^pwsdid=([0-9a-f-]+)', cookie)
                if (pwsdidcheck):
                    pwsdid = pwsdidcheck.group(1)
            if (wsuid == '' or pwsdid == ''):
                return None
            preuserkey = string.join((pwsdid, wsuid), '')
            userkey = hashlib.sha256(preuserkey).hexdigest()
            return binascii.a2b_hex(userkey[32:])
        except KeyError:
            print ('No "cookies" key found in Kobo plist: no legacy user key found.')
            return None
        except:
            print ('Error parsing Kobo plist: no legacy user key found.')
            return None
