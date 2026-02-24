#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# /**
# * Software Name : MCC_MNC
# * Version : 0.2
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
# * File Name : chk_cntr.py
# * Created : 2020-09-14
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


import sys
import argparse
#
from mcc_mnc_lut.p1_terr import P1_TERR
from mcc_mnc_lut.p1_cntr import P1_CNTR
from mcc_mnc_lut.p1_cc2  import P1_CC2


def printext_cntr(infos, ext=1, indent=''):
    c = infos['codes']
    try:
        print('%s  alpha-3 code  : %s' % (indent, c['cc3']))
        print('%s  numeric code  : %s' % (indent, c['ccn']))
    except Exception:
        pass
    #
    g = infos['geo']
    print('%s  Wold Factbook (geography):' % indent)
    try:
        print('%s    boundaries details: length %i km' % (indent, g['bound']['len']))
        for (c, l) in sorted(g['bound']['bord'].items()):
            print('%s    - %-16s: %i' % (indent, c, l))
    except Exception:
        pass
    try:
        print('%s    coastline details : length %i km' % (indent, g['coast']['len']))
        for (c, l) in sorted(g['coast']['bord'].items()):
            print('%s    - %-16s: %s' % (indent, c, l))
    except Exception:
        pass
    try:
        print('%s    airports          : %i' % (indent, g['airports']))
        print('%s    ports:' % indent)
        for (k, v) in sorted(g['ports'].items()):
            print('%s    - %-16s: %s' % (indent, k, v))
    except Exception:
        pass
    #
    t = infos['tel']
    print('%s  World Factbook (telecommunications):' % indent)
    try:
        print('%s    tld               : %s' % (indent, t['tld']))
        print('%s    telephone prefix  : +%s' % (indent, t['code']))
    except Exception:
        pass
    try:
        print('%s    subscribers       : %s' % (
            indent, ', '.join(['%s: %i' % (k, v) for (k, v) in sorted(t['subs'].items())])))
    except Exception:
        pass
    if ext > 1:
        try:
            for tkey in ('general', 'domestic', 'intl'):
                print('%s    %s (%i):' % (indent, tkey, t[tkey][-1]))
                for l in t[tkey][:-1]:
                    print('%s      - %s' % (indent, l))
        except Exception as err:
            pass


def print_cntr(cntr, dep=None, ext=0, indent=''):
    if dep is None:
        print('%s> %s (%s)' % (indent, cntr['name'], cntr['cc2']))
        neigh = P1_TERR[cntr['name']]['neigh']
    else:
        print('%s> %s, dependent to country %s (%s)' % (indent, cntr, dep['name'], dep['cc2']))
        neigh = P1_TERR[cntr]['neigh']
        cntr = dep
    #
    print('%s  MCC           : %s' % (indent, ', '.join(cntr['mcc'])))
    print('%s  MSISDN prefix : +%s' % (indent, ', +'.join(cntr['msisdn'])))
    print('%s  url Wikipedia : %s' % (indent, cntr['url']))
    print('%s  borders       : %s' % (indent, ', '.join(neigh['bord'])))
    print('%s  neighbours (< 30km) : %s' % (indent, ', '.join(neigh['less30'])))
    print('%s  neighbours (< 100km): %s' % (indent, ', '.join(neigh['less100'])))
    #
    if cntr['dep']:
        print('%s  dependency    : %s' % (indent, cntr['dep']))
    #
    try:
        print('%s  url World Factbook  : %s' % (indent, cntr['infos']['geo']['url_wfb']))
        print('%s  population    : %i' % (indent, cntr['infos']['geo']['popul']))
        print('%s  capital       : %s, coordinates: %s'\
              % (indent, cntr['infos']['geo']['capital']['name'], cntr['infos']['geo']['capital']['coord']))
    except Exception:
        pass
    #
    if ext:
        printext_cntr(cntr['infos'], ext=ext, indent=indent)
    if ext > 1:
        # give the list of MCC-MNC
        print('%s  list of MCC-MNC:' % indent)
        for mccmnc in cntr['mccmnc']:
            print('%s    %s' % (indent, mccmnc))


def main():
    parser = argparse.ArgumentParser(description=
        'provides information related to a given country or territory; '\
        'if no argument is passed, lists all known countries and territories')
    parser.add_argument('COUNTRY', nargs='*', help='0 or more string for country (can be an alpha-2 code too)')
    parser.add_argument('-x', action='count', help='provides extended country-related information, set more x for more verbose info')
    args = parser.parse_args()
    if not args.x:
        args.x = 0
    #print(args)
    #
    if not args.COUNTRY:
        for k in sorted(P1_TERR):
            print(k)
    else:
        for country in args.COUNTRY:
            if len(country) == 2 and country.upper() in P1_CC2:
                print_cntr(P1_CC2[country.upper()], ext=args.x)
                print('')
            elif country in P1_CNTR:
                print_cntr(P1_CNTR[country], ext=args.x)
                print('')
            else:
                found = False
                for name, inf in P1_CNTR.items():
                    if country.lower() in inf['infos']['nameset']:
                        print_cntr(inf, ext=args.x)
                        found = True
                        break
                if not found:
                    for name, inf in P1_TERR.items():
                        if country.lower() == name.lower():
                            assert( inf['cc2'] is None )
                            print_cntr(country, dep=P1_CC2[inf['dep']], ext=args.x)
                            found = True
                            break
                if not found:
                    print('> unknown country: %s' % country)
                print('')
    #
    return 0


if __name__ == '__main__':
    sys.exit(main())

