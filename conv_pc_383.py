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
# * File Name : conv_pc_383.py
# * Created : 2021-04-08
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */

__all__ = ['conv_pc_383']


import sys


def conv_pc_383(pcval):
    if '-' in pcval:
        pc_comps = pcval.split('-')
        return (int(pc_comps[0])<<11) + \
               (int(pc_comps[1])<<3)  + \
                int(pc_comps[2])
    else:
        pcint = int(pcval)
        return '%i-%i-%i' % (
                ((pcint>>11) & 0x7),
                ((pcint>>3) & 0xff),
                 (pcint & 0x7) )


def help():
    print('convert Point Code from 3-8-3 format to uint, and the opposite')
    print('just pass your value in X-Y-Z format or plain integer as argument')


def main(arg):
    if arg in ('-h', '--help'):
        help()
        return 0
    #
    try:
        pcconv = conv_pc_383(arg)
    except Exception:
        print('invalid arg')
        help()
    else:
        print(pcconv)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1]))

