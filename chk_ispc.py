#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# /**
# * Software Name : MCC_MNC
# * Version : 0.1
# *
# * Copyright 2021. Benoit Michau. P1 Security.
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
# * File Name : chk_ispc.py
# * Created : 2021-04-08
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


import sys
import argparse
#
from gen.p1_ispc    import P1_ISPC
from gen.p1_sanc    import P1_SANC
from gen.p1_cc2     import P1_CC2
from gen.p1_cntr    import P1_CNTR
from gen.p1_terr    import P1_TERR
from conv_pc_383    import conv_pc_383
from chk_cntr       import print_cntr
from patch_country_dep import COUNTRY_SPEC


def print_ispc(ispc, ext=0):
    #
    if ispc in P1_ISPC:
        cntr, ope, uname, pcint = P1_ISPC[ispc]
    else:
        pcint = conv_pc_383(ispc)
        uname = ''
        ope   = ''
        # check with the 3-8 prefix only against the SANC list
        pc_pref = '-'.join(ispc.split('-')[:2])
        cntr  = P1_SANC.get(pc_pref, 'unknown')   
    assert( int(pcint) == conv_pc_383(ispc) )
    #
    print('> %s: International Signaling Point Code' % ispc)
    print('  PC integer    : %s' % pcint)
    print('  country       : %s' % cntr)
    print('  unique name   : %s' % uname)
    print('  operator      : %s' % ope)
    if ext:
        if cntr in P1_CNTR:
            print_cntr(P1_CNTR[cntr], ext=ext-1)
        else:
            found = False
            for name, inf in P1_CNTR.items():
                if cntr in inf['infos']['nameset']:
                    print_cntr(inf, ext=ext-1)
                    found = True
                    break
            if not found and cntr in COUNTRY_SPEC:
                cntr_spec = COUNTRY_SPEC[cntr]
                if 'cc2' in cntr_spec:
                    print_cntr(P1_CC2[cntr_spec['cc2']], ext=ext-1)
                elif 'sub_cc2' in cntr_spec:
                    for cc2 in cntr_spec['sub_cc2']:
                        print_cntr(P1_CC2[cc2], ext=ext-1)
                found = True
            if not found and cntr.lower() not in ('reserved', 'unknown'):
                print('> unknown country: %s' % cntr)


def main():
    parser = argparse.ArgumentParser(description=
        'provides information related to ISPC (International Signaling Point Code); if no argument is passed, lists all known ISPC')
    parser.add_argument('ISPC', nargs='*', help='0 or more 3-8-3 formatted or integer ISPC values')
    parser.add_argument('-x', action='count', help='provides extended information for associated country')
    args = parser.parse_args()
    if not args.x:
        args.x = 0
    #print(args)
    #
    if not args.ISPC:
        for k in sorted(P1_ISPC):
            print(k)
    else:
        for ispc in args.ISPC:
            if '-' not in ispc:
                # convert from integer to 3-8-3 format
                try:
                    ispc = conv_pc_383(ispc)
                except Exception:
                    print('invalid format for ISPC: 3-8-3 or integer format required')
                    return 0
            else:
                if ispc.count('-') != 2:
                    print('invalid format for ISPC: 3-8-3 or integer format required')
                    return 0
                try:
                    a, b, c = map(int, ispc.split('-'))
                except Exception:
                    print('invalid format for ISPC: 3-8-3 or integer format required')
                    return 0
                else:
                    if not 0 <= a <= 7 or not 0 <= b <= 255 or not 0 <= c <= 7:
                        print('invalid format for ISPC: 3-8-3 or integer format required')
                        return 0
                    ispc = '%i-%.3i-%i' % (a, b, c)
            #
            print_ispc(ispc, args.x)
            print('')
    #
    return 0


if __name__ == '__main__':
    sys.exit(main())

