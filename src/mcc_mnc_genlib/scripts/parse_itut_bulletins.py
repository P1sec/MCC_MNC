#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# /**
# * Software Name : MCC_MNC
# * Version : 0.1
# *
# * Copyright 2020. Benoit Michau. P1 Security.
# *
# * This program is free software: you can redistribute it and/or modify
# * it under the terms of the GNU Affero General Public License as
# * published by the Free Software Foundation, either version 3 of the
# * License, or (at your option) any later version.
# *
# * This program is distributed in the hope that it will be useful,
# * but WITHOUT ANY WARRANTY; without even the implied warranty of
# * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# * GNU Affero General Public License for more details.
# *
# * You should have received a copy of the GNU Affero General Public License
# * along with this program.  If not, see <https://www.gnu.org/licenses/>.
# *
# *--------------------------------------------------------
# * File Name : parse_itut_bulletins.py
# * Created : 2020-09-14
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


from os.path import dirname, realpath, join
import sys
import os
import argparse
import urllib.request
import urllib.error
import subprocess
import time
import re

from mcc_mnc_genlib.scripts.parse_wikipedia_tables import (
    generate_json,
    generate_python,
    )


SCRIPT_DIR = dirname(realpath(__file__))
MODULE_DIR = dirname(realpath(SCRIPT_DIR))
SRC_DIR = dirname(realpath(MODULE_DIR))
ROOT_DIR = dirname(realpath(SRC_DIR))
DATA_DIR = join(ROOT_DIR, 'data')

PATH_RAW = join(MODULE_DIR, 'raw', '')

#------------------------------------------------------------------------------#
# download ITU-T operational bulletins
#------------------------------------------------------------------------------#

"""
download ITU-T bulletins in PDF format,
starting from the 1111 in 2016 (bulletin with an official complete list of MNCs),
and all bulletins onwards.

1st bulletin of 2017 is 1115
23 or 24 bulletins are edited each month
URL examples:
- https://www.itu.int/dms_pub/itu-t/opb/sp/T-SP-OB.1111-2016-OAS-PDF-E.pdf
- https://www.itu.int/dms_pub/itu-t/opb/sp/T-SP-OB.1115-2017-OAS-PDF-E.pdf
"""

# ITU-T website url prefix
ITUT_BULL_URL_PREF = 'https://www.itu.int/dms_pub/itu-t/opb/sp/'
# directory to store all ITU-T bulletins
PATH_PRE = join(DATA_DIR, 'itut', '')
# command to convert them to text file
PDFTOTXT = ['pdftotext', '-layout', '-nopgbrk']

BULL_FREQ = {
    2010 : list(range(947, 971)),
    2011 : list(range(971, 995)),
    2012 : list(range(995, 1018)),
    2013 : list(range(1018, 1042)),
    2014 : list(range(1042, 1067)),
    2015 : list(range(1067, 1091)),
    2016 : list(range(1091, 1114)),
    2017 : list(range(1114, 1139)),
    2018 : list(range(1139, 1163)),
    2019 : list(range(1163, 1187)),
    2020 : list(range(1187, 1211)),
    2021 : list(range(1211, 1235)),
    2022 : list(range(1235, 1259)),
    2023 : list(range(1259, 1283)),
    }


def strip_footer(fn, dbg=True):
    lines = []
    with open(fn, encoding='utf-8') as fd:
        bnum = fn.split('.')[1].split('-')[0]
        re1  = re.compile(r'No\. %s\s{0,}–\s{0,}[0-9]{1,}' % bnum)
        re2  = re.compile(r'Annex to ITU OB %s-E\s{0,}–\s{0,}[0-9]{1,}' % bnum)
        for line in fd.readlines():
            # starts or ends with:  No. 1111 – $page_number
            # Annex to ITU OB 1111-E
            if re1.search(line) or re2.search(line):
                if dbg:
                    print('> stripping footer: %s' % line.strip())
                continue
            lines.append(line)
    #
    # rewrite the file
    with open(fn, 'w', encoding='utf-8') as fd:
        fd.write(''.join(lines))


def dl_bull(bnum=1111, byear=2016, dbg=True, rmpdf=True):
    """try to download an ITU-T bulletin with the given bulletin number `bnum'
    from the given year `byear'
    """
    fn  = 'T-SP-OB.%i-%i-OAS-PDF-E.pdf' % (bnum, byear)
    url = ITUT_BULL_URL_PREF + fn
    try:
        resp = urllib.request.urlopen(url)
    except urllib.error.HTTPError as err:
        if dbg:
            print('> unable to download bulletin %.4i for year %.4i' % (bnum, byear))
        fnsub = 'T-SP-OB.%i-%i-PDF-E.pdf' % (bnum, byear)
        url   = ITUT_BULL_URL_PREF + fnsub
        try:
            resp = urllib.request.urlopen(url)
        except urllib.error.HTTPError as err:
            return False
    #
    if resp.code != 200:
        raise(Exception('resource %s not available, HTTP code %i' % (url, resp.code)))
    #
    with open(PATH_PRE + fn, 'wb') as fd:
        fd.write(resp.read())
        if dbg:
            print('> downloaded %s into %s' % (fn, PATH_PRE))
        # convert it into a txt file
        conv = subprocess.Popen(PDFTOTXT + [PATH_PRE + fn], )
        err  = conv.wait()
        if dbg:
            if err:
                # error
                print('> unable to convert pdf to text ; error %i' % err)
            else:
                print('> converted pdf to text file %s.txt' % fn[:-3])
        #
        if not err:
            # strip header line into the txt file
            strip_footer(PATH_PRE + fn[:-3] + 'txt', dbg=dbg)
        #
        if rmpdf:
            os.remove(PATH_PRE + fn)
        #
        return True
    #
    raise(Exception('unable to write local file %s' % (PATH_PRE + fn, )))


def dl_bull_all(bnum=1111, dbg=False):
    """download all ITU-T bulletins starting from bulletin 1111 in 2016 in PDF
    format and convert them to text files
    """
    # start with bulletin 1111 from 2016
    byear = 2016
    #
    while byear <= time.gmtime().tm_year:
        if dl_bull(bnum, byear, dbg=dbg):
            print('[+] downloaded PDF bulletin %i from year %i and converted to text' % (bnum, byear))
            bnum += 1
        else:
            byear += 1
    

def strip_all_txt(dbg=True):
    fns = os.listdir(PATH_PRE)
    for fn in fns:
        if fn[-4:] == '.txt':
            print('[+] stripping %s' % fn)
            strip_footer(PATH_PRE + fn, dbg=dbg)


#------------------------------------------------------------------------------#
# parse MNC list
#------------------------------------------------------------------------------#

"""
Bulletins 1111 (2016) and 1162 (2018) contain both the complete list of updated 
MCC-MNC per country.
The following script extract this list from both bulletins. 
"""

# to extract the list
RE_MNC_LIST_BEG     = re.compile(
    r'\nMobile Network Codes \(MNC\) under geographic Mobile Country Codes \(MCC\)\n',
    re.IGNORECASE
    )

RE_MNC_LIST_END     = re.compile(
    r'(\n____________\n\*       MCC: Mobile Country Code /)|'\
    r'(\nShared Mobile Country Codes \(MCC\) for networks and their respective Mobile Network\nCodes \(MNC\)\n)',
    re.IGNORECASE
    )


def parse_mnc_list(fn=PATH_PRE+'T-SP-OB.1162-2018-OAS-PDF-E.txt', dbg=False):
    with open(fn, encoding='utf-8') as fd:
        txt = fd.read()
        #
        # keep only the list of MCC-MNC
        beg = RE_MNC_LIST_BEG.search(txt)
        end = RE_MNC_LIST_END.search(txt)
        if not beg or not end:
            print('> no MNC list found')
            return None
        txt = txt[beg.end():end.start()].strip()
        #
        return parse_mnc_lines([l.rstrip() for l in txt.split('\n') if l.strip()], dbg)
    #
    return None


# Some table titles and a comment on Kosovo need to be stripped properly

RE_MNC_LINE_IGNORE  = re.compile(
    r'(Country or)|'\
    r'(Geographical Area\s{1,}Networks\s{1,}MCC \+ MNC codes)|'\
    r'(\*This designation is without prejudice to positions on status, and is in line with UNSCR 1244 and the ICJ Opinion on the Kosovo)|'\
    r'(declaration of independence.)$',
    re.IGNORECASE
    )


# Country declaration:
#
# Country names are always starting a line
# Most are alone on a single line
# But few are on 2 lines, followed by an MNO declaration on the 2nd line
#
# Need to hardcode those multiline country names 
# for proper distinction between country name and MNO

COUNTRY_MULT = [
    'French Departments and Territories in the Indian Ocean',
    'Saint Helena, Ascension and Tristan da Cunha',
    'Saint Vincent and the Grenadines',
    'The Former Yugoslav Republic of Macedonia',
    'Venezuela (Bolivarian Republic of)',
    ]

RE_COUNTRY      = re.compile(r'\w.*$')


# MNO declaration:
#
# pattern 1:
#    MNO desc       MCC-MNC
#
# pattern 2 (see e.g. Belarus):
#    MNO desc start
#    [MNO desc cont]
#                   MCC-MNC
#    [MNO desc cont]
#    MNO desc end
#
# pattern 3 (see e.g. Mexico):
#    MNO desc start
#    [MNO desc cont]
#    MNO desc cont  MCC-MNC
#    [MNO desc cont]
#    MNO desc end

RE_MNC          = re.compile(r'\s{24,}(.*?)([0-9]{3} [0-9]{2,3})$')
RE_DESC         = re.compile(r'\s{24,}(.*)$')


def parse_mnc_lines(lines, dbg=True):
    #
    R    = {}
    mnos = []
    mno  = []
    mnc  = ''
    cntr = ''
    cntr_mult = 0
    #
    for line in lines:
        if RE_MNC_LINE_IGNORE.match(line):
            continue
        #
        if dbg:
            print(line)
        #
        m = RE_COUNTRY.match(line)
        if m:
            _cntr = m.group()
            if cntr:
                if mnos:
                    # starting with a new country
                    # store the last one and its MNOs into the dict
                    R[cntr] = mnos
                    mnos    = []
                    mno     = []
                    mnc     = ''
                    cntr    = ''
                #
                _cntr_full = _get_cntr_mult(_cntr)
                if _cntr_full:
                    # 1st line of a multiline country name
                    cntr_mult = len(_cntr_full) - len(_cntr) - 1
                    assert( cntr_mult > 1 )
                    cntr = _cntr_full
                elif cntr_mult:
                    # 2nd line of a multiline country name
                    assert( not mno )
                    line = line[cntr_mult:]
                    cntr_mult = 0
                    assert( line[0:1] == ' ' )
                    line = 24 * ' ' + line
                    mnc = _parse_mnc_line(line, mnos, mno, mnc)
                else:
                    # single line country name
                    cntr = _cntr
            else:
                # 1st country of the list
                cntr = _cntr
        #
        else:
            mnc = _parse_mnc_line(line, mnos, mno, mnc)
    #
    assert( cntr and mnos )
    R[cntr] = mnos
    #
    return R


def _get_cntr_mult(name):
    for cntr in COUNTRY_MULT:
        if cntr.startswith(name):
            return cntr
    return ''


def _parse_mnc_line(line, mnos, mno, mnc):
    m = RE_MNC.match(line)
    if m:
        _mno, mnc = m.groups()
        _mno = _mno.strip()
        if _mno:
            if mno:
                # 3 or more lines declaration
                mno.append(_mno)
                mno.extend( [None]*(len(mno)-1) )
            else:
                # 1 line declaration
                assert( not mno )
                mnos.append( (_mno, mnc.replace(' ', '')) )
                mnc = ''
        else:
            # 3 or more lines declaration
            assert( mno )
            mno.extend( [None]*len(mno) )
        return mnc
    #
    m = RE_DESC.match(line)
    if m:
        _mno = m.group()
        _mno = _mno.strip()
        assert(_mno)
        if mno and mno[-1] is None:
            # one of the last line of a 3 lines or more declaration
            ind = mno.index(None)
            del mno[ind]
            mno.insert(ind, _mno)
            if mno[-1] is not None:
                # declaration completed
                mnos.append( (' '.join(mno), mnc.replace(' ', '')) )
                mno.clear()
                mnc = ''
        else:
            # one of the 1st line of a 3 lines or more declaration
            mno.append(_mno)
        return mnc
    #
    assert()


#------------------------------------------------------------------------------#
# parse MNC updates
#------------------------------------------------------------------------------#

"""
Regular MNC updates are available in bulletins
We extract them in order to update the database established from bulletins 1162 onward
The following script check within a bulletin if MNC updates are provided

We keep track of all information, whatever rule applies to it (ADD, SUP or LIR)
We don't try to get the country name, as we will match with the MCC afterwards
"""

# The list starts with a line like this
#Country/Geographical area            MCC+MNC           Operator/Network
# And ends with a line of underscores
#____________

RE_MNC_UPD_LIST_BEG     = re.compile(
    r' {0,}Country/Geographical area {1,}MCC\+MNC {0,}\*{0,1} {1,}Operator/Network',
    re.IGNORECASE
    )
RE_MNC_UPD_LIST_END     = re.compile(r' {0,}_{5,} {0,}', re.IGNORECASE)
RE_MNC_UPD_LIST_ENDALT  = re.compile(r'Extra-territorial use\*{3,}', re.IGNORECASE)
RE_MNC_UPD_MNC          = re.compile(r' {7,}([0-9]{3}) ([0-9]{2,3})(?:$|\s{1,})')
RE_MNC_UPD_MNO          = re.compile(r' {20,}(\S.{3,}) {0,}$')
RE_MNC_UPD_RULE         = re.compile(r'(?:^| )(ADD|SUP|LIR)(?: {0,1}\*{0,1})')


# this is for dropping crappy lines from crappy formed bulletins
MNC_UPD_LINEDROP        = [
    ('startswith', 'Country/Geographical area'),
    ('endswith',   'No. 1210 – 21'),
    ('endswith',   'Operator/Network'),
    ]


def parse_mnc_upd_list(fn=PATH_PRE+'T-SP-OB.1258-2022-OAS-PDF-E.txt', dbg=False):
    with open(fn, encoding='utf-8') as fd:
        txt = fd.read()
        #
        # keep only potential update of MNC
        beg = RE_MNC_UPD_LIST_BEG.search(txt)
        if not beg:
            if dbg:
                print('> %s: MNC update list not found, beg' % fn)
            return None
        txt = txt[beg.end():].strip()
        end = RE_MNC_UPD_LIST_END.search(txt)
        if not end:
            if dbg:
                print('> %s: MNC update list not found, end' % fn)
            return None
        # check if need to remove some crappy declaration at the end
        endalt = RE_MNC_UPD_LIST_ENDALT.search(txt)
        if endalt and endalt.start() < end.start():
            txt = txt[:endalt.start()].strip()
        else:
            txt = txt[:end.start()].strip()
        if dbg:
            print('> %s: MNC update list found' % fn)
        #
        mncdecl = []
        for line in txt.split('\n'):
            if not line.strip():
                continue
            line = line.rstrip()
            ins  = True
            for drop_meth, drop_expr in MNC_UPD_LINEDROP:
                if getattr(line, drop_meth)(drop_expr):
                    if dbg:
                        print('>>> %s: dropping %r' % (fn, line))
                    ins = False
                    break
            if ins:
                mncdecl.append(line)
        #
        mnclut = parse_mnc_upd_lines(mncdecl, dbg)
        if dbg:
            print('> %s: %i MNC records' % (fn, len(mnclut)))
        return mnclut

# We have 1 or 2 lines with country name and type of update
# ADD (addition), SUP (suppress), LIR (update)

# Then a list of MNO patterns
#
# pattern 1:
#   MCC MNC         MNO compl
#
# pattern 2:
#                   MNO start
#   MCC MNC
#                   MNO stop
#
# pattern 3:
#   MCC MNC         MNO start
#                   MNO stop
#
# and exceptionnally pattern 4:
#                   MNO start
#   MCC MNC         MNO cont
#                   MNO stop

def parse_mnc_upd_lines(lines, dbg=True):
    #
    #print('\n'.join(lines))
    #return
    #
    mnclut, mnclist, rest = {}, [], []
    cntr, rule, mnc, mno, mnc_empt = '', '', '', '', False
    #
    for line in lines:
        m = RE_MNC_UPD_RULE.search(line)
        if m:
            if mnclist: 
                mnclut.update(_mnclist_to_mnclut(cntr, rule, mnclist, dbg))
                rule = ''
            rest.append(line[:m.start()])
            rule = m.group(1) 
            cntr = str.strip(' '.join(map(str.strip, rest)))
            rest.clear()
            line = line[m.end():]
            if dbg:
                print('>>> rule: %s %s' % (cntr, rule))
        #
        m = RE_MNC_UPD_MNC.search(line)
        if m:
            assert( rule and cntr )
            mnc = m.group(1) + m.group(2)
            rem = line[m.end():].strip() 
            if rem:
                #    pat 1, MNO compl
                # or pat 3, MNO start
                mnclist.append((mnc, [rem]))
                mnc_empt = False
            else:
                # pat 2, MNC only
                if not mnclist:
                    if dbg:
                        print('>>> buggy MNC declaration: %r' % line)
                else:
                    mnclist.append((mnc, [mnclist[-1][1].pop()]))
                mnc_empt = True
        else:
            m = RE_MNC_UPD_MNO.search(line)
            if m:
                assert( cntr and rule )
                if mnc_empt:
                    # pat 2, MNO stop
                    if not mnclist:
                        if dbg:
                            print('>>> buggy MNC declaration: %r' % line)
                    else:
                        mnclist[-1][1].append(m.group(1).strip())
                else:
                    #    pat 2, MNO start
                    # or pat 3, MNO stop
                    if mnclist:
                        mnclist[-1][1].append(m.group(1).strip())
                    else:
                        mnclist.append(('', [m.group(1).strip()]))
            else:
                # end of the list of MNC, but no rule yet
                if mnclist: 
                    mnclut.update(_mnclist_to_mnclut(cntr, rule, mnclist, dbg))
                    rule = ''
                rest.append(line)
            mnc_empt = False
    if mnclist:
        mnclut.update(_mnclist_to_mnclut(cntr, rule, mnclist, dbg))
    return mnclut


def _mnclist_to_mnclut(cntr, rule, mnclist, dbg):
    mnclut = {}
    for i, (mnc, mno_its) in enumerate(mnclist):
        if not mnc:
            if mno_its:
                if len(mnclist) > 1:
                    # exceptional pat 4, MNO start
                    if dbg:
                        print('>>> splitted MNO description: %r, %r' % (mnclist[i], mnclist[i+1]))
                    assert(len(mno_its) == 1)
                    mnclist[i+1][1].insert(0, mno_its[0])
                else:
                    if dbg:
                        print('>>> buggy MNC collection: %r' % mno_its)
            continue
        mnclut[mnc] = (' '.join(mno_its), cntr, rule)
    mnclist.clear()
    return mnclut


def parse_mnc_incr(start=1163, fnpre=PATH_PRE, dbg=False):
    mncd = {}
    for fn in sorted(os.listdir(fnpre)):
        if not fn.startswith('T-SP-OB.'):
            continue
        elif int(fn[8:12]) < start:
            continue
        mnclut = parse_mnc_upd_list(fnpre + fn, dbg=dbg)
        if not mnclut:
            continue
        for mnc, (mno, cntr, rule) in mnclut.items():
            cntr = re.sub(r'\s{1,}', ' ', cntr)
            if cntr not in mncd:
                mncd[cntr] = [[mno, mnc, rule]]
            else:
                mncd[cntr].append([mno, mnc, rule])
    return mncd


#------------------------------------------------------------------------------#
# parse SANC list
#------------------------------------------------------------------------------#

"""
Bulletin 1125 (2017) contains the complete list of Signaling Area Network Code
per country.
The following script extract this list from the bulletin. 
"""

RE_SANC_LIST_BEG    = re.compile(
    r'\n\s{1,}List of Signalling Area/Network Codes \(SANC\)'\
    r'\n\s{1,}\(Complement to Recommendation ITU-T Q\.708 \(03/99\)\)'\
    r'\n\s{1,}\(Position on 1 June 2017\)\n'\
    r'\n\s{1,}\(Annex to ITU Operational Bulletin No\. 1125 - 1\.VI\.2017\)\n',
    re.IGNORECASE)


RE_SANC_LIST_END    = re.compile(
    r'\n\s{1,}Code\s{1,}Geographical Area or Signalling Network\s{1,}–\s{1,}alphabetical order\n',
    re.IGNORECASE)


def parse_sanc_list(fn=PATH_PRE+'T-SP-OB.1125-2017-OAS-PDF-E.txt', dbg=False):
    with open(fn, encoding='utf-8') as fd:
        txt = fd.read()
        #
        # keep only the list of SPC
        beg = RE_SANC_LIST_BEG.search(txt)
        if not beg:
            print('> no SANC list found, beg')
            return None
        txt = txt[beg.end():].strip()
        end = RE_SANC_LIST_END.search(txt)
        if not end:
            print('> no SANC list found, end')
            return None
        txt = txt[:end.start()].strip()
        #
        return parse_sanc_lines([l.strip() for l in txt.split('\n') if l.strip()], dbg)
    #
    return None


# Some table titles need to be stripped properly

RE_SANC_LINE_IGNORE  = re.compile(
    r'Code\s{1,}Geographical Area or Signalling Network\s{1,}–\s{1,}numerical order\s{0,}',
    re.IGNORECASE
    )

# SANC declaration:
#  SANC country
#
# SANC: W-XYZ digits
# 
RE_SANC = re.compile(
    r'([0-9]-[0-9]{3})\s{1,}(.*)',
    re.IGNORECASE
    )


def parse_sanc_lines(lines, dbg=True):
    R       = {}
    #
    for line in lines:
        if RE_SANC_LINE_IGNORE.match(line):
            continue
        #
        if dbg:
            print(line)
        #
        m = RE_SANC.match(line)
        if m:
            sanc, cntr = m.groups()
            assert( sanc not in R )
            R[sanc] = cntr
        else:
            assert( len(line) == 0 )
    #
    return R


#------------------------------------------------------------------------------#
# parse SPC list
#------------------------------------------------------------------------------#

"""
Bulletin 1199 (2020) contains the complete list of International Signaling Point
Codes per country.
The following script extract this list from the bulletin. 
"""

# to extract the list
RE_SPC_LIST_BEG     = re.compile(
    r'\n\s{1,}List of International Signalling Point Codes \(ISPC\) for signalling system No\. 7'\
    r'\n\s{1,}\(According to Recommendation ITU-T Q\.708 \(03/99\)\)\n',
    re.IGNORECASE
    )


RE_SPC_LIST_END     = re.compile(
    r'\n____________\nISPC:\s{1,}International Signalling Point Codes\.\n',
    re.IGNORECASE
    )


def parse_spc_list(fn=PATH_PRE+'T-SP-OB.1199-2020-OAS-PDF-E.txt', dbg=False):
    with open(fn, encoding='utf-8') as fd:
        txt = fd.read()
        #
        # keep only the list of SPC
        beg = RE_SPC_LIST_BEG.search(txt)
        if not beg:
            print('> no SPC list found, beg')
            return None
        txt = txt[beg.end():].strip()
        end = RE_SPC_LIST_END.search(txt)
        if not end:
            print('> no SPC list found, end')
            return None
        txt = txt[:end.start()].strip()
        #
        return parse_spc_lines([l[1:].rstrip() for l in txt.split('\n') if l.strip()], dbg)
    #
    return None


# Some table titles need to be stripped properly

RE_SPC_LINE_IGNORE  = re.compile(
    r'(\s{0,}Country/)|'\
    r'(\s{0,}Geographical Area)|'\
    r'(\s{0,}ISPC\s{1,}DEC\s{1,}Unique name of the signalling point\s{1,}Name of the signalling point operator)|'\
    r'(\s{0,}This designation is without prejudice to positions on status, and is in line with UNSCR 1244 and the ICJ Opinion on the Kosovo)|'\
    r'(declaration of independence.)$',
    re.IGNORECASE
    )


# Country declaration:
#
# Country names are always on a single line

# SPC declaration:
#    ISPC DEC name_spc name_ope
#
# name_spc or name_ope may be splitted on multiple lines

RE_ISPC         = re.compile(r'[0-9]\-[0-9]{3}\-[0-9]')


def parse_spc_lines(lines, dbg=True):
    R       = {}
    cntr    = ''
    spcs    = []
    #
    for line in lines:
        if RE_SPC_LINE_IGNORE.match(line):
            continue
        #
        if dbg:
            print(line)
        #
        m = RE_COUNTRY.match(line)
        if m and not line[0:1].isdigit():
            # country name
            if cntr and spcs:
                R[cntr] = spcs
                cntr = ''
                spcs = []
            #
            cntr = m.group()
            continue
        #
        m = RE_ISPC.match(line)
        if m:
            # SPC
            spc  = m.group()
            line = line[m.end():].lstrip()
            m    = re.match('[1-9]{1}[0-9]{0,}', line)
            assert(m)
            dec  = m.group()
            line = line[m.end():]
            if line.startswith(12 * ' '):
                # no SPC_name
                name_spc = ''
                name_ope = line.strip()
            else:
                name_spc, name_ope = map(str.strip, re.split(r'\s{2,}', line.strip()))
                if name_spc in ('\u2026', ):
                    name_spc = ''
            spcs.append([spc, dec, name_spc, name_ope])
            continue
        #
        if line.startswith(65 * ' '):
            # name_ope continuation
            assert(spcs)
            line = line.lstrip()
            spcs[-1][3] += ' %s' % line.rstrip()
            continue
        #
        if line.startswith(20 * ' '):
            # name_spc continuation
            assert(spcs)
            line = line.lstrip()
            if '  ' in line:
                name_spc, name_ope = map(str.strip, re.split(r'\s{2,}', line.strip()))
                spcs[-1][2] += ' %s' % name_spc
                spcs[-1][3] += ' %s' % name_ope
            else:
                spcs[-1][2] += ' %s' % line.rstrip()
            continue
        
        assert()
    #
    R[cntr] = spcs
    return R


#------------------------------------------------------------------------------#
# main
#------------------------------------------------------------------------------#

URL_LICENSE_ITUT = 'https://www.itu.int/pub/T-SP'


def main():
    parser = argparse.ArgumentParser(description=
        'download ITU-T operational bulletins, convert them to text, extract lists of MNC and SPC')
    parser.add_argument('-d', action='store_true', help='download and convert from pdf to text all ITU-T bulletins (requires pdftotext)')
    parser.add_argument('-b', default=1111, type=int, help='ITU-T bulletin number to start with, default is 1111')
    parser.add_argument('-j', action='store_true', help='produce a JSON file listing all MNC and SPC (with suffix .json)')
    parser.add_argument('-p', action='store_true', help='produce a Python file listing all MNC and SPC (with suffix .py)')
    args = parser.parse_args()
    #
    if args.d:
        try:
            dl_bull_all(bnum=args.b, dbg=False)
        except Exception as err:
            print('> error occured during downloading: %r' % err)
            return 1
    #
    try:
        MNC_1111 = parse_mnc_list(PATH_PRE + 'T-SP-OB.1111-2016-OAS-PDF-E.txt', dbg=False)
        MNC_1162 = parse_mnc_list(PATH_PRE + 'T-SP-OB.1162-2018-OAS-PDF-E.txt', dbg=False)
    except Exception as err:
        print('> error occured during MNC extraction: %r' % err)
        return 1
    try:
        SPC_1199 = parse_spc_list(PATH_PRE + 'T-SP-OB.1199-2020-OAS-PDF-E.txt', dbg=False)
    except Exception as err:
        print('> error occured during SPC extraction: %r' % err)
        return 1
    try:
        SANC_1125 = parse_sanc_list(PATH_PRE + 'T-SP-OB.1125-2017-OAS-PDF-E.txt', dbg=False)
    except Exception as err:
        print('> error occured during SANC extraction: %r' % err)
        return 1
    try:
        MNC_1162INCR = parse_mnc_incr(1163, fnpre=PATH_PRE, dbg=False)
    except Exception as err:
        print('> error occured during MNC incremental extraction: %r' % err)
        return 1
    #
    if args.j:
        generate_json(MNC_1111, PATH_RAW + 'itut_mnc_1111.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(MNC_1162, PATH_RAW + 'itut_mnc_1162.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(SPC_1199, PATH_RAW + 'itut_spc_1199.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(SANC_1125, PATH_RAW + 'itut_sanc_1125.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(MNC_1162INCR, PATH_RAW + 'itut_mnc_incr.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
    if args.p:
        generate_python(MNC_1111, PATH_RAW + 'itut_mnc_1111.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(MNC_1162, PATH_RAW + 'itut_mnc_1162.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(SPC_1199, PATH_RAW + 'itut_spc_1199.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(SANC_1125, PATH_RAW + 'itut_sanc_1125.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(MNC_1162INCR, PATH_RAW + 'itut_mnc_incr.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())

