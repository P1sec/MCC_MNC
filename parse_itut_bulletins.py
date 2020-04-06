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


# ITU-T website url prefix
ITUT_BULL_URL_PREF = 'https://www.itu.int/dms_pub/itu-t/opb/sp/'
# directory to store all ITU-T bulletins
PATH_PRE = 'itut_bulletins/'
# command to convert them to text file
PDFTOTXT = ['pdftotext', '-layout', '-nopgbrk']


# 1) download ITU-T bulletins in PDF format
# starting from the 1111 in 2016 (bulletin with the official complete list of MNCs)
# and all bulletins onwards
# 1st bulletin of 2017 is 1115
# 23 or 24 bulletins are edited each month
# URL examples:
# - https://www.itu.int/dms_pub/itu-t/opb/sp/T-SP-OB.1111-2016-OAS-PDF-E.pdf
# - https://www.itu.int/dms_pub/itu-t/opb/sp/T-SP-OB.1115-2017-OAS-PDF-E.pdf


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
    """try to download all ITU-T bulletins starting from bulletin 1111 in 2016
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
 

if __name__ == '__main__':
    print('houhou ?')
    dl_bull_all(dbg=True)

