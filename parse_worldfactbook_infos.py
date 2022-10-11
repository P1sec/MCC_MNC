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
# * File Name : parse_worldfactbook_infos.py
# * Created : 2020-09-14
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


import sys
import argparse
import urllib.request
import re
import json
import time

from parse_wikipedia_tables import (
    import_html_doc,
    explore_text,
    generate_json,
    generate_python,
    _stripbordref
    )


PATH_PRE = 'raw/'


def import_json_doc(url):
    resp = urllib.request.urlopen(url)
    if resp.code == 200:
        J = json.load(resp)
    else:
        raise(Exception('resource %s not available, HTTP code %i' % (url, resp.code)))
    return J


#------------------------------------------------------------------------------#
# parsing CIA World Factbook country information
#------------------------------------------------------------------------------#

# old URLs, not valid anymore since January 2021
#URL_FACTBOOK = 'https://www.cia.gov/library/publications/the-world-factbook/appendix/appendix-d.html'
#URL_PREF     = 'https://www.cia.gov/library/publications/the-world-factbook/geos/'

URL_FACTBOOK  = 'https://www.cia.gov/the-world-factbook/page-data/references/country-data-codes/page-data.json'
URL_PREF      = 'https://www.cia.gov/the-world-factbook/countries/'
URL_PREF_JSON = 'https://www.cia.gov/the-world-factbook/page-data/countries/'


REC_COUNTRY  = {
    'name'  : '',
    'url'   : '',
    'json'  : '',
    'genc'  : '',
    'cc2'   : '',
    'cc3'   : '',
    'ccn'   : '',
    'stan'  : '', 
    'tld'   : '',
    'cmt'   : ''
    }


# this is a LUT for special case, where the country name from the country codes does not correspond
# to the country name in the rest of the WFB database
WFB_COUNTRY_LUT = {
    'South Georgia and the Islands' : 'south-georgia-and-south-sandwich-islands',
    }

# regexp to change crappy char in country name to - as used within url of the WFB
RE_WFB_URL = re.compile('[\s,\(\)]{1,}')

def country_name_to_url(s):
    if s in WFB_COUNTRY_LUT:
        return WFB_COUNTRY_LUT[s]
    else:
        ret = RE_WFB_URL.sub('-', s.lower()).replace('\'', '')
        if ret[-1:] == '-':
            ret = ret[:-1].strip()
        return ret

def parse_table_country_all():
    J = import_json_doc(URL_FACTBOOK)
    try:
        T = json.loads(J['result']['data']['page']['json'])['country_codes']
    except Exception as err:
        raise(Exception('> invalid json for WFB country data codes: %s' % err))
    #
    D   = {} 
    #
    for L in T:
        rec = dict(REC_COUNTRY)
        rec['name'] = L['entity']
        rec['genc'] = L['genc'].upper() if L['genc'] is not None and len(L['genc']) in {2, 3, 4} else ''
        rec['cc2']  = L['iso_code_1'].upper() if L['iso_code_1'] is not None and len(L['iso_code_1']) == 2 else ''
        rec['cc3']  = L['iso_code_2'].upper() if L['iso_code_2'] is not None and len(L['iso_code_2']) == 3 else ''
        rec['ccn']  = L['iso_code_3'].upper() if L['iso_code_3'] is not None and len(L['iso_code_3']) == 3 else ''
        rec['stan'] = L['stanag_code'].upper() if L['stanag_code'] is not None and len(L['stanag_code']) == 3 else ''
        rec['tld']  = L['internet_code'].lower() if L['internet_code'] is not None and len(L['internet_code']) >= 3 else ''
        rec['cmt']  = L['comment'] if L['comment'] else ''
        #
        # build the country URL from the country name
        cntr_name   = country_name_to_url(L['entity'])
        rec['url']  = URL_PREF + cntr_name
        rec['json'] = URL_PREF_JSON + cntr_name + '/page-data.json'
        #
        rec['infos'] = parse_json_country(rec['json'])
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


def parse_json_country(url):
    # the web server may not be fully responsive when we scan all URLs,
    # let's do some sleep / retry
    J, err = None, 0
    while J is None and err < 3:
        if err:
            time.sleep(2)
        try:
            J = json.loads(import_json_doc(url)['result']['data']['country']['json'])
        except Exception as exc:
            err += 1
    if J is None:
        return {}
    #
    D = {}
    # warning: for some country url, the HTML structure is inconsistent
    _extract_sections(J, D)
    return D


# JSON section title, and sub-section id
# structure of titles and ids:
#
# - Introduction
#   - background
# - Geography
#   - location
#   - geographic-coordinates
#   - map-references
#   - area
#   - area-comparative
#   - land-boundaries
#   - coastline
#   - maritime-claims
#   - climate
#   - terrain
#   - elevation
#   - natural-resources
#   - land-use
#   - irrigated-land
#   - population-distribution
#   - natural-hazards
#   - environment-current-issues
#   - environment-international-agreements
#   - geography-note
# - People and Society
#   - population
#   - nationality
#   - ethnic-groups
#   - languages
#   - religions
#   - demographic-profile
#   - age-structure
#   - dependency-ratios
#   - median-age
#   - population-growth-rate
#   - birth-rate
#   - death-rate
#   - net-migration-rate
#   - population-distribution
#   - urbanization
#   - major-urban-areas-population
#   - sex-ratio
#   - maternal-mortality-rate
#   - infant-mortality-rate
#   - life-expectancy-at-birth
#   - total-fertility-rate
#   - contraceptive-prevalence-rate
#   - drinking-water-source
#   - current-health-expenditure
#   - physicians-density
#   - hospital-bed-density
#   - sanitation-facility-access
#   - hiv-aids-adult-prevalence-rate
#   - hiv-aids-people-living-with-hiv-aids
#   - hiv-aids-deaths
#   - major-infectious-diseases
#   - obesity-adult-prevalence-rate
#   - children-under-the-age-of-5-years-underweight
#   - education-expenditures
#   - literacy
#   - school-life-expectancy-primary-to-tertiary-education
#   - unemployment-youth-ages-15-24
# - Government
#   - country-name
#   - government-type
#   - capital
#   - administrative-divisions
#   - independence
#   - national-holiday
#   - constitution
#   - legal-system
#   - international-law-organization-participation
#   - citizenship
#   - suffrage
#   - executive-branch
#   - legislative-branch
#   - judicial-branch
#   - political-parties-and-leaders
#   - international-organization-participation
#   - diplomatic-representation-in-the-us
#   - diplomatic-representation-from-the-us
#   - flag-description
#   - national-symbols
#   - national-anthem
# - Economy
#   - economic-overview
#   - gdp-real-growth-rate-2
#   - inflation-rate-consumer-prices
#   - credit-ratings
#   - gdp-purchasing-power-parity-real
#   - gdp-official-exchange-rate
#   - gdp-per-capita-ppp
#   - gross-national-saving
#   - gdp-composition-by-sector-of-origin
#   - gdp-composition-by-end-use
#   - ease-of-doing-business-index-scores
#   - agriculture-products
#   - industries
#   - industrial-production-growth-rate
#   - labor-force
#   - labor-force-by-occupation
#   - unemployment-rate
#   - population-below-poverty-line
#   - household-income-or-consumption-by-percentage-share
#   - budget
#   - taxes-and-other-revenues
#   - budget-surplus-or-deficit
#   - public-debt
#   - fiscal-year
#   - current-account-balance
#   - exports
#   - exports-partners
#   - exports-commodities
#   - imports
#   - imports-commodities
#   - imports-partners
#   - reserves-of-foreign-exchange-and-gold
#   - debt-external
#   - exchange-rates
# - Energy
#   - electricity-access
#   - electricity-production
#   - electricity-consumption
#   - electricity-exports
#   - electricity-imports
#   - electricity-installed-generating-capacity
#   - electricity-from-fossil-fuels
#   - electricity-from-nuclear-fuels
#   - electricity-from-hydroelectric-plants
#   - electricity-from-other-renewable-sources
#   - crude-oil-production
#   - crude-oil-exports
#   - crude-oil-imports
#   - crude-oil-proved-reserves
#   - refined-petroleum-products-production
#   - refined-petroleum-products-consumption
#   - refined-petroleum-products-exports
#   - refined-petroleum-products-imports
#   - natural-gas-production
#   - natural-gas-consumption
#   - natural-gas-exports
#   - natural-gas-imports
#   - natural-gas-proved-reserves
#   - carbon-dioxide-emissions-from-consumption-of-energy
# - Communications
#   - telephones-fixed-lines
#   - telephones-mobile-cellular
#   - telecommunication-systems
#   - broadcast-media
#   - internet-country-code
#   - internet-users
#   - broadband-fixed-subscriptions
# - Transportation
#   - national-air-transport-system
#   - civil-aircraft-registration-country-code-prefix
#   - airports
#   - airports-with-paved-runways
#   - airports-with-unpaved-runways
#   - heliports
#   - pipelines
#   - railways
#   - roadways
#   - waterways
#   - merchant-marine
#   - ports-and-terminals
# - Military and Security
#   - military-and-security-forces
#   - military-expenditures
#   - military-and-security-service-personnel-strengths
#   - military-equipment-inventories-and-acquisitions
#   - military-deployments
#   - military-service-age-and-obligation
#   - military-note
# - Transnational Issues
#   - disputes-international
#   - refugees-and-internally-displaced-persons
#   - illicit-drugs

RE_NOTE  = re.compile('[nN]ote\s{0,}:')


RE_SPACE = re.compile('\s{1,}')

def _strip_str(s):
    return RE_SPACE.sub(' ', s).strip()


RE_HTML_BR = re.compile('<br[\s/]{0,}>')
 
def _strip_html_br(s):
    return RE_HTML_BR.sub('', s)


def _extract_geo_mult(s):
    r = []
    for ssub in s.split(';'):
        if ':' in ssub:
            r.append( tuple(map(_strip_str, ssub.split(':'))) )
        else:
            r.insert(0, _strip_str(ssub))
    return r


def _extract_area(l):
    r = {}
    for s in l:
        try:
            name, s = map(_strip_str, s.split(':', 1))
        except ValueError:
            # not a named section
            assert( 'note' not in r )
            r['note'] = _strip_str(s)
        else:
            m = RE_NOTE.search(s)
            if m:
                assert( 'note' not in r )
                r['note'] = s[m.end():].strip()
                s = s[:m.start()].strip()
            r[name] = s
    return r


# 3 kinds of border notation:
# "border countries (15):", "border sovereign base areas:", "regional borders (1):"

RE_DIST = re.compile('([0-9]{1,}[,0-9]{0,})\s{0,}(?:km){0,1}')
RE_BORD = re.compile('(?:regional ){0,1}border(?:s){0,1}(?: countries| sovereign base areas|)(?:\s\(([0-9]{1,})\)){0,1}:')

def _extract_bound(l):
    r = {'bord': {}}
    for s in l:
        if 'border' in s:
            m = RE_BORD.match(s)
            if m:
                num = m.group(1)
                s = s.split(':', 1)[1].strip()
                m = RE_NOTE.search(s)
                if m:
                    assert( 'note' not in r )
                    r['note'] = s[m.end():].strip()
                    s = s[:m.start()].strip()
                countries = list(map(_strip_str, s.split(';')))
                for country in countries:
                    m = RE_DIST.search(country)
                    if m:
                        r['bord'][country[:m.start()].strip()] = int(m.group(1).replace(',', ''))
                    else:
                        print('> missing boundary length: %s' % country)
                        r['bord'][country] = 0
                if num is not None and int(num) != len(r['bord']):
                    #assert()
                    print('> boundary number mismatch: %s / %r' % (num, r['bord']))
        elif 'total' in s:
            dist = s.split(':', 1)[1].strip().replace(',', '')
            m = RE_DIST.match(dist)
            if m and 'len' not in r:
                r['len'] = int(m.group(1))
    _consolidate_bound(r)
    return r

def _consolidate_bound(r):
    if not r['bord'] and 'len' not in r:
        r['len'] = 0
    elif r['bord']:
        bord = r['bord']
        upd  = {}
        # fix in case multiple entries for a single country
        for c, l in bord.items():
            name = _stripbordref(c)
            if name != c:
                if 'note' not in r:
                    r['note'] = 'border with %s' % c
                else:
                    r['note'] += '; border with %s' % c
            if name in upd:
                upd[name] += l
            else:
                upd[name] = l
        r['bord'] = upd


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


def _extract_country_name(l):
    r = {}
    for s in l:
        if s.startswith('conventional short'):
            r['conv_short']  = _strip_str(s.split(':', 1)[1])
        elif s.startswith('conventional long'):
            r['conv_long']   = _strip_str(s.split(':', 1)[1])
        elif s.startswith('local short'):
            r['local_short'] = _strip_str(s.split(':', 1)[1])
        elif s.startswith('local long'):
            r['local_long']  = _strip_str(s.split(':', 1)[1])
    return r


RE_TIME_DIFF = re.compile('UTC\s{0,}[\-\+\.0-9]{0,}')

def _extract_capital(l):
    r = {}
    for s in l:
        if s.startswith('name'):
            r['name'] = _strip_str(s.split(':', 1)[1])
        elif s.startswith('time diff'):
            m = RE_TIME_DIFF.match(s.split(':', 1)[1].strip())
            if m:
                r['time_diff'] = m.group()
        elif s.startswith('geographic coord'):
            r['coord'] = _strip_str(s.split(':', 1)[1])
    return r


def _extract_total_value(l):
    for s in l:
        if s.startswith('total'):
            return _extract_value(s.split(':', 1)[1].strip())
    return ''


RE_COUNTRY_CODE = re.compile('^country code - ([0-9\-]{1,5})')
RE_YEAR         = re.compile('\(\s{0,}(20[0-9]{2})\s{0,}(est\.{0,1}){0,1}\)$')

def _extract_tel_year(s):
    m = RE_YEAR.search(s)
    if m:
        year = int(m.group(1))
        s = s[:m.start()].strip()
    else:
        year = 0
    return [p for p in map(_strip_str, s.split(';')) if p] + [year]

def _extract_tel(l):
    r = {}
    for s in l:
        # it seems some "&rsquo;" expr remains in textual description
        s = s.replace('&rsquo;', '\'') 
        if s.startswith('general assess'):
            r['general'] = _extract_tel_year(s.split(':', 1)[1].strip())
        elif s.startswith('domestic'):
            r['domestic'] = _extract_tel_year(s.split(':', 1)[1].strip())
        elif s.startswith('international'):
            s = s.split(':', 1)[1].strip()
            m = RE_COUNTRY_CODE.match(s)
            if m:
                s = s[m.end():].strip()
                r['code'] = m.group(1).replace('-', '')
            r['intl'] = _extract_tel_year(s)
        else:
            name, s = map(str.strip, s.split(':', 1))
            r[name] = _extract_tel_year(s)
    return r


def _extract_ports(l):
    r = {}
    for s in l:
        if s.startswith('major seaport'):
            r['seaport']   = _strip_html_br(_strip_str(s.split(':', 1)[1]))
        elif s.startswith('container port'):
            r['container'] = _strip_html_br(_strip_str(s.split(':', 1)[1]))
        elif s.startswith('cruise/ferry'):
            r['ferry']     = _strip_html_br(_strip_str(s.split(':', 1)[1]))
    return r


COUNTRY_SECTIONS = {
    'Geography': {
        'geographic-coordinates'    : ('coord',         _extract_geo_mult),
        'map-references'            : ('region',        _extract_geo_mult),
        'area'                      : ('area',          _extract_area),
        'land-boundaries'           : ('boundaries',    _extract_bound),
        'coastline'                 : ('coastline',     _extract_value),
        },
    'People and Society': {
        'population'                : ('population',    _extract_value),
        },
    'Government': {
        'country-name'              : ('country_name',  _extract_country_name),
        'capital'                   : ('capital',       _extract_capital),
        },
    'Communications': {
        'telephones-fixed-lines'        : ('subs_fixed',        _extract_total_value),
        'telephones-mobile-cellular'    : ('subs_mobile',       _extract_total_value),
        'telecommunication-systems'     : ('telecom',           _extract_tel),
        'internet-users'                : ('users_internet',    _extract_total_value),
        'broadband-fixed-subscriptions' : ('subs_broadband',    _extract_total_value),
        },
    'Transportation': {
        'airports'                  : ('airports',      _extract_total_value),
        'ports-and-terminals'       : ('ports',         _extract_ports),
        }
    }


RE_HTML_CMT   = re.compile('<\!--.*-->')
RE_HTML_SPAN  = re.compile('<span\s.*>')
RE_HTML_STYLE = re.compile('</{0,1}(strong|p)>')
RE_HTML_GLYPH = re.compile('&[a-zA-Z];')
 
def _strip_html(s):
    ret = RE_HTML_CMT.sub(' ', s)
    ret = RE_HTML_SPAN.sub(' ', ret)
    ret = RE_HTML_STYLE.sub(' ', ret)\
          .replace('&nbsp;', ' ')\
          .replace('&amp;', '&')\
          .strip()
    ret = re.sub('\s{1,}', ' ', ret)
    m = RE_HTML_GLYPH.search(ret)
    if m:
        print('> found more HTML expr: %s' % m.group())
    return ret


def _extract_sections(J, D):
    for section in J['categories']:
        if section['title'] in COUNTRY_SECTIONS:
            subsel = COUNTRY_SECTIONS[section['title']]
            for subsection in section['fields']:
                if subsection['id'] in subsel:
                    selname, cb = subsel[subsection['id']]
                    #print('- %s' % subsection['id'])
                    #
                    if 'subfields_raw' in subsection:
                        subs = list(map(str.strip, subsection['subfields_raw'].split(', ')))
                        cont = list(map(_strip_html, subsection['content'].split('<br><br>')))
                        D[selname] = cb(cont)
                        #print('  - subs: %s' % ', '.join(subs))
                        #print('  - cont:')
                        #for c in cont:
                        #    print('    - %s' % c)
                    else:
                        cont = _strip_html(subsection['content'])
                        D[selname] = cb(cont)
                        #print('  - cont: %s' % cont)


#------------------------------------------------------------------------------#
# Main
#------------------------------------------------------------------------------#

URL_LICENSE = "https://www.cia.gov/the-world-factbook/about/copyright-and-contributors/"

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
