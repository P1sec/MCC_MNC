#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
#
from p1_terr import P1_TERR
from p1_cntr import P1_CNTR
from p1_cc2  import P1_CC2


def printext_cntr(infos):
    c = infos['codes']
    try:
        print('  alpha-3 code  : %s' % c['cc3'])
        print('  numeric code  : %s' % c['ccn'])
    except Exception:
        pass
    #
    g = infos['geo']
    print('  Wold Factbook (geography):')
    try:
        print('    boundaries details: length %i km' % g['bound']['len'])
        for (c, l) in sorted(g['bound']['bord'].items()):
            print('    - %-16s: %i' % (c, l))
    except Exception:
        pass
    try:
        print('    coastline details : length %i km' % g['coast']['len'])
        for (c, l) in sorted(g['coast']['bord'].items()):
            print('    - %-16s: %s' % (c, l))
    except Exception:
        pass
    try:
        print('    airports          : %i' % g['airports'])
        print('    ports:')
        for (k, v) in sorted(g['ports'].items()):
            print('    - %-16s: %s' % (k, v))
    except Exception:
        pass
    #
    t = infos['tel']
    print('  World Factbook (telecommunications):')
    try:
        print('    tld               : %s' % t['tld'])
        print('    telephone prefix  : +%s' % t['code'])
    except Exception:
        pass
    try:
        print('    subscribers       : %s' % ', '.join(['%s: %i' % (k, v) for (k, v) in sorted(t['subs'].items())]))
    except Exception:
        pass
    try:
        print('    general information (%i):' % t['general'][-1])
        for i in t['general'][:-1]:
            print('      - %s' % i)
        print('    international connection (%i):' % t['intl'][-1])
        for i in t['intl'][:-1]:
            print('      - %s' % i)
    except Exception:
        pass


def print_cntr(cntr, sov=None, ext=0):
    if sov is None:
        print('> %s (%s)' % (cntr['name'], cntr['cc2']))
        neigh = P1_TERR[cntr['name']]['neigh']
    else:
        print('> %s, sovereign country %s (%s)' % (cntr, sov['name'], sov['cc2']))
        neigh = P1_TERR[cntr]['neigh']
        cntr = sov
    #
    print('  MCC           : %s' % ', '.join(cntr['mcc']))
    print('  MSISDN prefix : +%s' % ', +'.join(cntr['msisdn']))
    print('  url Wikipedia : %s' % cntr['url'])
    print('  borders       : %s' % ', '.join(neigh['bord']))
    print('  neighbours (< 30km) : %s' % ', '.join(neigh['less30']))
    print('  neighbours (< 100km): %s' % ', '.join(neigh['less100']))
    #
    try:
        print('  url World Factbook  : %s' % cntr['infos']['geo']['url_wfb'])
        print('  population    : %i' % cntr['infos']['geo']['popul'])
        print('  capital       : %s, coordinates: %s'\
              % (cntr['infos']['geo']['capital']['name'], cntr['infos']['geo']['capital']['coord']))
    except Exception:
        pass
    #
    if ext:
        printext_cntr(cntr['infos'])
    if ext > 1:
        # give the list of MCC-MNC
        print('  list of MCC-MNC:')
        for mccmnc in cntr['mccmnc']:
            print('    %s' % mccmnc)


def main():
    parser = argparse.ArgumentParser(description=
        'provides information related to a given country or territory; '\
        'if no argument is passed, lists all known countries and territories')
    parser.add_argument('COUNTRY', nargs='*', help='0 or more string for country (can be an alpha-2 code too)')
    parser.add_argument('-x', action='count', help='provides extended country-related information')
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
                    if country in inf['infos']['nameset']:
                        print_cntr(inf, ext=args.x)
                        found = True
                        break
                if not found:
                    for name, inf in P1_TERR.items():
                        if country.lower() == name.lower():
                            assert( inf['cc2'] is None )
                            print_cntr(country, sov=P1_CC2[inf['sov']], ext=args.x)
                            found = True
                            break
                if not found:
                    print('> unknown country: %s' % country)
                print('')
    #
    return 0


if __name__ == '__main__':
    sys.exit(main())

