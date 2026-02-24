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
# * File Name : chk_mnc.py
# * Created : 2020-09-14
# * Authors : Benoit Michau
# *--------------------------------------------------------
# */


import sys
import argparse

#
from mcc_mnc_lut.p1_mnc import P1_MNC
from mcc_mnc_lut.p1_mcc import P1_MCC
from mcc_mnc_lut.p1_cc2 import P1_CC2

#
from mcc_mnc_genlib.scripts.chk_cntr import print_cntr


def print_mcc(mcc, cc2s, indent=''):
    print('%s> MCC %s' % (indent, mcc))
    mcc = P1_MCC[mcc]
    if isinstance(mcc, list):
        mccs = mcc
        for mcc in mccs:
            if mcc['cc2'] in cc2s:
                print('%s  country       : %s' % (indent, mcc['cc2']))
                print('%s  url Wikipedia : %s' % (indent, mcc['url']))
                print('%s  regulator     : %s' % (indent, mcc['reg']))
                if mcc['notes']:
                    print('%s  notes         : %s' % (indent, mcc['notes']))
    else:
        print('%s  country       : %s' % (indent, mcc['cc2']))
        print('%s  url Wikipedia : %s' % (indent, mcc['url']))
        print('%s  regulator     : %s' % (indent, mcc['reg']))
        if mcc['notes']:
            print('%s  notes         : %s' % (indent, mcc['notes']))


def print_mno(mccmnc, mno, ext, indent=''):
    print('%s  operational   : %s' % (indent, repr(mno['ope']).lower()))
    print('%s  brand         : %s' % (indent, mno['brand']))
    print('%s  operator      : %s' % (indent, mno['operator']))
    print('%s  country       : %s' % (indent, mno['country']))
    print('%s  bands         : %s' % (indent, ', '.join(mno['bands'])))
    print('%s  src           : %s' % (indent, mno['src']))
    if ext:
        if mccmnc[:3] in P1_MCC:
            print_mcc(mccmnc[:3], mno['cc2s'], indent='  ')
        for cc2 in mno['cc2s']:
            print_cntr(P1_CC2[cc2], ext=ext - 1, indent='  ')


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
    parser = argparse.ArgumentParser(
        description='provides information related to mobile operator(s); if no argument is passed, lists all known MCC-MNC'
    )
    parser.add_argument(
        'MCCMNC', nargs='*', help='0 or more 5/6-digit string for MCC-MNC'
    )
    parser.add_argument(
        '-x',
        action='count',
        help='provides extended information for MNO(s), set more x for more verbose info',
    )
    args = parser.parse_args()
    if not args.x:
        args.x = 0
    # print(args)
    #
    if not args.MCCMNC:
        for k in sorted(P1_MNC):
            print(k)
    else:
        for mccmnc in args.MCCMNC:
            mcc, mnc = mccmnc[:3], mccmnc[3:]
            if len(mcc) != 3 or mcc not in P1_MCC:
                print('> unknown MCC: %s\n' % mcc)
                continue
            elif not mnc:
                # country code only, print all MCCMNC for the given MCC
                mcc_cntr = P1_MCC[mcc]
                if isinstance(mcc_cntr, list):
                    # MCC used for several countries / territories
                    mncs = set()
                    for mcc_cntr_sin in mcc_cntr:
                        mncs.update(mcc_cntr_sin['mncs'])
                    mncs = list(sorted(mncs))
                else:
                    mncs = mcc_cntr['mncs']
                for _mccmnc in mncs:
                    print_mnos(_mccmnc, args.x)
            elif mccmnc not in P1_MNC:
                print('> unknown MCC-MNC: %s\n' % mccmnc)
            else:
                print_mnos(mccmnc, args.x)
            print('')
    #
    return 0


if __name__ == '__main__':
    sys.exit(main())
