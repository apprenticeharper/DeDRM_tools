#!/bin/env python
# vim:ts=4:sw=4:softtabstop=4:smarttab:expandtab
#
# xPml2XHtml.py
#
# This is a python script. You need a Python interpreter to run it.
# For example, ActiveState Python, which exists for windows.
#
# Based on Code, Input and Ideas from: 
#      The Dark Reverser (original author)
#      Kevin Hendricks
#      Logan Kennelly
#      John Schember (Calibre project)
#      WayneD's (perl pml2html.pl)

# Changelog
#  0.02 - tried to greatly improve html conversion especially with \t tags
#  0.03 - more cleanup, a few fixes, and add in use of tidy to output xhtml
#  0.04 - incorporate more cleanups
#  0.05 - add check to fix block elements nested in inline elements which are not allowed
#  0.07 - handle clean up for remains left over from fixing nesting issues rampant in pml
#  0.08 - deal with inline style tags nesting issues in new way using a style tag list
#  0.09 - add in support for wrapping all text not in a block in <p></p> tags
#  0.10 - treat links effectively as block elements for style markup
#  0.11 - add in various paragraphs indentations to handle leading spaces that html would ignore or compress
#  0.12 - add in support for handling xml based pml footnotes and sidebars - using pseudo pml tags
#  0.14 - add in full header info parsing and remove need for bookinfo.txt
#  0.15 - cleanup high chars better handled, optional use of tidy with command line switch
#  0.16 - use proper and safe temporary file when passing things to tidy
#  0.17 - add support for tidy.exe under windows
#  0.18 - fix corner case of lines that start with \axxx or \Uxxxx tags
#  0.19 - change to use auto flushed stdout, and use proper return values
#  0.20 - properly handle T markup inside links
#  0.21 - properly handle new sigil Chapter Breaks for 0.2X series and up

__version__='0.21'

class Unbuffered:
    def __init__(self, stream):
        self.stream = stream
    def write(self, data):
        self.stream.write(data)
        self.stream.flush()
    def __getattr__(self, attr):
        return getattr(self.stream, attr)

import sys
sys.stdout=Unbuffered(sys.stdout)

import struct, binascii, zlib, os, getopt, os.path, urllib, re, tempfile
import logging
from subprocess import Popen, PIPE, STDOUT

logging.basicConfig()
#logging.basicConfig(level=logging.DEBUG)


class PmlConverter(object):
    def __init__(self, s):
        def cleanupHighChars(src):
            # special win1252 chars 0x80 - 0xa0 properly handled
            src = re.sub('[\x80-\xff]', lambda x: '\\a%03d' % ord(x.group()), src)
            src = re.sub('[^\x00-\xff]', lambda x: '\\U%04x' % ord(x.group()), src)
            return src
        def convertFootnoteXMLtoPseudoPML(src):
            # creates pseudo tag \Ft="id"footnote text\Ft
            p = re.compile(r'<footnote id="(?P<label>[^"]+)">\n')
            m = p.search(src)
            while m:
                (b, e) = m.span()
                fid = m.groups('label')[0]
                src = src[0:b] + '\\p\\Ft="' + fid + '"' + src[e:]
                src = re.sub('\n</footnote>\n','\\\\Ft\n\n',src,1)
                m = p.search(src)
            return src
        def convertSidebarXMLtoPseudoPML(src):
            # creates pseudo tag \St="id"sidebar text\St
            p = re.compile(r'<sidebar id="(?P<label>[^"]+)">\n')
            m = p.search(src)
            while m:
                (b, e) = m.span()
                sid = m.groups('label')[0]
                src = src[0:b] + '\\p\\St="' + sid + '"' + src[e:]
                src = re.sub('\n</sidebar>\n','\\\\St\n\n',src,1)
                m = p.search(src)
            return src
        def convert_x_to_pX0(src):
            # converts all \x \x to \p\X0 \X0 make later code simpler
            p = re.compile(r'\\x(.*?)\\x')
            m = p.search(src)
            while m:
                (b, e) = m.span()
                src = src[0:b] + '\\p\\X0' + src[b+2:e-2] + '\\X0' + src[e:]
                m = p.search(src)
            return src
        def findPrevStartofLine(src,p,n):
            # find last end of previous line in substring from p to n
            b1 = src.rfind('\n',p,n)
            b2 = src.rfind('\\c',p,n)
            b3 = src.rfind('\\r',p,n)
            b4 = src.rfind('\\x',p,n)
            b5 = src.rfind('\\p',p,n)
            b = max(b1, b2, b3, b4, b5)
            if b == -1:
                return n
            if b == b1:
                return b + 1
            return b + 2
        def markHangingIndents(src):
            r = ''
            p = 0
            while True:
                if p > len(src):
                    return r
                n = src.find('\\t', p)
                if n == -1:
                    r += src[p:]
                    return r
                pc = findPrevStartofLine(src,p,n)
                if pc == n :
                    # \t tag is at start of line so indent block will work
                    end = src.find('\\t',n+2)
                    if end == -1:
                        end = n
                    r += src[p:end+2]
                    p = end + 2
                else : 
                    # \t tag not at start of line so hanging indent case
                    # recode \t to pseudo \h tags and move it to start of this line
                    # and recode its close as well 
                    r += src[p:pc] + '\\h' + src[pc:n]
                    end = src.find('\\t',n+2)
                    if end == -1:
                        end = n+2
                    r += src[n+2:end] + '\\h'
                    p = end + 2
            return r
        # recode double single slashes in pml to allow easier regular expression usage 
        s = s.replace('\\\\','_amp#92_')
        s = cleanupHighChars(s)
        s = markHangingIndents(s)
        s = convertFootnoteXMLtoPseudoPML(s)
        s = convertSidebarXMLtoPseudoPML(s)
        s = convert_x_to_pX0(s)
        # file('converted.pml','wb').write(s)
        self.s = s
        self.pos = 0
        self.markChapters = (s.find('\\X') == -1)
    def headerInfo(self):
        title, author, copyright, publisher, eisbn = None, None, None, None, None
        m = re.search(r'\\v.*TITLE="(?P<value>[^"]+)".*\\v', self.s, re.DOTALL)
        if m:
            title = m.groups('value')[0]
        m = re.search(r'\\v.*AUTHOR="(?P<value>[^"]+)".*\\v', self.s, re.DOTALL)
        if m:
            author = m.groups('value')[0]
        m = re.search(r'\\v.*PUBLISHER="(?P<value>[^"]+)".*\\v', self.s, re.DOTALL)
        if m:
            publisher = m.groups('value')[0]
        m = re.search(r'\\v.*EISBN="(?P<value>[^"]+)".*\\v', self.s, re.DOTALL)
        if m:
            eisbn = m.groups('value')[0]
        m = re.search(r'\\v.*COPYRIGHT="(?P<value>[^"]+)".*\\v', self.s, re.DOTALL)
        if m:
            copyright = m.groups('value')[0]
        return title, author, copyright, publisher, eisbn
    def nextOptAttr(self):
        p = self.pos
        if self.s[p:p+2] != '="':
            return None
        r = ''
        p += 2
        while self.s[p] != '"':
            r += self.s[p]
            p += 1
        self.pos = p + 1
        return r
    def skipNewLine(self):
        p = self.pos
        if p >= len(self.s):
            return
        if self.s[p] == '\n':
            self.pos = p + 1
        return
    def next(self):
        p = self.pos
        if p >= len(self.s):
            return None
        if self.s[p] != '\\':
            res = self.s.find('\\', p)
            if res == -1:
                res = len(self.s)
            self.pos = res
            return self.s[p : res], None, None
        c = self.s[p+1]
        # add in support for new pseudo tag \\h
        if c in 'pxcriuovthnsblBk-lI\\d':
            self.pos = p + 2
            return None, c, None
        if c in 'TwmqQ':
            self.pos = p + 2
            return None, c, self.nextOptAttr()
        if c == 'a':
            self.pos = p + 5
            return None, c, int(self.s[p+2:p+5])
        if c == 'U':
            self.pos = p + 6
            return None, c, int(self.s[p+2:p+6], 16)
        c = self.s[p+1:p+1+2]
        if c in ('X0','X1','X2','X3','X4','Sp','Sb'):
            self.pos = p + 3
            return None, c, None
        # add in support for new pseudo tags Ft and St
        if c in ('C0','C1','C2','C3','C4','Fn','Sd', 'Ft', 'St'):
            self.pos = p + 3
            return None, c, self.nextOptAttr()
        print "unknown escape code %s" % c
        self.pos = p + 1
        return None, None, None
    def LinkPrinter(link):
        return '<a href="%s">' % link
    # for every footnote provide a unique id (built on footnote unique id) 
    # so that a hyperlink return is possibly
    def FootnoteLinkPrinter(link):
        rlink = 'return_' + link
        footnote_ids[link] = rlink 
        return '<a id="%s" href="#%s">' % (rlink, link)
    def Footnote(link):
        return '<div title="footnote" id="%s">' % link
    def EndFootnote(link):
        return '&nbsp;&nbsp;<a href="#%s"><small>return</small></a></div>' % footnote_ids[link]
    # for every sidebar provide a unique id (built from sidebar unique id) 
    # so that a hyperlink return is possibly
    def SidebarLinkPrinter(link):
        rlink = 'return_' + link
        sidebar_ids[link] = rlink 
        return '<a id="%s" href="#%s">' % (rlink, link)
    def Sidebar(link):
        return '<div title="sidebar" id="%s">' % link
    def EndSidebar(link):
        return '&nbsp;&nbsp;<a href="#%s"><small>return</small></a></div>' % sidebar_ids[link]
    # standard font switch is used mainly for special chars that may not be in user fonts
    # but since these special chars are html encoded neither of these are needed
    # def NormalFont(link):
    #     return '<!-- NormalFont -->%s' %link
    # def EndNormalFont(link):
    #     return '<!-- EndNormalFont -->'
    # def StdFont(link):
    #     return '<!-- StdFont -->%s' %link
    # def EndStdFont(link):
    #     return '<!-- EndStdFont -->'

    # See http://wiki.mobileread.com/wiki/PML#Palm_Markup_Language
    # html non-style related beg and end tags
    html_tags = {
        'v' : ('<!-- ', ' -->'),
        'c' : ('\n<div class="center">', '</div>\n'),
        'r' : ('\n<div class="right">', '</div>\n'),
        't' : ('<div class="indent">','</div>\n'),
        'h' : ('<div class="hang">','</div>\n'), # pseudo-tag created to handle hanging indent cases
        'X0' : ('<h1>', '</h1>\n'),
        'X1' : ('<h2>', '</h2>\n'),
        'X2' : ('<h3>', '</h3>\n'),
        'X3' : ('<h4>', '</h4>\n'),
        'X4' : ('<h5>', '</h5>\n'),
        'q' : (LinkPrinter, '</a>'),
        'Fn' : (FootnoteLinkPrinter, '</a>'),
        'Sd' : (SidebarLinkPrinter, '</a>'),
        'Ft' : (Footnote, EndFootnote),
        'St' : (Sidebar, EndSidebar),
        'I' : ('<i>', '</i>'),
        'P' : ('<p>', '</p>\n'), # pseudo tag indicating a paragraph (imputed from pml file contents)
        #'x' : ('<div class="breakafter"></div><h1>', '</h1>\n'), handled via recoding
    }
    
    # html style related beg and end tags
    html_style_tags = {
        'i' : ('<i>', '</i>'),
        'u' : ('<span class="under">', '</span>'),
        'b' : ('<b>', '</b>'),
        'B' : ('<b>', '</b>'),
        'o' : ('<del>', '</del>'),
        'v' : ('<!-- ', ' -->'),
        'Sb' : ('<sub>', '</sub>'),
        'Sp' : ('<sup>', '</sup>'),
        'l' : ('<span class="big">', '</span>'),
        'k' : ('<span class="smallcaps">', '</span>'),
        'I' : ('<i>', '</i>'), # according to calibre - all ereader does is italicize the index entries
        'l' : ('<span class="big">', '</span>'),
        'k' : ('<span class="smallcaps">', '</span>'),
        #'n' : (NormalFont, EndNormalFont), handle as a single and strip out to prevent undesired mid word breaks
        #'s' : (StdFont, EndStdFont), handle as a single and strip out to prevent undesired mid word breaks
    }

    # single tags (non-paired) that require no arguments
    html_one_tags = {
        #'p' : '<div class="breakafter"></div>\n', handle them in the if block to create at body level
        #'\\': '\\', handled via recoding
        '-' : '&shy;',
        's' : '', # strip out see earlier note on standard and normla font use
        'n' : '', # strip out see earlier note on standard and normla font use
    }

    # single tags that are not paired but that require attribute an argument
        #'w' : handled in the if block, 
        #'m' : handled in if block, 
        #'Q' : handled in if block, 
        #'a' : handled in if block, 
        #'U' : handled in if block, 
        #'C0' : handled in if block,
        #'C1' : handled in if block,
        #'C2' : handled in if block,
        #'C3' : handled in if block,
        #'C4' : handled in if block,
        #'T' : handled in if block,
 
    html_block_tags = ('c','r','t','h','X0','X1','X2','X3','X4','x','P', 'Ft', 'St')

    html_link_tags = ('q','Fn','Sd')

    html_comment_tags = ('v')

    pml_chars = {
        128 : '&#8364;', 129 : ''       , 130 : '&#8212;', 131 : '&#402;' , 132 : '&#8222;',
        133 : '&#8230;', 134 : '&#8224;', 135 : '&#8225;', 136 : '&#710;' , 137 : '&#8240;', 
        138 : '&#352;' , 139 : '&#8249;', 140 : '&#338;' , 141 : ''       , 142 : '&#381;' ,
        143 : ''       , 144 : ''       , 145 : '&#8216;', 146 : '&#8217;', 147 : '&#8220;', 
        148 : '&#8221;', 149 : '&#8226;', 150 : '&#8211;', 151 : '&#8212;', 152 : ''       ,
        153 : '&#8482;', 154 : '&#353;' , 155 : '&#8250;', 156 : '&#339;' , 157 : ''       , 
        158 : '&#382;' , 159 : '&#376;' , 160 : '&nbsp;' ,
    }


    def process(self):
        lastbreaksize = 0
        final = '<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        final += '<html>\n<head>\n'
        final += '<meta http-equiv="content-type" content="text/html; charset=windows-1252"/>\n'
        title, author, copyright, publisher, eisbn = self.headerInfo()
        if not title: title = bookname
        if not author: author = 'Unknown' 
        final += '<title>%s by %s</title>\n' % (title, author)
        final += '<meta name="Title" content="%s"/>\n' % title
        final += '<meta name="Author" content="%s"/>\n' % author
        if copyright: final += '<meta name="Copyright" content="%s"/>\n' % copyright
        if publisher: final += '<meta name="Publisher" content="%s"/>\n' % publisher
        if eisbn: final += '<meta name="EISBN" content="%s"/>\n' % eisbn
        final += '<style type="text/css">\n'
        final += 'div.center { text-align:center; }\n'
        final += 'div.right { text-align:right; }\n'
        final += 'div.indent { margin-left: 5%; margin-right: 5%; }\n'
        final += 'div.hang { text-indent: -5%; margin-left: 5%; margin-right: 5%; }\n'
        final += 'span.big { font-size: 175%; }\n'
        final += 'span.smallcaps { font-size: 80%; font-variant: small-caps; }\n'
        final += 'span.under { text-decoration: underline; }\n'
        final += '.breakafter { page-break-after: always; }\n'
        final += 'p { text-indent: 0; margin-top: 0; margin-bottom: 0; }\n' 
        final += 'p.i0 { text-indent: 0; margin-top: 0; margin-bottom: 0; }\n' 
        final += 'p.i1 { text-indent: 1%; margin-top: 0; margin-bottom: 0; }\n' 
        final += 'p.i2 { text-indent: 2%; margin-top: 0; margin-bottom: 0; }\n' 
        final += 'p.i3 { text-indent: 3%; margin-top: 0; margin-bottom: 0; }\n' 
        final += 'p.i4 { text-indent: 4%; margin-top: 0; margin-bottom: 0; }\n' 
        final += 'p.i5 { text-indent: 5%; margin-top: 0; margin-bottom: 0; }\n' 
        final += '</style>\n'
        final += '</head>\n<body>\n'
        in_tags = []
        st_tags = []
        
        def inSet(slist):
            rval = False
            j = len(in_tags)
            if j == 0:
                return False
            while True:
                j = j - 1
                if in_tags[j][0] in slist:
                    rval = True
                    break
                if j == 0:
                    break
            return rval

        def inBlock():
            return inSet(self.html_block_tags)

        def inLink():
            return inSet(self.html_link_tags)

        def inComment():
            return inSet(self.html_comment_tags)

        def inParaNow():
            j = len(in_tags)
            if j == 0:
                return False
            if in_tags[j-1][0] == 'P':
                return True
            return False

        def getTag(ti, end):
            cmd, attr = ti
            r = self.html_tags[cmd][end]
            if type(r) != str:
                r = r(attr)
            return r

        def getSTag(ti, end):
            cmd, attr = ti
            r = self.html_style_tags[cmd][end]
            if type(r) != str:
                r = r(attr)
            return r

        def applyStyles(ending):
            s = ''
            j = len(st_tags)
            if j > 0:
                if ending:
                    while True:
                        j = j - 1
                        s += getSTag(st_tags[j], True)
                        if j == 0:
                            break
                else:
                    k = 0
                    while True:
                        s += getSTag(st_tags[k], False)
                        k = k + 1
                        if k == j:
                            break
            return s

        def indentLevel(line_start):
            nb = 0
            while line_start[nb:nb+1] == ' ':
                nb = nb + 1
            line_start = line_start[nb:]
            if nb > 5:
                nb = 5
            return nb, line_start
            

        def makeText(s):
            # handle replacements required for html
            s = s.replace('&', '&amp;')
            s = s.replace('<', '&lt;')
            s = s.replace('>', '&gt;')
            return_s =''
            # parse the text line by line
            lp = s.find('\n')
            while lp != -1:
                line = s[0:lp]
                s = s[lp+1:]
                if not inBlock() and not inLink() and not inComment():
                    if len(line) > 0:
                        # text should not exist in the <body> tag level unless it is in a comment
                        nb, line = indentLevel(line)
                        return_s += '<p class="i%d">' % nb
                        return_s += applyStyles(False)    
                        return_s += line
                        return_s += applyStyles(True)
                        return_s += '</p>\n'
                    else:
                        return_s += '<p>&nbsp;</p>\n'
                elif inParaNow():
                    # text is a continuation of a previously started paragraph
                    return_s += line
                    return_s += applyStyles(True)
                    return_s += '</p>\n'
                    j = len(in_tags)
                    del in_tags[j-1]
                else:
                    if len(line) > 0:
                        return_s += line + '<br />\n'
                    else:
                        return_s += '<br />\n'
                lp = s.find('\n')
            linefrag = s
            if len(linefrag) > 0:
                if not inBlock() and not inLink() and not inComment():
                    nb, linefrag = indentLevel(linefrag)
                    return_s += '<p class="i%d">' % nb
                    return_s += applyStyles(False)
                    return_s += linefrag
                    ppair = ('P', None)
                    in_tags.append(ppair)
                else:
                    return_s += linefrag
            return return_s

        while True:
            r = self.next()
            if not r:
                break
            text, cmd, attr = r

            if text:
                final += makeText(text)

            if cmd:

                # handle pseudo paragraph P tags
                # close if starting a new block element
                if cmd in self.html_block_tags or cmd == 'w':
                    j = len(in_tags)
                    if j > 0:
                        if in_tags[j-1][0] == 'P':
                            final += applyStyles(True)
                            final += getTag(in_tags[j-1],True)
                            del in_tags[j-1]

                if cmd in self.html_block_tags:
                    pair = (cmd, attr)
                    if cmd not in [a for (a,b) in in_tags]:
                        # starting a new block tag
                        final += getTag(pair, False)                  
                        final += applyStyles(False)
                        in_tags.append(pair)
                    else:
                        # process ending tag for a tag pair
                        # ending tag should be for the most recently added start tag 
                        j = len(in_tags)
                        if cmd == in_tags[j-1][0]:
                            final += applyStyles(True)
                            final += getTag(in_tags[j-1], True)
                            del in_tags[j-1]
                        else:
                            # ow: things are not properly nested
                            # process ending tag for block
                            # ending tag **should** be for the most recently added block tag
                            # but in too many cases it is not so we must fix this by
                            # closing all open tags up to the current one and then
                            # reopen all of the tags we had to close due to improper nesting of styles
                            print 'Warning: Improperly Nested Block Tags: expected %s found %s' % (cmd, in_tags[j-1][0])
                            print 'after processing %s' % final[-40:]
                            j = len(in_tags)
                            while True:
                                j = j - 1
                                final += applyStyles(True)
                                final += getTag(in_tags[j], True)
                                if in_tags[j][0] == cmd:
                                    break
                            del in_tags[j]
                            # now create new block start tags if they were previously open
                            while j < len(st_tags):
                                final += getTag(in_tags[j], False)
                                final += applyStyles(False)
                                j = j + 1
                        self.skipNewLine()

                elif cmd in self.html_link_tags:
                    pair = (cmd, attr)
                    if cmd not in [a for (a,b) in in_tags]:
                        # starting a new link tag
                        # first close out any still open styles
                        if inBlock():
                            final += applyStyles(True)
                        # output start tag and styles needed
                        final += getTag(pair, False)
                        final += applyStyles(False)
                        in_tags.append(pair)
                    else:
                        # process ending tag for a tag pair
                        # ending tag should be for the most recently added start tag 
                        j = len(in_tags)
                        if cmd == in_tags[j-1][0]:
                            j = len(in_tags)
                            # apply closing styles and tag
                            final += applyStyles(True)
                            final += getTag(in_tags[j-1], True)
                            # if needed reopen any style tags
                            if inBlock():
                                final += applyStyles(False)
                            del in_tags[j-1]
                        else:
                            # ow: things are not properly nested
                            print 'Error: Improperly Nested Link Tags: expected %s found %s' % (cmd, in_tags[j-1][0])
                            print 'after processing %s' % final[-40:]

                elif cmd in self.html_style_tags:
                    spair = (cmd, attr)
                    if cmd not in [a for (a,b) in st_tags]:
                        # starting a new style
                        if inBlock() or inLink():
                            final += getSTag(spair,False)
                        st_tags.append(spair)
                    else:
                        # process ending tag for style
                        # ending tag **should** be for the most recently added style tag
                        # but in too many cases it is not so we must fix this by
                        # closing all open tags up to the current one and then
                        # reopen all of the tags we had to close due to improper nesting of styles
                        j = len(st_tags)
                        while True:
                            j = j - 1
                            if inBlock() or inLink():
                                final += getSTag(st_tags[j], True)
                            if st_tags[j][0] == cmd:
                                break
                        del st_tags[j]
                        # now create new style start tags if they were previously open
                        while j < len(st_tags):
                            if inBlock() or inLink():
                                final += getSTag(st_tags[j], False)
                            j = j + 1

                elif cmd in self.html_one_tags:
                    final += self.html_one_tags[cmd]

                elif cmd == 'p':
                    # create page breaks at the <body> level so
                    # they can be easily used for safe html file segmentation breakpoints
                    # first close any open tags
                    j = len(in_tags)
                    if j > 0:
                        while True:
                            j = j - 1
                            if in_tags[j][0] in self.html_block_tags:
                                final += applyStyles(True)
                            final += getTag(in_tags[j], True)
                            if j == 0:
                                break

                    # insert the page break tag
                    final += '\n<div class="breakafter"></div>\n'

                    if sigil_breaks:
                        if (len(final) - lastbreaksize) > 3000:
                            final += '<hr class="sigilChapterBreak" />\n'
                            lastbreaksize = len(final)

                    # now create new start tags for all tags that 
                    # were previously open
                    while j < len(in_tags):
                        final += getTag(in_tags[j], False)
                        if in_tags[j][0] in self.html_block_tags:
                            final += applyStyles(False)
                        j = j + 1
                    self.skipNewLine()

                elif cmd[0:1] == 'C':
                    if self.markChapters:
                        # create toc entries at the <body> level
                        # since they will be in an invisible block
                        # first close any open tags
                        j = len(in_tags)
                        if j > 0:
                            while True:
                                j = j - 1
                                if in_tags[j][0] in self.html_block_tags:
                                    final += applyStyles(True)
                                final += getTag(in_tags[j], True)
                                if j == 0:
                                    break
                        level = int(cmd[1:2]) + 1
                        final += '<h%d title="%s"></h%d>' % (level, attr, level)
                        # now create new start tags for all tags that 
                        # were previously open
                        while j < len(in_tags):
                            final += getTag(in_tags[j], False)
                            if in_tags[j][0] in self.html_block_tags:
                                final += applyStyles(False)
                            j = j + 1
                    else:
                        final += '<!-- ToC%s: %s -->' % (cmd[1:2], attr)

                # now handle single tags (non-paired) that have attributes
                elif cmd == 'm':
                    unquotedimagepath = bookname + '_img/' + attr
                    imagepath = urllib.quote( unquotedimagepath )
                    final += '<img src="%s" alt="" />' % imagepath

                elif cmd == 'Q':
                    final += '<span id="%s"> </span>' % attr

                elif cmd == 'a':
                    if not inBlock() and not inLink() and not inComment():
                        final += '<p class="i0">'
                        final += applyStyles(False)
                        final += self.pml_chars.get(attr, '&#%d;' % attr)
                        ppair = ('P', None)
                        in_tags.append(ppair)
                    else:
                        final += self.pml_chars.get(attr, '&#%d;' % attr)

                elif cmd == 'U':
                    if not inBlock() and not inLink() and not inComment():
                        final += '<p class="i0">'
                        final += applyStyles(False)
                        final += '&#%d;' % attr
                        ppair = ('P', None)
                        in_tags.append(ppair)
                    else:
                        final += makeText('&#%d;' % attr)

                elif cmd == 'w':
                    # hr width and align parameters are not allowed in strict xhtml but style widths are possible 
                    final += '\n<hr style="width: %s;" />' % attr
                    # final += '<div style="width: %s; margin-left: auto; margin-right: auto;  \
                    #  border-top-style: solid; border-top-color: grey; border-top-width: thin;">&nbsp;</div>' % attr
                    self.skipNewLine()

                elif cmd == 'T':
                    if inBlock() or inLink() or inComment():
                        final += '<span style="margin-left: %s;">&nbsp;</span>' % attr
                    else:
                        final += '<p style="text-indent: %s;">' % attr
                        final += applyStyles(False)
                        ppair = ('P', None)
                        in_tags.append(ppair)

                else:
                    logging.warning("Unknown tag: %s-%s", cmd, attr)


        # handle file ending condition for imputed P tags 
        j = len(in_tags)
        if (j > 0):
            if in_tags[j-1][0] == 'P':
                final += '</p>'

        final += '</body>\n</html>\n'

        # recode html back to a single slash
        final = final.replace('_amp#92_', '\\')

        # cleanup the html code for issues specifically generated by this translation process
        # ending divs already break the line at the end so we don't need the <br /> we added
        final = final.replace('</div><br />\n','</div>\n')

        # clean up empty elements that can be created when fixing improperly nested pml tags
        # and by moving page break tags to the body level so that they can be used as  html file split points
        while True:
            s = final
            final = final.replace('<b></b>','')
            final = final.replace('<i></i>','')
            final = final.replace('<del></del>','')
            final = final.replace('<sup></sup>','')
            final = final.replace('<sub></sub>','')
            final = final.replace('<span class="under"></span>','')
            final = final.replace('<span class="big"></span>','')
            final = final.replace('<span class="smallcaps"></span>','')
            final = final.replace('<span class="under"> </span>','')
            final = final.replace('<span class="big"> </span>','')
            final = final.replace('<span class="smallcaps"> </span>','')
            final = final.replace('<p></p>','')
            final = final.replace('<p> </p>','')
            final = final.replace('<p class="i0"></p>','')
            final = final.replace('<p class="i1"></p>','')
            final = final.replace('<p class="i2"></p>','')
            final = final.replace('<p class="i3"></p>','')
            final = final.replace('<p class="i4"></p>','')
            final = final.replace('<p class="i5"></p>','')
            final = final.replace('<h1></h1>\n','')
            final = final.replace('<h2></h2>\n','')
            final = final.replace('<h3></h3>\n','')
            final = final.replace('<h4></h4>\n','')
            final = final.replace('<h5></h5>\n','')
            final = final.replace('<div class="center"></div>\n','')
            final = final.replace('<div class="hang"></div>\n','')
            final = final.replace('<div class="indent"></div>\n','')
            final = final.replace('<div class="right"></div>\n','')
            if s == final:
               break
        return final


def tidy(rawhtmlfile):
    # processes rawhtmlfile through command line tidy via pipes 
    rawfobj = file(rawhtmlfile,'rb')
    # --doctype strict forces strict dtd checking
    # --enclose-text yes - enclosees non-block electment text inside <body></body> into its own <p></p> block to meet xhtml spec
    # -w 100 -i will wrap text at column 120 and indent it to indicate level of nesting to make structure clearer
    # -win1252 sets the input encoding of pml files
    # -asxhtml convert to xhtml
    # -q (quiet)
    cmdline = 'tidy -w 120 -i -q -asxhtml -win1252  --enclose-text yes --doctype strict '
    if sys.platform[0:3] == 'win':
        cmdline = 'tidy.exe -w 120 -i -q -asxhtml -win1252  --enclose-text yes --doctype strict '
    p2 = Popen(cmdline, shell=True, stdin=rawfobj, stdout=PIPE, stderr=PIPE, close_fds=False)
    stdout, stderr = p2.communicate()
    # print "Tidy Original Conversion Warnings and Errors" 
    # print stderr
    return stdout

def usage():
    print "Converts PML file to XHTML"
    print "Usage:"
    print "  xpml2xhtml [options] infile.pml outfile.html "
    print " "
    print "Options: "
    print "  -h                prints this message"
    print "  --sigil-breaks    insert Sigil Chapterbbreaks"
    print "  --use-tidy        use tidy to further clean up the html "
    print " "
    return

def main(argv=None):
    global bookname
    global footnote_ids
    global sidebar_ids
    global sigil_breaks
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["sigil-breaks", "use-tidy"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        return 1
    if len(args) != 2:
        usage()
        return 1
    sigil_breaks = False
    use_tidy = False
    for o, a in opts:
        if o == "-h":
            usage()
            return 0
        elif o == "--sigil-breaks":
            sigil_breaks = True
        elif o == "--use-tidy":
            use_tidy = True
    infile, outfile = args[0], args[1]
    bookname = os.path.splitext(os.path.basename(infile))[0]
    footnote_ids = { }
    sidebar_ids = { }
    try:
        print "Processing..."
        import time
        start_time = time.time()
        print "   Converting pml to raw html"
        pml_string = file(infile,'rb').read()
        pml = PmlConverter(pml_string)
        html_src = pml.process()
        if use_tidy:
            print "   Tidying html to xhtml"
            fobj = tempfile.NamedTemporaryFile(mode='w+b',suffix=".html",delete=False)
            tempname = fobj.name
            fobj.write(html_src)
            fobj.close()
            html_src = tidy(tempname)
            os.remove(tempname)
        file(outfile,'wb').write(html_src)
        end_time = time.time()
        convert_time = end_time - start_time
        print 'elapsed time: %.2f seconds' % (convert_time, ) 
        print 'output is in file %s' % outfile
        print "Finished Processing"
    except ValueError, e:
        print "Error: %s" % e
        return 1
    return 0

if __name__ == "__main__":
    #import cProfile
    #command = """sys.exit(main())"""
    #cProfile.runctx( command, globals(), locals(), filename="cprofile.profile" )
    
    sys.exit(main())
