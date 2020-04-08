#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
#
from gen.p1_msisdn import P1_MSISDN
from gen.p1_cntr   import P1_CNTR
#
from chk_cntr  import print_cntr
from chk_mnc   import print_mcc


def main():
    parser = argparse.ArgumentParser(description=
        'provides information related to international telephone prefix; '\
        'if no argument is passed, lists all known MSISDN prefixes')
    parser.add_argument('MSISDN', nargs='*', help='0 or more digit string for MSISDN')
    parser.add_argument('-x', action='count', help='provides extended country-related information, set more x for more verbose info')
    args = parser.parse_args()
    if not args.x:
        args.x = 0
    #print(args)
    #
    if not args.MSISDN:
        for k in sorted(P1_MSISDN):
            print(k)
    else:
        for msisdn in args.MSISDN:
            if not msisdn.isdigit():
                print('> invalid MSISDN: %s\n' % msisdn)
                continue
            #
            found = False
            if msisdn in P1_MSISDN:
                cntrs = P1_MSISDN[msisdn]
                print('> +%s: known prefix for countries:\n  %s'\
                      % (msisdn, ',\n  '.join(cntrs)))
                if args.x:
                    for cntr in cntrs:
                        print_cntr(P1_CNTR[cntr], ext=args.x-1)
                        for mcc in P1_CNTR[cntr]['mcc']:
                            print_mcc(mcc, {P1_CNTR[cntr]['cc2']})
                print('')
                found = True
            else:
                for i in range(1, len(msisdn)):
                    if msisdn[:-i] in P1_MSISDN:
                        cntrs = P1_MSISDN[msisdn[:-i]]
                        print('> %s: known prefix +%s for countries:\n  %s'\
                              % (msisdn, msisdn[:-i], ',\n  '.join(cntrs)))
                        if args.x:
                            for cntr in cntrs:
                                print_cntr(P1_CNTR[cntr], ext=args.x-1)
                                for mcc in P1_CNTR[cntr]['mcc']:
                                    print_mcc(mcc, {P1_CNTR[cntr]['cc2']})
                        print('')
                        found = True
                        break
            if not found:
                print('> unknown MSISDN: %s\n' % msisdn)
    #
    return 0


if __name__ == '__main__':
    sys.exit(main())

