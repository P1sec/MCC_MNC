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
# * File Name : parse_various_csv.py
# * Created : 2020-09-14
# * Authors : Benoit Michau
# *--------------------------------------------------------
# */


import argparse
import csv
import os
import sys
import urllib.request
from os.path import dirname, join, realpath

from mcc_mnc_genlib.scripts.parse_wikipedia_tables import (
    generate_json,
    generate_python,
)

SCRIPT_DIR = dirname(realpath(__file__))
MODULE_DIR = dirname(realpath(SCRIPT_DIR))

PATH_PRE = join(MODULE_DIR, 'raw', '')

# ------------------------------------------------------------------------------#
# get Egallic minimum distance between countries
# ------------------------------------------------------------------------------#

# download the dataset with minimum distance between countries, from here
URL_MIN_DIST = (
    'https://gist.githubusercontent.com/mtriff/185e15be85b44547ed110e412a1771bf/'
    'raw/1bb4d287f79ca07f63d4c56110099c26e7c6ee7d/countries_distances.csv'
)
# which is an updated version of the dataset computed here:
# http://egallic.fr/en/closest-distance-between-countries/
# this dataset is computed thanks to various R packages


def get_egal_min_dist():
    if not os.path.exists(PATH_PRE + 'csv_country_dist.csv'):
        resp = urllib.request.urlopen(URL_MIN_DIST)
        if resp.code != 200:
            raise (
                Exception(
                    'resource %s not available, HTTP code %i'
                    % (url, resp.code)
                )
            )
        with open(PATH_PRE + 'csv_country_dist.csv', 'w') as fd:
            # as the data provided through the URL is not updated
            # we better keep a local copy of it
            fd.write(resp.read().decode('utf-8'))
        print('> downloaded and stored to csv_country_dist.csv')
    with open(PATH_PRE + 'csv_country_dist.csv', encoding='utf-8') as fd:
        csv_lines = fd.readlines()
        if 'pays1' in csv_lines[0]:
            # remove header
            del csv_lines[0]
        while not csv_lines[-1].strip():
            # remove blank lines
            del csv_lines[-1]
        #
        # make it a dictionnary
        D = {}
        for n, src, dst, dist in csv.reader(csv_lines, delimiter=','):
            src, dst, dist = (t.replace('"', '').strip() for t in (src, dst, dist))
            if src not in D:
                D[src] = {}
            elif dst in D[src]:
                print(
                    '> duplicate entry in Egallic csv for {} in {}'.format(dst, src)
                )
            D[src][dst] = float(dist)
        print(
            '[+] parsed Egallic-related csv file with minimum distance between countries'
        )
        return D


# ------------------------------------------------------------------------------#
# Main
# ------------------------------------------------------------------------------#

URL_LICENSE_EGAL = 'http://egallic.fr/en/closest-distance-between-countries/'


def main():
    parser = argparse.ArgumentParser(
        description='dump csv file from the Egallic blog (distance between countries)'
    )
    parser.add_argument(
        '-j',
        action='store_true',
        help='produce a JSON file (with suffix .json)',
    )
    parser.add_argument(
        '-p',
        action='store_true',
        help='produce a Python file (with suffix .py)',
    )
    args = parser.parse_args()
    try:
        DE = get_egal_min_dist()
    except Exception as err:
        print('> error occured: {}'.format(err))
        return 1
    if args.j:
        generate_json(
            DE,
            PATH_PRE + 'csv_egal_min_dist.json',
            [URL_MIN_DIST],
            URL_LICENSE_EGAL,
        )
    if args.p:
        generate_python(
            DE,
            PATH_PRE + 'csv_egal_min_dist.py',
            [URL_MIN_DIST],
            URL_LICENSE_EGAL,
        )
    return 0


if __name__ == '__main__':
    sys.exit(main())
