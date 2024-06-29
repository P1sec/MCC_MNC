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

DEBUG = 1

# old URLs, not valid anymore since January 2021
#URL_FACTBOOK = 'https://www.cia.gov/library/publications/the-world-factbook/appendix/appendix-d.html'
#URL_PREF     = 'https://www.cia.gov/library/publications/the-world-factbook/geos/'

URL_FACTBOOK  = 'https://www.cia.gov/the-world-factbook/page-data/references/country-data-codes/page-data.json'
URL_PREF      = 'https://www.cia.gov/the-world-factbook/countries/'
URL_PREF_JSON = 'https://www.cia.gov/the-world-factbook/page-data/countries/'

# this is a LUT for special cases, where the country name from the country codes does not correspond
# to the country name in the rest of the WFB database
WFB_COUNTRY_LUT = {
    'Baker Island' : 'united-states-pacific-island-wildlife-refuges',
    'Howland Island' : 'united-states-pacific-island-wildlife-refuges',
    'Jarvis Island' : 'united-states-pacific-island-wildlife-refuges',
    'Johnston Atoll' : 'united-states-pacific-island-wildlife-refuges',
    'Kingman Reef' : 'united-states-pacific-island-wildlife-refuges',
    'Midway Islands' : 'united-states-pacific-island-wildlife-refuges',
    'Palmyra Atoll' : 'united-states-pacific-island-wildlife-refuges',
    'Virgin Islands (US)' : 'virgin-islands',
    'South Georgia and the Islands' : 'south-georgia-and-south-sandwich-islands',
    'Akrotiri' : 'akrotiri-and-dhekelia',
    'Dhekelia' : 'akrotiri-and-dhekelia',
    'Zaire' : 'democratic-republic-of-the-congo'
    }


# model for the base dict extracted from the WFB
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

def parse_table_country_all(idx=(0, None)):
    J = import_json_doc(URL_FACTBOOK)
    try:
        T = J['result']['data']['appendix']['entries']
    except Exception as err:
        raise(Exception('> invalid json for WFB country data codes: %r' % err))
    #
    D   = {} 
    #
    for L in T[idx[0]:idx[1]]:
        rec = dict(REC_COUNTRY)
        for f in L['fields']:
            if f['attribute'] == 'name':
                rec['name'] = f['value']
                if DEBUG:
                    print('processing for %s' % f['value'])
            elif f['attribute'] == 'genc':
                v = f['value'].upper().strip()
                if len(v) in {2, 3, 4} and v.isalpha():
                    rec['genc'] = v
                else:
                    if DEBUG:
                        print('%s, GENC: %s' % (rec['name'], v))
                    rec['genc'] = ''
            elif f['attribute'] == 'iso3166':
                v = tuple(map(str.strip, f['value'].upper().split('|')))
                if len(v) == 3 and len(v[0]) == 2 and v[0].isalpha() and len(v[1]) == 3 and v[1].isalpha() \
                and len(v[2]) == 3 and v[2].isdigit():
                    rec['cc2'], rec['cc3'], rec['ccn'] = v
                else:
                    if DEBUG:
                        print('%s, ISO: %r' % (rec['name'], v))
                    rec['cc2'], rec['cc3'], rec['ccn'] = '', '', ''
            elif f['attribute'] == 'stanag':
                v = f['value'].upper().strip()
                if len(v) == 3 and v.isalpha():
                    rec['stan'] = v
                else:
                    if DEBUG:
                        print('%s, Stanag: %s' % (rec['name'], v))
                    rec['stan'] = ''
            elif f['attribute'] == 'internet':
                v = f['value'].lower().strip()
                if v[0:1] == '.' and len(v) >= 3:
                    rec['tld'] = v
                else:
                    if DEBUG:
                        print('%s, TLD: %s' % (rec['name'], v))
                    rec['tld'] = ''
            elif f['attribute'] == 'comment':
                if f['value']:
                    rec['cmt'] = f['value'].strip()
                else:
                    rec['cmt'] = ''
        #
        # build the country URL from the country name
        cntr_name   = country_name_to_url(rec['name'])
        rec['url']  = URL_PREF + cntr_name + '/'
        rec['json'] = URL_PREF_JSON + cntr_name + '/page-data.json'
        #
        rec['infos'] = parse_json_country(rec['json'])
        if not rec['infos']:
            print('> web page does not exist for %s' % rec['name'])
        else:
            print('> infos extracted for %s' % rec['name'])
        #
        if DEBUG > 1:
            print(L, rec)
        if rec['name'] in D:
            raise(Exception('> duplicate entry for country %s' % rec['name']))
        else:
            D[rec['name']] = rec
        if DEBUG:
            print(80*'-')
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
            J = import_json_doc(url)['result']['data']
            # J['country'], J['fields']
        except Exception as exc:
            err += 1
    if J is None:
        return {}
    #
    D = {}
    # warning: for some country url, the HTML structure is inconsistent
    _extract_sections(J, D)
    return D


# JSON section title, and sub-section id, from 2023/02/14
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


# Common and generic stripping and extraction routines

RE_NOTE  = re.compile('[nN]ote\s{0,}:')
RE_SPACE = re.compile('\s{1,}')

def _strip_str(s):
    return RE_SPACE.sub(' ', s).strip()


RE_HTML_BR    = re.compile('<br[\s/]{0,}>')
RE_HTML_EMIN  = re.compile('<em>')
RE_HTML_EMOUT = re.compile('</em>')
 
def _strip_html_brem(s):
    # strip <br> and </em>
    s = RE_HTML_EMOUT.sub('', RE_HTML_BR.sub('', s)).strip()
    # strip <em> when at offset 0, otherwise replace it with ;
    if s.startswith('<em>'):
        s = s[4:].lstrip()
    s = RE_HTML_EMIN.sub('; ', s)
    return s.strip()


def _extract_uint(s):
    return int(s.strip().replace(',', '').replace('.', ''))


# Dedicated extraction routines

def _extract_geo_mult(s):
    r = []
    for ssub in s.split(';'):
        if ':' in ssub:
            r.append( tuple(map(_strip_str, ssub.split(':'))) )
        else:
            r.insert(0, _strip_str(ssub))
    return r

# HTML <strong> and <p> are stripped early on all data fields
#RE_HTML_STRONG = re.compile('</{0,1}strong>')

def _extract_mult_kv(txt):
    r, year = {}, None
    sep = '<br><br>'
    if '<br><br>' not in txt:
        if txt.count('<br /><br />') > 2:
            sep = '<br /><br />'
        elif txt.count('<br />') > 2:
            sep = '<br />'
    for s in map(str.strip, txt.split(sep)):
        #s = RE_HTML_STRONG.sub('', s).strip()
        try:
            name, s = map(_strip_str, s.split(':', 1))
        except ValueError:
            s = _strip_str(s)
            if s:
                # not a named section, keep it as note
                if 'note' in r:
                    r['note'].append( _strip_str(s) )
                else:
                    r['note'] = [_strip_str(s)]
        else:
            m = RE_NOTE.search(s)
            if m:
                note = s[m.end():].strip()
                s = s[:m.start()].strip()
                if 'note' in r:
                    r['note'].append(note)
                else:
                    r['note'] = [note]
            #
            if name == 'key ports':
                r[name] = s
            elif name == 'note':
                if 'note' in r:
                    r['note'].append(s)
                else:
                    r['note'] = [s]
            else:
                v = _extract_value(s)
                if 'year' in v:
                    year = v['year']
                if v['num'] == 0 and len(s) > 10:
                    # we have some comments we want to keep
                    r[name] = s
                else:
                    r[name] = v['num']
    if year:
        r['year'] = year
    return r


# 3 kinds of border notation:
# "border countries (15):", "border sovereign base areas:", "regional borders (1):"

RE_DIST = re.compile('([0-9]{1,}[,0-9]{0,})\s{0,}(?:km){0,1}')
RE_BORD = re.compile('(?:regional ){0,1}border(?:s){0,1}(?: countries| sovereign base areas|)(?:\s\(([0-9]{1,})\)){0,1}:')

def _extract_bound(l):
    r = {'bord': {}}
    for s in map(str.strip, l.split('<br><br>')):
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
        else:
            print('> unprocessed boundary declaration: %s' % s)
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
    r = {}
    #s = _strip_str(RE_HTML_STRONG.sub('', s))
    s = _strip_str(s)
    # the year could eventually comes 1st or last, so we process it and strip it 1st
    m = RE_YEAR.search(s)
    if m:
        r['year'] = int(m.group(1))
        s = str.strip(s[:m.start()] + s[m.end():])
    if s[:6].lower() == 'approx':
        # remove 1st word
        s = s.split(' ', 1)[1].strip()
    m = RE_INTEG_VAL.match(s)
    if m:
        v = float(m.group(1).replace(',', ''))
        if m.group(2):
            r['num'] = int(v * 1000000)
        else:
            r['num'] = int(v)
    else:
        r['num'] = 0
    return r


def _extract_coastline(s):
    r = _extract_value(s)
    if r['num'] == 0 and len(s) > 20:
        # some islands have detailed coastlines
        r = _extract_mult_kv(s)
    return r


def _extract_country_name(s):
    r = {}
    for l in map(str.strip, s.split('<br><br>')):
        if l.startswith('conventional short'):
            r['conv_short']  = _strip_str(l.split(':', 1)[1])
        elif l.startswith('conventional long'):
            r['conv_long']   = _strip_str(l.split(':', 1)[1])
        elif l.startswith('local short'):
            r['local_short'] = _strip_str(l.split(':', 1)[1])
        elif l.startswith('local long'):
            r['local_long']  = _strip_str(l.split(':', 1)[1])
    return r


RE_TIME_DIFF = re.compile('UTC\s{0,}[\-\+\.0-9]{0,}')

def _extract_capital(s):
    r = {}
    for l in map(str.strip, s.split('<br><br>')):
        if l.lower().startswith('name'):
            r['name'] = _strip_str(l.split(':', 1)[1])
        elif l.lower().startswith('geographic coord'):
            r['coord'] = _strip_str(l.split(':', 1)[1])
        elif l.lower().startswith('time diff'):
            m = RE_TIME_DIFF.match(l.split(':', 1)[1].strip())
            if m:
                r['time_diff'] = m.group()
    return r


def _extract_total_value(s):
    if '<br><br>' in s:
        lines = s.split('<br><br>')
    else:
        lines = s
    for l in lines:
        if l.startswith('total'):
            return _extract_value(s.split(':', 1)[1].strip())
    return ''


RE_COUNTRY_CODE = re.compile('^country code - ([0-9\-]{1,5})')
RE_YEAR         = re.compile('\(\s{0,}(20[0-9]{2})\s{0,}(est\.{0,1}){0,1}\s{0,}\)')

def _extract_tel_year(s):
    m = RE_YEAR.search(s)
    if m:
        year = int(m.group(1))
        s = s[:m.start()].rstrip()
    else:
        year = 0
    return [p for p in map(_strip_str, s.split(';')) if p] + [year]

def _extract_tel(txt):
    r = {}
    for s in map(str.strip, txt.split('<br><br>')):
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
            try:
                name, s = map(str.strip, s.split(':', 1))
                r[name] = _extract_tel_year(s)
            except Exception:
                pass
    return r


def __old_extract_ports(l):
    r = {}
    for s in map(str.strip, l.split('<br><br>')):
        s = _strip_str(s)
        # TODO: we need to strip <em></em>
        if s.startswith('major seaport'):
            r['seaport']   = _strip_html_brem(_strip_str(s.split(':', 1)[1]))
        elif s.startswith('container port'):
            r['container'] = _strip_html_brem(_strip_str(s.split(':', 1)[1]))
        elif s.startswith('cruise/ferry'):
            r['ferry']     = _strip_html_brem(_strip_str(s.split(':', 1)[1]))
    return r


def _extract_anyports(s):
    r = {}
    if '<br><br>' in s:
        s = s.split('<br><br>', 1)[0]
    if s[0:1].isdigit():
        # we have a number
        return _extract_value(s)
    return r


COUNTRY_SECTIONS = {
    # 2023/09/15: new flat data model
    'Geographic coordinates':           ('coord',           _extract_geo_mult),
    'Capital':                          ('capital',         _extract_capital),
    'Coastline':                        ('coastline',       _extract_coastline),
    'Land boundaries':                  ('boundaries',      _extract_bound),
    'Ports':                            ('ports',           _extract_mult_kv),
    'Telecommunication systems':        ('telecom',         _extract_tel),
    'Country name':                     ('country_name',    _extract_country_name),
    'Map references':                   ('region',          _extract_geo_mult),
    'Population':                       ('population',      _extract_mult_kv),
    'Internet users':                   ('users_internet',  _extract_total_value),
    'Area':                             ('area',            _extract_mult_kv),
    'Airports':                         ('airports',        _extract_anyports),
    'Heliports':                        ('heliports',       _extract_anyports),
    'Telephones - mobile cellular':     ('subs_mobile',     _extract_total_value),
    'Broadband - fixed subscriptions':  ('subs_broadband',  _extract_total_value),
    'Telephones - fixed lines':         ('subs_fixed',      _extract_total_value),
    'Roadways':                         ('roadways',        _extract_mult_kv),
    #
    # other items of interest:
    #'Major urban areas - population'
    #'Languages'
    #'Median age'
    #'Disputes - international'
    #'Merchant marine'
    #'Railways'
    #'Pipelines'
    #'Natural resources'
    #'Elevation'
    #'National holiday'
    #'Broadcast media'
    }

RE_HTML_CMT   = re.compile('<\!--.*-->')
RE_HTML_SPAN  = re.compile('<span\s.*>')
RE_HTML_STYLE = re.compile('</{0,1}(strong|p)>')
RE_HTML_GLYPH = re.compile('\&[a-zA-Z]{1,};')
TXT_HTML_TR   = {
    '&ldquo;'   : '“',
    '&rdquo;'   : '”',
    '&lsquo;'   : '‘',
    '&rsquo;'   : '’',
    '&mdash;'   : '—',
    '&ndash;'   : '–',
    '&ocirc;'   : 'ô',
    '&iacute;'  : 'í',
    '&Oacute;'  : 'Ó',
    '&uacute;'  : 'ú',
    '&nbsp;'    : ' ',
    '&amp;'     : '&',
    '&deg;'     : '°',
    }


def _strip_html(s):
    ret = RE_HTML_CMT.sub(' ', s)
    ret = RE_HTML_SPAN.sub(' ', ret)
    ret = RE_HTML_STYLE.sub(' ', ret).strip()
    ret = re.sub('\s{1,}', ' ', ret)
    for html, glyph in TXT_HTML_TR.items():
        if html in ret:
            ret = ret.replace(html, glyph)
    m = RE_HTML_GLYPH.search(ret)
    if m:
        print('> found more HTML expr: %s' % m.group())
    return ret


def _extract_sections(J, D):
    # go over all the "nodes" in "fields"
    for node in J['fields']['nodes']:
        if DEBUG > 1:
            print('= %s: %r' % (node['name'], node['data']))
        if node['name'] in COUNTRY_SECTIONS:
            fname, cb = COUNTRY_SECTIONS[node['name']]
            data = _strip_html(node['data'])
            if DEBUG:
                print('- %s: %s' % (fname, data))
            D[fname] = cb(data)
    #
    # consolidate airports and airports_paved
    if 'airports_paved' in D and D['airports_paved']:
        if 'airports' not in D:
            assert()
        D['airports']['paved'] = D['airports_paved']['num']
        del D['airports_paved']


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
        print('> error occured: %r' % err)
        return 1
    #
    if args.j:
        generate_json(D, PATH_PRE + 'world_fb.json', [URL_FACTBOOK], URL_LICENSE)
    if args.p:
        generate_python(D, PATH_PRE + 'world_fb.py', [URL_FACTBOOK], URL_LICENSE)
    return 0


if __name__ == '__main__':
    sys.exit(main())
