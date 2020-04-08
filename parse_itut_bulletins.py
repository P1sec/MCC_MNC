#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

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
    with open(fn) as fd:
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
    with open(fn, 'w') as fd:
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


def dl_bull_all(dbg=False):
    """download all ITU-T bulletins starting from bulletin 1111 in 2016 in PDF
    format and convert them to text files
    """
    # start with bulletin 1111 from 2016
    bnum  = 1111
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
Bulletin 1111 (2016) and 1162 (2018) contains both the complete list of updated 
MCC-MNC per country.
The following script extract this list from both bulletins. 
"""

# to extract the list
RE_LIST_BEG     = re.compile(
    '\nMobile Network Codes \(MNC\) under geographic Mobile Country Codes \(MCC\)\n',
    re.IGNORECASE
    )

RE_LIST_END     = re.compile(
    '(\n____________\n\*       MCC: Mobile Country Code /)|'\
    '(\nShared Mobile Country Codes \(MCC\) for networks and their respective Mobile Network\nCodes \(MNC\)\n)',
    re.IGNORECASE
    )


def parse_mnc_list(fn=PATH_PRE+'T-SP-OB.1162-2018-OAS-PDF-E.txt', dbg=False):
    with open(fn) as fd:
        txt = fd.read()
        #
        # keep only the list of MCC-MNC
        beg = RE_LIST_BEG.search(txt)
        end = RE_LIST_END.search(txt)
        if not beg or not end:
            print('> no MNC list found')
            return None
        txt = txt[beg.end():end.start()].strip()
        #
        return parse_mnc_lines([l.rstrip() for l in txt.split('\n') if l.strip()], dbg)
    #
    return None


# Some table titles and a comment on Kosovo need to be stripped properly

RE_LINE_IGNORE  = re.compile(
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
        if RE_LINE_IGNORE.match(line):
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
# parse MNC list
#------------------------------------------------------------------------------#

URL_LICENSE_ITUT = 'https://www.itu.int/pub/T-SP'


def main():
    parser = argparse.ArgumentParser(description=
        'download ITU-T operational bulletins, convert them to text, extract lists of MNC')
    parser.add_argument('-d', action='store_true', help='download and convert all ITU-T bulletins, starting from the 1111')
    parser.add_argument('-j', action='store_true', help='produce a JSON file listing all MNC (with suffix .json)')
    parser.add_argument('-p', action='store_true', help='produce a Python file listing all MNC (with suffix .py)')
    args = parser.parse_args()
    #
    if args.d:
        try:
            dl_bull_all(dbg=False)
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
    #
    if args.j:
        generate_json(MNC_1111, PATH_RAW + 'itut_mnc_1111.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_json(MNC_1162, PATH_RAW + 'itut_mnc_1162.json', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
    if args.p:
        generate_python(MNC_1111, PATH_RAW + 'itut_mnc_1111.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
        generate_python(MNC_1162, PATH_RAW + 'itut_mnc_1162.py', [URL_LICENSE_ITUT], URL_LICENSE_ITUT)
    return 0


if __name__ == '__main__':
    sys.exit(main())

