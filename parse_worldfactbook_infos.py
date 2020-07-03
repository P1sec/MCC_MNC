#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import sys
import argparse
import urllib.request
import re

from parse_wikipedia_tables import (
    import_html_doc,
    explore_text,
    generate_json,
    generate_python,
    _stripbordref
    )


PATH_PRE = 'raw/'

#------------------------------------------------------------------------------#
# parsing CIA World Factbook country information
#------------------------------------------------------------------------------#

URL_FACTBOOK = 'https://www.cia.gov/library/publications/the-world-factbook/appendix/appendix-d.html'
URL_PREF     = 'https://www.cia.gov/library/publications/the-world-factbook/geos/'


REC_COUNTRY  = {
    'name'  : '',
    'url'   : '',
    'gec'   : '',
    'cc2'   : '',
    'cc3'   : '',
    'ccn'   : '',
    'stan'  : '', 
    'tld'   : '',
    'cmt'   : ''
    }


def _get_text(e, cb=None):
    t = explore_text(e)
    if t is not None and t.text:
        if callable(cb):
            return cb(t.text.strip())
        else:
            return t.text.strip()
    else:
        return ''


def parse_table_country_all():
    T   = import_html_doc(URL_FACTBOOK).xpath('//table')
    T_C = T[0][2]
    D   = {} 
    #
    for L in T_C:
        rec = dict(REC_COUNTRY)
        L0  = explore_text(L[0])
        rec['name'] = L0.text.strip()
        rec['gec']  = _get_text(L[1], cb=str.upper)
        rec['cc2']  = _get_text(L[2], cb=str.upper)
        rec['cc3']  = _get_text(L[3], cb=str.upper)
        rec['ccn']  = _get_text(L[4], cb=str.upper)
        rec['stan'] = _get_text(L[5], cb=str.upper)
        rec['tld']  = _get_text(L[6], cb=str.lower)
        rec['cmt']  = _get_text(L[7])
        #
        if L0.values() and len(L0.values()[0]) > 8:
            rec['url']  = URL_PREF + 'print_' + L0.values()[0][8:].strip().lower()
            rec['infos'] = parse_table_country(rec['url'])
            if not rec['infos']:
                print('> web page does not exist for %s' % rec['name'])
            else:
                print('> infos extracted for %s' % rec['name'])
        #
        if rec['name'] in D:
            raise(Exception('> duplicate entry for country %s' % rec['name']))
        else:
            D[rec['name']] = rec
    #
    return D


RE_COUNTRY_CODE = re.compile('^country code - ([0-9\-]{1,5})')
RE_YEAR         = re.compile('^\(\s{0,}(20[0-9]{2})\s{0,}(est\.{0,1}){0,1}\)$')


def _extract_tel_generic(infos, year):
    return [t.strip() for t in infos.split(';') if t.strip()] + \
           [int(RE_YEAR.match(year).group(1))]
    

def _extract_tel(e):
    r = {}
    for esub in e:
        infos = [t.strip() for t in ''.join(esub.itertext()).split('\n') if t.strip()]
        if len(infos) == 2:
            sect, infos = infos
            year = '(2000)'
        elif len(infos) == 3:
            sect, infos, year = infos
        else: 
            continue
        #
        infos = re.sub('[\s\xa0]{1,}', ' ', infos)
        if sect == 'general assessment:':
            r['general']  = _extract_tel_generic(infos, year)
        elif sect == 'domestic:':
            r['domestic'] = _extract_tel_generic(infos, year)
        elif sect == 'international:':
            m = RE_COUNTRY_CODE.match(infos)
            if m:
                infos = infos[m.end():].strip() 
                r['code']     = m.group(1).replace('-', '')
            r['intl']     = [t.strip() for t in infos.split(';') if t.strip()] + [int(RE_YEAR.match(year).group(1))]
        else:
            r[sect[:-1]]  = _extract_tel_generic(infos, year)
    return r


_PORT_TYPES = {
    'major seaport',
    'container port',
    'cruise/ferry port',
    'cargo port',
    'cruise departure port'
    }

def _extract_port(e):
    r = {}
    for esub in e:
        sect, infos = [t.strip() for t in ''.join(esub.itertext()).split('\n')][1:3]
        infos = re.sub('[\s\xa0]{1,}', ' ', infos)
        for ptype in _PORT_TYPES:
            if re.match(ptype, sect):
                r[ptype] = infos
                continue
    return r


RE_INTEG_VAL = re.compile('([0-9\.,]{1,})(\s{1,}million){0,1}')

def _extract_value(s):
    s = s.strip()
    if s[:6].lower() == 'approx':
        # remove 1st word
        s = s.split(' ', 1)[1].strip()
    m = RE_INTEG_VAL.match(s)
    if m:
        v = float(m.group(1).replace(',', ''))
        if m.group(2):
            return int(v * 1000000)
        else:
            return int(v)
    else:
        return 0


def _extract_geo_mult(e):
    r = []
    t = re.sub('\s{1,}', ' ', ''.join(e.itertext())).strip()
    for tsub in t.split(';'):
        if ':' in tsub:
            r.append( tuple(map(str.strip, tsub.split(':'))) )
        else:
            r.insert(0, tsub.strip())
    return r


RE_DIST = re.compile('([0-9]{1,})\s{0,}(?:km){0,1}')
RE_BORD = re.compile('border countries(?: \(([0-9]{1,})\)){0,1}:')


def _extract_dist(s):
    return int(RE_DIST.match(s.replace(',', '')).group(1))


def _extract_bound(e):
    r = {'bord': {}}
    for esub in e:
        infos = [t.strip() for t in ''.join(esub.itertext()).split('\n') if t.strip()]
        if len(infos) == 1 and RE_DIST.match(infos[0]):
            r['len'] = _extract_dist(infos[0])
        elif len(infos) == 2:
            m = RE_BORD.match(infos[0])
            if m:
                num       = int(m.group(1))
                countries = list(map(_stripbordref, infos[1].split(',')))
                assert(len(countries) == num)
                for country in countries:
                    m = RE_DIST.search(country)
                    if m:
                        r['bord'][country[:m.start()].strip()] = int(m.group(1))
                    else:
                        r['bord'][country] = 0
            elif 'len' not in r and infos[0][-6:] == 'total:':
                r['len'] = _extract_dist(infos[1])
    return r


def _extract_country_name(e):
    r = {}
    for esub in e:
        sect, infos = map(str.strip, ''.join(esub.itertext()).split('\n')[1:3])
        if sect.startswith('conventional short'):
            r['conv_short'] = infos
        elif sect.startswith('conventional long'):
            r['conv_long'] = infos
        elif sect.startswith('local short'):
            r['local_short'] = infos
        elif sect.startswith('local long'):
            r['local_long'] = infos
    return r


def _extract_capital(e):
    r = {}
    for esub in e:
        sect, infos = map(str.strip, ''.join(esub.itertext()).split('\n')[1:3])
        if sect == 'name:':
            r['name'] = infos
        elif sect == 'time difference:':
            r['time_diff'] = infos
        elif sect == 'geographic coordinates:':
            r['coord'] = infos
    return r


COUNTRY_SECTIONS = {
    'geography-category-section': {
        'field-geographic-coordinates': (
            'coord',
            _extract_geo_mult
            ),
        'field-map-references': (
            'region',
            _extract_geo_mult
            ),
        'field_area': (
            'area',
            lambda e: _get_text(e)
            ),
        'field-land-boundaries': (
            'boundaries',
            _extract_bound
            ),
        'field-coastline': (
            'coastline',
            _extract_bound
            #lambda e: _extract_dist(_get_text(e))
            ),
        },
    'people-and-society-category-section': {
        'field-population': (
            'population',
            lambda e: _extract_value(_get_text(e))
            ),
        },
    'government-category-section': {
        'field-country-name': (
            'country_name',
            _extract_country_name
            ),
        'field-capital': (
            'capital',
            _extract_capital
            ),
        },
    'communications-category-section': {
        'field-telephones-fixed-lines': (
            'subs_fixed',
            lambda e: _extract_value(_get_text(e[0])) if len(e) else ''
            ),
        'field-telephones-mobile-cellular': (
            'subs_mobile',
            lambda e: _extract_value(_get_text(e[0])) if len(e) else ''
            ),
        'field-telecommunication-systems': (
            'telecom',
            _extract_tel
            ),
        'field-internet-users': (
            'users_internet',
            lambda e: _extract_value(_get_text(e[0])) if len(e) else ''
            ),
        'field-broadband-fixed-subscriptions' : (
            'subs_broadband',
            lambda e: _extract_value(_get_text(e[0])) if len(e) else ''
            ),
        },
    'transportation-category-section': {
        'field-airports': (
            'airports',
            lambda e: _extract_value(_get_text(e))
            ),
        'field-ports-and-terminals': (
            'ports',
            _extract_port
            )
        }
    }


def _explore_subsection(S, D, FIELDS):
    for subsection in S:
        if 'id' in subsection.attrib and subsection.attrib['id'] in FIELDS:
            #print('subsection found: %s' % subsection.attrib['id'])
            name, cb = FIELDS[subsection.attrib['id']]
            D[name] = cb(subsection)
    # sometimes, HTML structure hierarchy is corrupted, hence this:
    _explore_section(S, D)


def _explore_section(S, D):
    for section in S:
        if 'id' in section.attrib and section.attrib['id'] in COUNTRY_SECTIONS:
            #print('section found: %s' % section.attrib['id'])
            _explore_subsection(section, D, COUNTRY_SECTIONS[section.attrib['id']])
        # sometimes, HTML structure hierarchy is corrupted, hence this:
        _explore_section(section, D)


def parse_table_country(url):
    try:
        T = import_html_doc(url)[2][0][0][0][0][0][1][1]
    except Exception:
        return {}
    #
    D = {}
    # warning: for some country url, the HTML structure is inconsistent
    _explore_section(T, D)
    return D


#------------------------------------------------------------------------------#
# Main
#------------------------------------------------------------------------------#

URL_LICENSE = "https://www.cia.gov/library/publications/the-world-factbook/docs/contributor_copyright.html"

def main():
    parser = argparse.ArgumentParser(description=
        'dump country-related informations from the CIA World Factbook into JSON or Python file')
    parser.add_argument('-j', action='store_true', help='produce a JSON file (with suffix .json)')
    parser.add_argument('-p', action='store_true', help='produce a Python file (with suffix .py)')
    args = parser.parse_args()
    try:
        D = parse_table_country_all()
    except Exception as err:
        print('> error occured: %s' % err)
        return 1
    #
    if args.j:
        generate_json(D, PATH_PRE + 'world_fb.json', [URL_FACTBOOK], URL_LICENSE)
    if args.p:
        generate_python(D, PATH_PRE + 'world_fb.py', [URL_FACTBOOK], URL_LICENSE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
