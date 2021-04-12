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


import sys
import os
import argparse
import urllib.request
import urllib.error
import subprocess
import time
import re

from parse_wikipedia_tables import (
    generate_json,
    generate_python,
    )


PATH_RAW = 'raw/'

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
PATH_PRE = 'itut/'
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
    }


def strip_footer(fn, dbg=True):
    lines = []
    with open(fn, encoding='utf-8') as fd:
        bnum = fn.split('.')[1].split('-')[0]
        re1  = re.compile('No\. %s\s{0,}–\s{0,}[0-9]{1,}' % bnum)
        re2  = re.compile('Annex to ITU OB %s-E\s{0,}–\s{0,}[0-9]{1,}' % bnum)
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


def dl_bull(bnum=1111, byear=2016, dbg=True):
    """try to download an ITU-T bulletin with the given bulletin number `bnum'
    from the given year `byear'
    """
    fn  = 'T-SP-OB.%i-%i-OAS-PDF-E.pdf' % (bnum, byear)
    url = ITUT_BULL_URL_PREF + fn
    try:
        resp = urllib.request.urlopen(url)
    except urllib.error.HTTPError as err:
        #print('> unable to download bulletin %.4i for year %.4i' % (bnum, byear))
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
    '\nMobile Network Codes \(MNC\) under geographic Mobile Country Codes \(MCC\)\n',
    re.IGNORECASE
    )

RE_MNC_LIST_END     = re.compile(
    '(\n____________\n\*       MCC: Mobile Country Code /)|'\
    '(\nShared Mobile Country Codes \(MCC\) for networks and their respective Mobile Network\nCodes \(MNC\)\n)',
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
    '(Country or)|'\
    '(Geographical Area\s{1,}Networks\s{1,}MCC \+ MNC codes)|'\
    '(\*This designation is without prejudice to positions on status, and is in line with UNSCR 1244 and the ICJ Opinion on the Kosovo)|'\
    '(declaration of independence.)$',
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

RE_COUNTRY      = re.compile('\w.*$')


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

RE_MNC          = re.compile('\s{24,}(.*?)([0-9]{3} [0-9]{2,3})$')
RE_DESC         = re.compile('\s{24,}(.*)$')


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
# parse SPC list
#------------------------------------------------------------------------------#

"""
Bulletin 1125 (2017) contains the complete list of Signaling Area Network Code
per country.
The following script extract this list from the bulletin. 
"""

RE_SANC_LIST_BEG    = re.compile(
    '\n\s{1,}List of Signalling Area/Network Codes \(SANC\)'\
    '\n\s{1,}\(Complement to Recommendation ITU-T Q\.708 \(03/99\)\)'\
    '\n\s{1,}\(Position on 1 June 2017\)\n'\
    '\n\s{1,}\(Annex to ITU Operational Bulletin No\. 1125 - 1\.VI\.2017\)\n',
    re.IGNORECASE)


RE_SANC_LIST_END    = re.compile(
    '\n\s{1,}Code\s{1,}Geographical Area or Signalling Network\s{1,}–\s{1,}alphabetical order\n',
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
    'Code\s{1,}Geographical Area or Signalling Network\s{1,}–\s{1,}numerical order\s{0,}',
    re.IGNORECASE
    )

# SANC declaration:
#  SANC country
#
# SANC: W-XYZ digits
# 
RE_SANC = re.compile(
    '([0-9]-[0-9]{3})\s{1,}(.*)',
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
    '\n\s{1,}List of International Signalling Point Codes \(ISPC\) for signalling system No\. 7'\
    '\n\s{1,}\(According to Recommendation ITU-T Q\.708 \(03/99\)\)\n',
    re.IGNORECASE
    )


RE_SPC_LIST_END     = re.compile(
    '\n____________\nISPC:\s{1,}International Signalling Point Codes\.\n',
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
    '(\s{0,}Country/)|'\
    '(\s{0,}Geographical Area)|'\
    '(\s{0,}ISPC\s{1,}DEC\s{1,}Unique name of the signalling point\s{1,}Name of the signalling point operator)|'\
    '(\s{0,}This designation is without prejudice to positions on status, and is in line with UNSCR 1244 and the ICJ Opinion on the Kosovo)|'\
    '(declaration of independence.)$',
    re.IGNORECASE
    )


# Country declaration:
#
# Country names are always on a single line

# SPC declaration:
#    ISPC DEC name_spc name_ope
#
# name_spc or name_ope may be splitted on multiple lines

RE_ISPC         = re.compile('[0-9]\-[0-9]{3}\-[0-9]')


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
                name_spc, name_ope = map(str.strip, re.split('\s{2,}', line.strip()))
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
                name_spc, name_ope = map(str.strip, re.split('\s{2,}', line.strip()))
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
            print('> error occured during downloading: %s' % err)
            return 1
    #
    try:
        MNC_1111 = parse_mnc_list(PATH_PRE + 'T-SP-OB.1111-2016-OAS-PDF-E.txt', dbg=False)
        MNC_1162 = parse_mnc_list(PATH_PRE + 'T-SP-OB.1162-2018-OAS-PDF-E.txt', dbg=False)
    except Exception as err:
        print('> error occured during MNC extraction: %s' % err)
        return 1
    try:
        SPC_1199 = parse_spc_list(PATH_PRE + 'T-SP-OB.1199-2020-OAS-PDF-E.txt', dbg=False)
    except Exception as err:
        print('> error occured during SPC extraction: %s' % err)
        return 1
    try:
        SANC_1125 = parse_sanc_list(PATH_PRE + 'T-SP-OB.1125-2017-OAS-PDF-E.txt', dbg=False)
    except Exception as err:
        print('> error occured during SANC extraction: %s' % err)
        return 1
    #
    if args.j:
        generate_json(MNC_1111, PATH_RAW + 'itut_mnc_1111.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(MNC_1162, PATH_RAW + 'itut_mnc_1162.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(SPC_1199, PATH_RAW + 'itut_spc_1199.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(SANC_1125, PATH_RAW + 'itut_sanc_1125.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
    if args.p:
        generate_python(MNC_1111, PATH_RAW + 'itut_mnc_1111.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(MNC_1162, PATH_RAW + 'itut_mnc_1162.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(SPC_1199, PATH_RAW + 'itut_spc_1199.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(SANC_1125, PATH_RAW + 'itut_sanc_1125.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())

