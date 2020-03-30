#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
#
from p1_mnc import P1_MNC
from p1_mcc import P1_MCC
from p1_cc2 import P1_CC2
#
from chk_cntr import print_cntr


def print_mcc(mcc):
    print('> MCC %s' % mcc)
    mcc = P1_MCC[mcc]
    print('  country       : %s' % mcc['cc2'])
    print('  url Wikipedia : %s' % mcc['url'])
    print('  regulator     : %s' % mcc['reg'])
    if mcc['notes']:
        print('  notes         : %s' % mcc['notes'])


def print_mno(mccmnc, mno, ext):
    print('  operational   : %s' % repr(mno['ope']).lower())
    print('  brand         : %s' % mno['brand'])
    print('  operator      : %s' % mno['operator'])
    print('  country       : %s' % mno['country'])
    print('  bands         : %s' % ', '.join(mno['bands']))
    if ext:
        if mccmnc[:3] in P1_MCC:
            print_mcc(mccmnc[:3])
        for cc2 in mno['cc2s']:
            print_cntr(P1_CC2[cc2], ext=ext-1)


def print_mnos(mccmnc, ext=0):
    mnos = P1_MNC[mccmnc]
    if isinstance(mnos, list):
        print('> %s: multiple MNOs' % mccmnc)
        for mno in mnos:
            print('>')
            print_mno(mccmnc, mno, ext)
    else:
        print('> %s: MNO' % mccmnc)
        print_mno(mccmnc, mnos, ext)


def main():
    parser = argparse.ArgumentParser(description=
        'provides information related to mobile operator(s); if no argument is passed, lists all known MCC-MNC')
    parser.add_argument('MCCMNC', nargs='*', help='0 or more 5/6-digit string for MCC-MNC')
    parser.add_argument('-x', action='count', help='provides extended information for MNO(s)')
    args = parser.parse_args()
    if not args.x:
        args.x = 0
    #print(args)
    #
    if not args.MCCMNC:
        for k in sorted(P1_MNC):
            print(k)
    else:
        for mccmnc in args.MCCMNC:
            if not 5 <= len(mccmnc) <= 6 or not mccmnc.isdigit():
                print('> invalid MCC-MNC: %s\n' % mccmnc)
                continue
            elif mccmnc not in P1_MNC:
                print('> unknown MCC-MNC: %s\n' % mccmnc)
                continue
            print_mnos(mccmnc, args.x)
            print('')
    #
    return 0


if __name__ == '__main__':
    sys.exit(main())

