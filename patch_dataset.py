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
# * File Name : patch_dataset.py
# * Created : 2020-09-14
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


__all__ = [
    # Wikipedia structures
    'WIKIP_ISO3166',
    'WIKIP_BORDERS',
    'WIKIP_MCC',
    'WIKIP_MNC',
    'WIKIP_MSISDN',
    'WIKIP_COUNTRY',
    'WIKIP_TERRITORY',
    # World Factbook structure
    'WORLD_FB',
    # Egallic minimum distance
    'CSV_EGAL_MIN_DIST',
    # txtNation list of MCCMNC
    'CSV_TXTN_MCCMNC',
    # ITU-T MNC lists
    'ITUT_MNC_1111',
    'ITUT_MNC_1162',
    'ITUT_SPC_1199',
    # Custom structures
    'WFB_UNINHABITED',
    'COUNTRY_SPEC',
    'CC2_ALIAS',
    'CC2_INTL',
    # functions
    'country_name_canon',
    'country_match',
    'country_match_set',
    'country_present',
    ]


import os
import re
import csv

from parse_wikipedia_tables     import (
    REC_ISO3166,
    REC_MCC,
    REC_MNC,
    REC_BORDERS,
    )
from parse_worldfactbook_infos  import (
    REC_COUNTRY,
    )
from patch_country_dep          import COUNTRY_SPEC

try:
    from raw.wikip_borders      import WIKIP_BORDERS
    from raw.wikip_iso3166      import WIKIP_ISO3166
    from raw.wikip_mcc          import WIKIP_MCC
    from raw.wikip_mnc          import WIKIP_MNC
    from raw.wikip_msisdn       import WIKIP_MSISDN
    from raw.wikip_country      import WIKIP_COUNTRY
    from raw.wikip_territory    import WIKIP_TERRITORY
except ImportError:
    raise(Exception('error: please run first ./parse_wikipedia_tables.py'))
try:
    from raw.world_fb           import WORLD_FB
except ImportError:
    raise(Exception('error: please run first ./parse_worldfactbook_infos.py'))
try:
    from raw.csv_egal_min_dist  import CSV_EGAL_MIN_DIST
    from raw.csv_txtn_mccmnc    import CSV_TXTN_MCCMNC
except ImportError:
    raise(Exception('error: please run first ./parse_various_csv.py'))
try:
    from raw.itut_mnc_1111      import ITUT_MNC_1111
    from raw.itut_mnc_1162      import ITUT_MNC_1162
    from raw.itut_spc_1199      import ITUT_SPC_1199
except ImportError:
    raise(Exception('error: please run first ./parse_itut_bulletins.py'))


__doc__ = """
This module is used as an "enhanced" loader for all Python dictionnaries generated
from raw data sources (ITU-T bulletins, Wikipedia, World Factbook, txtNation, Egallic blog).

It applies patches to some of the dictionnaries to solve specific conflicts and
political / geographical situations, align data values and ease further integration
"""


#------------------------------------------------------------------------------#
# functions to match country names
#------------------------------------------------------------------------------#

def country_name_canon(name):
    """returns a set of shorten / canonical names for the given country name `n'
    """
    name = name.lower()
    r = {name}
    if name.startswith('the '):
        name = name[4:].strip()
        assert(name)
        r.add(name)
    for expr in ('republic of', 'rep. of', 'rep of'):
        if name.startswith(expr):
            name = name[len(expr):].strip()
            assert(name)
            r.add(name)
    #
    m = re.search('\(.*?\)', name)
    if m and m.start() >= 5:
        name = name[:m.start()].strip()
        assert(name)
        r.add(name)
    #
    if '&' in name:
        r.add(name.replace('&', 'and'))
    if ',' in name:
        r.add(name.replace(',', ''))
    if '.' in name:
        r.add(name.replace('.', ''))
    if '*' in name:
        r.add(name.replace('*', ''))
    return r


def country_match(name1, name2):
    """returns True if both country names `name1' and `name2' have an equal 
    canonical form, else False
    """
    for n1 in country_name_canon(name1):
        if n1 in country_name_canon(name2):
            return True
    return False


def country_present(name1, nameset2):
    """returns True if one of the canonical form of country name `name1' is 
    matching one of the canonical form from the set of country names `nameset2',
    else False
    """
    for name2 in nameset2:
        if country_match(name1, name2):
            return True
    return False
            

def country_match_set(name, nameset):
    """returns True if country name `name' match one of the name within `nameset',
    else False
    """
    for n in country_name_canon(name):
        for nm in nameset:
            if nm == n:
                return True
    return False


#------------------------------------------------------------------------------#
# Wikipedia common changes
#------------------------------------------------------------------------------#

# Countries / CC2 for which ambiguities exist and some names and / or infos 
# of the data set need to be updated
# COUNTRY_SPEC is imported from the external file patch_country_dep.py


COUNTRY_SPEC_CC2 = [country for country in COUNTRY_SPEC if 'cc2' in COUNTRY_SPEC[country]]


COUNTRY_RENAME = {
    #
    # Europe
    'Bailiwick of Guernsey'     : 'Guernsey', # needed
    'Vatican City'              : 'Vatican',
    'Vatican City State'        : 'Vatican',
    'Holy See (Vatican City)'   : 'Vatican',
    'Holy See'                  : 'Vatican', # needed
    'UK'                        : 'United Kingdom',
    'Czech Rep.'                : 'Czech Republic',
    'Ireland'                   : 'Republic of Ireland', # needed
    'Vatican City State (Holy See)' : 'Vatican',
    'The Kingdom of the Netherlands': 'Netherlands', # needed
    'Macedonia'                 : 'North Macedonia',
    'The Former Yugoslav Republic of Macedonia': 'North Macedonia',
    #
    # Middle-East / Asia
    'Burma'                     : 'Myanmar',
    'Burma / Myanmar'           : 'Myanmar',
    'Laos P.D.R.'               : 'Laos',
    'Lao P.D.R.'                : 'Laos',
    'Viet Nam'                  : 'Vietnam',
    'Korea, North'              : 'North Korea',
    'Korea N., Dem. People\'s Rep.' : 'North Korea',
    'Korea, South'              : 'South Korea',
    'Korea S, Republic of'      : 'South Korea',
    'Brunei Darussalam'         : 'Brunei',
    'Macao, China'              : 'Macau',
    'Hong Kong, China'          : 'Hong Kong',
    'Palau (Republic of)'       : 'Palau',
    'People\'s Republic of China'   : 'China',
    'Artsakh'                   : 'Nagorno-Karabakh',
    'The Islamic Republic of Iran'  : 'Iran',
    'Iran (Islamic Republic of)'    : 'Iran', # needed
    'Palestine'                 : 'State of Palestine',
    'Palestine, State of'       : 'State of Palestine',
    'Palestinian Territory'     : 'State of Palestine',
    'UAE'                       : 'United Arab Emirates',
    #
    # Africa
    'Somaliland'                : 'Somalia',
    'Swaziland'                 : 'Eswatini',
    'Central African Rep.'      : 'Central African Republic',
    'Congo'                     : 'Republic of the Congo',
    'Republic of Congo'         : 'Republic of the Congo',
    'Congo, Republic'           : 'Republic of the Congo',
    'Congo, Dem. Rep.'          : 'Democratic Republic of the Congo',
    'Dem. Rep. of the Congo'    : 'Democratic Republic of the Congo',
    'Congo, Democratic Republic of the (Zaire)' : 'Democratic Republic of the Congo',
    'Côte d\'Ivoire'            : 'Ivory Coast',
    'Cote d\'Ivoire'            : 'Ivory Coast',
    'Gambia'                    : 'The Gambia', # needed
    #
    # America
    'US'                        : 'United States',
    'USA'                       : 'United States',
    'Wake Island, USA'          : 'Wake Island',
    'Argentina Republic'        : 'Argentina',
    #
    # Islands
    'Bahamas'                   : 'The Bahamas', # needed
    'Caribbean Netherlands'     : 'Bonaire, Saba and Sint Eustatius',
    'Curacao'                   : 'Curaçao',
    'Cocos (Keeling) Islands'   : 'Cocos Islands', # needed
    'São Tomé and Príncipe'     : 'Sao Tome and Principe', # needed
    'Micronesia'                : 'Federated States of Micronesia',
    'Reunion'                   : 'Réunion',
    'Saint Barthelemy'          : 'Saint Barthélemy',
    'Timor-Leste'               : 'East Timor',
    'Virgin Islands, British'   : 'British Virgin Islands',
    'Virgin Islands, US'        : 'United States Virgin Islands',
    'US Virgin Islands'         : 'United States Virgin Islands',
    'Madeira Islands'           : 'Madeira',
    'Svalbard'                  : 'Svalbard and Jan Mayen', # needed
    'Ascension Island'          : 'Ascension',
    'Heard Island'              : 'Heard Island and McDonald Islands', # needed
    'Midway Island, USA'        : 'Midway Island',
    'Dominican Rep.'            : 'Dominican Republic',
    'Northern Marianas'         : 'Northern Mariana Islands',
    'Chatham Island, New Zealand'   : 'Chatham Island',
    'Collectivity of Saint Martin'  : 'Saint Martin', # needed
    'Micronesia, Federated States of'       : 'Federated States of Micronesia',
    'French Southern and Antarctic Lands'   : 'French Southern Territories',
    #
    # others
    'International Networks (country code)' : 'International Networks' # needed
    }


#------------------------------------------------------------------------------#
# Wikipedia ISO3166 dict
#------------------------------------------------------------------------------#

# code alpha 2 to be added, which is an alias for another code
CC2_ALIAS = {
    'UK' : 'GB',
    }


# CC2 used for international organizations
CC2_INTL = {
    'EU',
    'XC',
    'XD',
    'XG',
    'XP',
    'XR',
    'XS',
    'XT',
    'XV',
    }


def patch_wikip_iso3166():
    print('[+] patch Wikipedia ISO3166 dict: WIKIP_ISO3166')
    #
    # 1) add entries
    for country, infos in sorted(COUNTRY_SPEC.items()):
        if 'cc2' in infos and infos['cc2'] not in WIKIP_ISO3166:
            r = dict(REC_ISO3166)
            for k in r:
                if k in infos:
                    r[k] = infos[k]
            r['country_name'] = country
            r['code_alpha_2'] = infos['cc2']
            if 'url' in infos:
                r['country_url'] = infos['url']
            WIKIP_ISO3166[r['code_alpha_2']] = r
            print('> CC2 %s, %s added' % (r['code_alpha_2'], r['country_name']))
    #
    for new, old in sorted(CC2_ALIAS.items()):
        if new not in WIKIP_ISO3166:
            WIKIP_ISO3166[new] = WIKIP_ISO3166[old]
            print('> CC2 %s, alias to %s' % (new, old))
    #
    # 1bis) add more entries, extracted from the international telephone numbering listing
    for pref, infos in sorted(WIKIP_MSISDN.items()):
        for cc2, name, url in sorted(infos):
            if cc2 not in WIKIP_ISO3166:
                r = dict(REC_ISO3166)
                r['code_alpha_2']  = cc2
                r['country_name']  = name
                r['country_url']   = url
                WIKIP_ISO3166[cc2] = r
                print('> CC2 %s, %s added from WIKIP_MSISDN' % (cc2, name))
    #
    # 2) patch country names
    for cc2, infos in sorted(WIKIP_ISO3166.items()):
        for oldname, newname in sorted(COUNTRY_RENAME.items()):
            if country_match(infos['country_name'], oldname): 
                infos['country_name'] = newname
                if newname in COUNTRY_SPEC_CC2:
                    assert( COUNTRY_SPEC[newname]['cc2'] == cc2 )
                    if 'url' in COUNTRY_SPEC[newname]:
                        infos['country_url'] = COUNTRY_SPEC[newname]['url']
                print('> CC2 %s, country name changed from %s to %s' % (cc2, oldname, newname))
    #
    # 3) ensure all tld are lower case, and CC codes are upper case
    for infos in WIKIP_ISO3166.values():
        infos['cc_tld']       = infos['cc_tld'].lower()
        infos['cc_tld_url']   = infos['cc_tld_url'].lower()
        infos['code_alpha_2'] = infos['code_alpha_2'].upper()
        infos['code_alpha_3'] = infos['code_alpha_3'].upper()
    #
    # 4) ensure all canon names do not collide
    names = [country_name_canon(r['country_name']) for r in \
             [WIKIP_ISO3166[cc2] for cc2 in sorted(WIKIP_ISO3166)]]
    for i, nameset in enumerate(names[:-1]):
        for name in nameset:
            for j, nameset_totest in enumerate(names[1+i:]):
                if name in nameset_totest:
                    print('> country name collision %s / %s'\
                          % (sorted(WIKIP_ISO3166)[i], sorted(WIKIP_ISO3166)[i+1+j]))
    #
    # 5) ensure all overseas, sub-territories and other geographic specificities
    # are referenced correctly, and verify sovereignity
    for country in COUNTRY_SPEC_CC2:
        cc2 = COUNTRY_SPEC[country]['cc2']
        wc  = WIKIP_ISO3166[cc2]
        if country != wc['country_name']:
            print('> CC2 %s, country name changed from %s to %s' % (cc2, wc['country_name'], country))
            wc['country_name'] = country
            if 'url' in COUNTRY_SPEC[country]:
                wc['country_url'] = COUNTRY_SPEC[country]['url']
        if 'sub_cc2' in COUNTRY_SPEC[country]:
            for cc2_s in COUNTRY_SPEC[country]['sub_cc2']:
                if cc2_s not in WIKIP_ISO3166:
                    print('> missing CC2 %s, part of %s' % (cc2_s, country))
                else:
                    wc_s = WIKIP_ISO3166[cc2_s]
                    
                    
                    if wc_s['sovereignity'] == '':
                        wc_s['sovereignity'] = cc2
                    elif wc_s['sovereignity'] != cc2:
                        print('> CC2 %s, %s, sovereignity mismatch %s / %s'\
                              % (cc2_s, wc_s['country_name'], wc_s['sovereignity'], cc2))
    #
    # 6) keep track of country name variants
    for cc2, infos in sorted(WIKIP_ISO3166.items()):
        infos['nameset'] = country_name_canon(infos['country_name'])
        if infos['state_name']:
            infos['nameset'].update( country_name_canon(infos['state_name']) )

patch_wikip_iso3166()


# extend COUNTRY_SPEC with sub-territories, which have their own CC2

def extend_country_spec():
    print('[+] patch COUNTRY_SPEC dict')
    for cc2, r in sorted(WIKIP_ISO3166.items()):
        if r['sovereignity'] in WIKIP_ISO3166:
            # country dependent from another one
            sov  = WIKIP_ISO3166[r['sovereignity']]
            if sov['country_name'] not in COUNTRY_SPEC:
                COUNTRY_SPEC[sov['country_name']] = {}
            sovs = COUNTRY_SPEC[sov['country_name']]
            if 'sub' not in sovs:
                sovs['sub'] = []
            if 'sub_cc2' not in sovs:
                sovs['sub_cc2'] = []
            if r['country_name'] not in sovs['sub']:
                sovs['sub'].append(r['country_name'])
                print('> country %s (%s) added under %s' % (r['country_name'], cc2, sov['country_name']))
            if cc2 not in sovs['sub_cc2']:
                sovs['sub_cc2'].append(cc2)

extend_country_spec()


SUBTERR_TO_COUNTRY = {}
for name, infos in COUNTRY_SPEC.items(): 
    if 'sub' in infos:
        for subname in infos['sub']:
            SUBTERR_TO_COUNTRY[subname] = name


#------------------------------------------------------------------------------#
# Wikipedia territory borders list
#------------------------------------------------------------------------------#

# territory name that needs to be deleted
BORD_COUNTRY_DEL = [
    #
    # Special administrative regions of China:
    # used in China's neighbours, corresponds to Macau and Hong-Kong which are also listed
    # no ref in other sources
    # => delete neighbours entry within China
    'Special administrative regions of China',
    #
    # Adam's Bridge:
    # used in India's neighbours, corresponds to border with Sri Lanka which is also listed
    # no ref in other sources
    # => delete neighbours entry within India
    'Adam\'s Bridge',
    #
    # Borders of India:
    # used in India's neighbours, corresponds to:
    # Nepal, Pakistan, China, Bangladesh, Bhutan, Sri Lanka, Afghanistan, Myanmar
    # which are already listed
    # no ref in other sources
    # => delete neighbours entry within India
    'Borders of India',
    ]


# territory names that are in duplicate to their oversea territories
BORD_DUP_DEL = [
    #
    # France:
    # 1st entry corresponds to metropolitan France
    # 2nd entry corresponds to France including all overseas territories: delete it
    'France',
    #
    # Netherlands:
    # 1st entry corresponds to metropolitan Netherlands
    # 2nd entry corresponds to the Kingdom of Netherlands including oversea territories: delete it
    #'Netherlands',
    # 2021/03/11: not anymore...
    #
    # United Kingdom:
    # 1st entry corresponds to metropolitan France
    # 2nd entry corresponds to France including all overseas territories: delete it
    'United Kingdom',
    ]


def patch_wikip_borders():
    print('[+] patch Wikipedia territory borders list: WIKIP_BORDERS')
    #
    # 1) patch names
    for r in WIKIP_BORDERS:
        for oldname, newname in sorted(COUNTRY_RENAME.items()):
            if country_match(r['country_name'], oldname): 
                r['country_name'] = newname
                if newname in COUNTRY_SPEC and 'url' in COUNTRY_SPEC[newname]:
                    r['country_url'] = COUNTRY_SPEC[newname]['url']
                print('> country name changed from %s to %s' % (oldname, newname))
        for n in r['neigh'][:]:
            for oldname, newname in sorted(COUNTRY_RENAME.items()):
                if country_match(n, oldname):
                    r['neigh'].remove(n)
                    r['neigh'].append(newname)
                    r['neigh'].sort()
                    print('> country %s, border changed from %s to %s'\
                          % (r['country_name'], oldname, newname))
        for s in r['country_sub'][:]:
            if country_match(s[0], r['country_name']):
                # simply remove territory
                r['country_sub'].remove(s)
            for oldname, newname in sorted(COUNTRY_RENAME.items()):
                if country_match(s[0], oldname):
                    if newname in COUNTRY_SPEC and 'url' in COUNTRY_SPEC[newname]:
                        new_s = (newname, COUNTRY_SPEC[newname])
                    else:
                        new_s = (newname, s[1])
                    r['country_sub'].remove(s)
                    r['country_sub'].append( new_s )
                    r['country_sub'].sort(key=lambda t: t[0])
                    print('> country %s, sub changed from %s to %s'\
                          % (r['country_name'], oldname, newname))
    #
    # 2) delete entries
    for r in WIKIP_BORDERS[:]:
        if r['country_name'] in BORD_COUNTRY_DEL:
            WIKIP_BORDERS.remove(r)
            print('> country %s deleted' % r['country_name'])
        elif r['country_name'] in BORD_DUP_DEL and r['country_sub']:
            WIKIP_BORDERS.remove(r)
            print('> duplicated country %s deleted' % r['country_name'])
            # ensure all sub-territories are referenced within COUNTRY_SPEC
            for name, url in r['country_sub']:
                if not country_present(name, COUNTRY_SPEC[r['country_name']]['sub']):
                    print('> country %s, sub-territory %s not present in COUNTRY_SPEC'\
                          % (r['country_name'], name))
        else:
            for n in r['neigh'][:]:
                if country_present(n[0], BORD_COUNTRY_DEL):
                    r['neigh'].remove(n)
                    print('> country %s, border %s deleted' % (r['country_name'], n[0]))
    #
    # 4) remove borders to FR, NL, UK when actually against an oversea territory
    # to enable conversion of WIKIP_BORDERS into a dict
    BD = {r['country_name']: r for r in WIKIP_BORDERS}
    assert( len(BD) == len(WIKIP_BORDERS) )
    for name in BORD_DUP_DEL:
        for r in WIKIP_BORDERS:
            for r_neigh in r['neigh'][:]:
                if country_match(r_neigh, name) \
                and not country_present(r['country_name'], BD[name]['neigh']):
                    # delete entry
                    r['neigh'].remove(r_neigh)
                    print('> country %s, neighbour %s removed' % (r['country_name'], r_neigh))
    #
    # 5) ensure all country / borders are in the ISO3166 dict
    isonames = set()
    [isonames.update(country_name_canon(r['country_name'])) for r in WIKIP_ISO3166.values()]
    for r in WIKIP_BORDERS:
        #
        if not any([name in isonames for name in country_name_canon(r['country_name'])]):
            if country_present(r['country_name'], SUBTERR_TO_COUNTRY):
                # warning: SUBTERR_TO_COUNTRY lookup could fail here
                print('> country %s, not present in ISO3166 dict but referenced as sub of %s'\
                      % (r['country_name'], SUBTERR_TO_COUNTRY[r['country_name']]))
            else:
                print('> country %s, not present in ISO3166 dict' % r['country_name'])
        #
        if r['country_name'] in COUNTRY_SPEC and 'bord' in COUNTRY_SPEC[r['country_name']]:
            # ensure those specific borders are correctly referenced
            for b in COUNTRY_SPEC[r['country_name']]['bord']:
                if b not in [n[0] for n in r['neigh']]:
                    print('> country %s, missing border %s' % (r['country_name'], b))
        #
        for n in r['neigh']:
            if not any([name in isonames for name in country_name_canon(n)]):
                if country_present(n, SUBTERR_TO_COUNTRY):
                    # warning: SUBTERR_TO_COUNTRY lookup could fail here
                    print('> country %s, border %s in not present in ISO3166 dict but referenced as sub of %s'\
                          % (r['country_name'], n, SUBTERR_TO_COUNTRY[n]))
                else:
                    print('> country %s, border %s in not present in ISO3166 dict'\
                          % (r['country_name'], n))
    
patch_wikip_borders()


#------------------------------------------------------------------------------#
# Wikipedia MCC and MNC lists
#------------------------------------------------------------------------------#

MCC_INTL = {
    '001',
    '901',
    '902',
    '991',
    '999',
    }


MCC_CC2_LUT = {
    #
    # Abhkazia CC2 is moved to its unofficial 2-letter code
    'GE-AB': 'AB',
    }


# Adds MNC aliases to existing MNOs 
MNC_ALIAS = {
    ('722', '070'): ('722', '07'),
    }    


def patch_wikip_mcc():
    print('[+] patch Wikipedia list of MCC: WIKIP_MCC')
    # patch country names and crappy CC2
    # ensure CC codes are upper case
    # and CC2 is in WIKIP_ISO3166 otherwise intl mcc
    for r in WIKIP_MCC:
        for oldname, newname in sorted(COUNTRY_RENAME.items()):
            if country_match(r['country_name'], oldname):
                r['country_name'] = newname
                if newname in COUNTRY_SPEC and 'url' in COUNTRY_SPEC[newname]:
                    r['country_url'] = COUNTRY_SPEC[newname]['url']
                print('> MCC %s, country name changed from %s to %s'\
                      % (r['mcc'], oldname, newname))
        #
        if r['code_alpha_2'] in MCC_CC2_LUT:
            r['code_alpha_2'] = MCC_CC2_LUT[r['code_alpha_2']]
        #
        r['code_alpha_2'] = r['code_alpha_2'].upper()
        if r['code_alpha_2']:
            assert( r['code_alpha_2'] in WIKIP_ISO3166 )
        else:
            assert( r['mcc'] in MCC_INTL )
        #
        # check mcc format
        assert( len(r['mcc']) == 3 and r['mcc'].isdigit() )
    
patch_wikip_mcc()


def patch_wikip_mnc():
    print('[+] patch Wikipedia list of MCC-MNC: WIKIP_MNC')
    #
    nameset = set()
    [nameset.update(country_name_canon(r['country_name'])) for r in WIKIP_ISO3166.values()]
    #
    # patch country names and ensure country name exists in iso3166 db (or align them)
    # ensure CC2 is upper case and in WIKIP_ISO3166
    # ensure CC2 is available when network is not intl
    logs = set()
    for mcc0 in sorted(WIKIP_MNC):
        for r in WIKIP_MNC[mcc0]:
            for oldname, newname in sorted(COUNTRY_RENAME.items()):
                if country_match(r['country_name'], oldname):
                    r['country_name'] = newname
                    print('> MCC %s MNC %s, country name changed from %s to %s'\
                          % (r['mcc'], r['mnc'], oldname, newname))
            #
            r['codes_alpha_2'] = list(sorted(map(str.upper, r['codes_alpha_2'])))
            #
            if r['codes_alpha_2']:
                if len(r['codes_alpha_2']) == 1 and not country_present(r['country_name'], nameset):
                    newname = WIKIP_ISO3166[r['codes_alpha_2'][0]]['country_name']
                    logs.add('> MCC %s, all MNC, country name updated from %s to %s, CC2 %s'\
                          % (r['mcc'], r['country_name'], newname, r['codes_alpha_2'][0]))
                    r['country_name'] = newname
                for cc2 in r['codes_alpha_2']:
                    if cc2 not in WIKIP_ISO3166:
                        print('> MCC %s MNC %s, CC2 %s unknown' % (r['mcc'], r['mnc'], cc2))
            elif r['mcc'] not in MCC_INTL:
                print('> MCC %s MNC %s, no CC2 but not intl network' % (r['mcc'], r['mnc']))
    #
    aliases = []
    for mcc0 in sorted(WIKIP_MNC):
        for r in WIKIP_MNC[mcc0]:
            if (r['mcc'], r['mnc']) in MNC_ALIAS:
                # add an alias
                alias = dict(r)
                alias['mcc'], alias['mnc'] = MNC_ALIAS[(r['mcc'], r['mnc'])]
                aliases.append( alias )
                print('> added MNC alias %s.%s -> %s.%s'\
                      % (r['mcc'], r['mnc'], alias['mcc'], alias['mnc']))
    for alias in aliases:
        WIKIP_MNC[alias['mcc'][0:1]].append(alias)
    #
    for log in sorted(logs):
        print(log)

patch_wikip_mnc()


#------------------------------------------------------------------------------#
# Wikipedia MSISDN prefix dict
#------------------------------------------------------------------------------#

# custom CC2:
# AB, Abkhazia: no ref within telephone prefixes (same prefix as Georgia ?)
# AK, Akrotiri and Dhekelia: no ref within telephone prefixes (same prefix as Cyprus ? UK ? US ?)


def patch_wikip_msisdn():
    print('[+] patch Wikipedia list of country prefixes: WIKIP_MSISDN')
    #
    for pref, infos in sorted(WIKIP_MSISDN.items()):
        assert( pref.isdigit() )
        for (cc2, name, url) in infos:
            new, update = (cc2, name, url), False
            #
            # actually all missing CC2 are already added into ISO3166 dict
            # see patch_wikip_iso3166(), step 1bis)
            #if cc2 not in WIKIP_ISO3166:
            #    print('> MSISDN +%s, CC2 %s not in ISO3166 dict' % (pref, cc2))
            #
            if name != WIKIP_ISO3166[cc2]['country_name']:
                new, update = (new[0], WIKIP_ISO3166[cc2]['country_name'], new[2]), True
                print('> MSISDN +%s, country name changed from %s to %s'\
                      % (pref, name, new[1]))
            #
            if url != WIKIP_ISO3166[cc2]['country_url']:
                new, update = (new[0], new[1], WIKIP_ISO3166[cc2]['country_url']), True
            #
            if update:
                ind = infos.index( (cc2, name, url) )
                del infos[ind]
                infos.insert(ind, new)

patch_wikip_msisdn()


def patch_wikip_country():
    print('[+] patch Wikipedia list of country prefixes: WIKIP_COUNTRY')
    #
    isonameset = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    #
    for country, preflist in sorted(WIKIP_COUNTRY.items()):
        assert( all([pref.isdigit() for pref in preflist]) )
        #
        found = False
        #
        if country in COUNTRY_RENAME:
            newname = COUNTRY_RENAME[country]
            WIKIP_COUNTRY[newname] = preflist
            del WIKIP_COUNTRY[country]
            print('> country name changed from %s to %s' % (country, newname))
            found = True
        #
        elif country in isonameset:
            found = True
        #
        elif country in SUBTERR_TO_COUNTRY:
            #print('> country %s, prefix %s, sub-territory of %s'\
            #      % (country, ', '.join(['+%s' % pref for pref in preflist]), SUBTERR_TO_COUNTRY[country]))
            found = True
        #
        else:
            for r in sorted(WIKIP_ISO3166.values(), key=lambda r: r['country_name']):
                if country_present(country, r['nameset']):
                    newname = r['country_name']
                    WIKIP_COUNTRY[newname] = preflist
                    del WIKIP_COUNTRY[country]
                    print('> country name changed from %s to %s' % (country, newname))
                    found = True
                    break
        #
        if not found:
            print('> country name %s, prefix %s, not found in WIKIP_ISO3166'\
                  % (country, ', '.join(['+%s' % pref for pref in preflist])))
        #
        for pref in preflist:
            if pref not in WIKIP_MSISDN:
                found = True
                for i in range(len(pref)-1, 0, -1):
                    if pref[:i] in WIKIP_MSISDN:
                        if i == 1:
                            print('> country %s, prefix +%s not in WIKIP_MSISDN, corresponds to +%s'\
                                  % (country, pref, pref[:i]))
                        else:
                            print('> country %s, prefix +%s not in WIKIP_MSISDN, but +%s corresponds to %s'\
                                  % (country, pref, pref[:i],
                                     ', '.join(['%s (%s)' % (r[1], r[0]) for r in WIKIP_MSISDN[pref[:i]]])))
                        found = True
                if not found:
                    print('> country %s, prefix +%s not in WIKIP_MSISDN' % (country, pref))

patch_wikip_country()


#------------------------------------------------------------------------------#
# patch Egallic dataset on minimum distance between countries
#------------------------------------------------------------------------------#

def patch_egal_min_dist():
    print('[+] patch Egallic country distance dataset: CSV_EGAL_MIN_DIST')
    #
    isonameset    = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    #
    # 1) rename some countries
    for src, dst_dist in sorted(CSV_EGAL_MIN_DIST.items()):
        for dst in sorted(dst_dist):
            if dst in COUNTRY_RENAME:
                CSV_EGAL_MIN_DIST[src][COUNTRY_RENAME[dst]] = CSV_EGAL_MIN_DIST[src][dst]
                del CSV_EGAL_MIN_DIST[src][dst]
    #
    for src, dst_dist in sorted(CSV_EGAL_MIN_DIST.items()):
        if src in COUNTRY_RENAME:
            CSV_EGAL_MIN_DIST[COUNTRY_RENAME[src]] = CSV_EGAL_MIN_DIST[src]
            del CSV_EGAL_MIN_DIST[src]
            src = COUNTRY_RENAME[src]
    #
    # 2) do some verifications
    for src, dst_dist in sorted(CSV_EGAL_MIN_DIST.items()):
        for dst in dst_dist:
            if dst not in CSV_EGAL_MIN_DIST:
                print('> dst country %s in %s, not in src' % (dst, src))
        if not src in isonameset:
            if not src in SUBTERR_TO_COUNTRY:
                print('> country %s, not matching any territory name' % src)
            else:
                print('> country %s, matching only a sub-territory name' % src)

patch_egal_min_dist()


#------------------------------------------------------------------------------#
# patch and verify the World Factbook dataset
#------------------------------------------------------------------------------#

WFB_COUNTRY_DEL = [
    # duplicated entries
    'Virgin Islands (UK)',
    'Virgin Islands (US)',
    'Myanmar',
    # outdated entries
    'Netherlands Antilles',
    'France, Metropolitan',
    'Zaire',
    ]


_URL_Scattered_Islands = 'https://en.wikipedia.org/wiki/Scattered_Islands_in_the_Indian_Ocean' # France
_URL_US_Insular_area   = 'https://en.wikipedia.org/wiki/Territories_of_the_United_States#Incorporated_and_unincorporated_territories'

WFB_UNINHABITED = {
    'Juan de Nova Island'   : _URL_Scattered_Islands,
    'Baker Island'          : _URL_US_Insular_area,
    'Bassas da India'       : _URL_Scattered_Islands,
    'Coral Sea Islands'     : 'https://en.wikipedia.org/wiki/Coral_Sea_Islands', # Australia
    'Palmyra Atoll'         : _URL_US_Insular_area,
    'Paracel Islands'       : 'https://en.wikipedia.org/wiki/Paracel_Islands', # disputed China / Vietnam
    #'Wake Island'           : _URL_US_Insular_area,
    'Tromelin Island'       : _URL_Scattered_Islands,
    'Glorioso Islands'      : _URL_Scattered_Islands,
    'Ashmore and Cartier Islands': 'https://en.wikipedia.org/wiki/Ashmore_and_Cartier_Islands', # Australia
    'Navassa Island'        : _URL_US_Insular_area,
    'Midway Islands'        : _URL_US_Insular_area,
    'Western Samoa'         : 'https://en.wikipedia.org/wiki/Samoa',
    'Johnston Atoll'        : _URL_US_Insular_area,
    'Europa Island'         : _URL_Scattered_Islands,
    'Jarvis Island'         : _URL_US_Insular_area,
    'Spratly Islands'       : 'https://en.wikipedia.org/wiki/Spratly_Islands', # disputed  
    #   between China / Taiwan / Malaysia / Philippines / Vietnam
    'Howland Island'        : _URL_US_Insular_area,
    'Kingman Reef'          : _URL_US_Insular_area,
    }


def patch_wfb():
    print('[+] patch the World Factbook dataset: WORLD_FB')
    #
    isonameset    = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    #
    for name, infos in sorted(WORLD_FB.items()):
        for k in ('cc2', 'cc3', 'ccn', 'gec'):
            if infos[k] == '-':
                infos[k] = ''
        if name in WFB_COUNTRY_DEL:
            del WORLD_FB[name]
            print('> country %s deleted' % name)
    #
    for name, infos in sorted(WORLD_FB.items()):
        if name in COUNTRY_RENAME:
            newname = COUNTRY_RENAME[name]
            assert( newname not in WORLD_FB )
            WORLD_FB[newname] = infos
            del WORLD_FB[name]
            print('> country name changed from %s to %s' % (name, newname))
        # patch borders' names too
        try:
            bord = infos['infos']['boundaries']['bord']
        except Exception:
            pass
        else:
            for b, d in list(bord.items()):
                if b in COUNTRY_RENAME:
                    bord[COUNTRY_RENAME[b]] = d
                    del bord[b]
    #
    for name, infos in sorted(WORLD_FB.items()):
        if name not in isonameset:
            if name in SUBTERR_TO_COUNTRY:
                country = SUBTERR_TO_COUNTRY[name]
                if infos['cc2'] and infos['cc2'] != COUNTRY_SPEC[country]['cc2']:
                    print('> country %s, exists as sub-territory, CC2 mismatch %s / %s'\
                          % (name, infos['cc2'], COUNTRY_SPEC[country]['cc2']))
                else:
                    pass
                    #print('> country %s, exists as sub-territory of %s' % (name, country))
            else:
                # CC2 lookup
                if infos['cc2']:
                    if infos['cc2'] not in WIKIP_ISO3166:
                        print('> country %s, CC2 %s, not in WIKIP_ISO3166' % (name, infos['cc2']))
                    else:
                        newname = WIKIP_ISO3166[infos['cc2']]['country_name']
                        assert( newname not in WORLD_FB )
                        WORLD_FB[newname] = infos
                        del WORLD_FB[name]
                        print('> country name changed from %s to %s' % (name, newname))
                elif name not in WFB_UNINHABITED:
                    print('> country %s, no CC2, not referenced, unknown' % name)

patch_wfb()


#------------------------------------------------------------------------------#
# patch txtNation dataset
#------------------------------------------------------------------------------#

def _patch_country_name(name):
    #
    if name in COUNTRY_RENAME:
        newname = COUNTRY_RENAME[name]
        print('> country name changed from %s to %s' % (name, newname))
        return newname
    #
    nameset = country_name_canon(name)
    for cinf in WIKIP_ISO3166.values():
        for namesub in nameset:
            if country_match_set(namesub, cinf['nameset']):
                newname = cinf['country_name']
                print('> country name changed from %s to %s' % (name, newname))
                return newname
    #
    print('> country name %s not found' % name)
    return ''


def patch_txtn_mnc():
    print('[+] patch txtNation list of MCC-MNC: CSV_TXTN_MCCMNC')
    #
    isonameset = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    #
    for mccmnc, inf in sorted(CSV_TXTN_MCCMNC.items()):
        if not mccmnc.isdigit():
            print('> deleting entry for %s' % mccmnc)
            del CSV_TXTN_MCCMNC[mccmnc]
            continue
        #
        if isinstance(inf, list):
            infs = inf
            for inf in infs:
                if inf[0] not in isonameset:
                    newname = _patch_country_name(inf[0])
                    if newname:
                        i = infs.index(inf)
                        del infs[i]
                        infs.insert(i, (newname, inf[1]))
        else:
            if inf[0] not in isonameset:
                newname = _patch_country_name(inf[0])
                if newname:
                    CSV_TXTN_MCCMNC[mccmnc] = (newname, inf[1])

patch_txtn_mnc()


#------------------------------------------------------------------------------#
# patch ITU-T dataset
#------------------------------------------------------------------------------#

# warning:
# ITU-T uses "French Departments and Territories in the Indian Ocean" each time
# instead of Réunion and / or Mayotte
# So this needs to be handled explicitely when looking up for the country


def patch_itut_mnc(mncs):
    print('[+] patch ITU-T list of MCC-MNC: %r' % id(mncs))
    #
    isonameset  = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    mncset      = set()
    for mnos in WIKIP_MNC.values():
        for mno in mnos:
            mncset.add(mno['mcc'] + mno['mnc'])
    #
    for cntr, mnos in list(mncs.items()):
        if cntr not in isonameset:
            newname = _patch_country_name(cntr)
            if newname:
                del mncs[cntr]
                mncs[newname] = mnos

patch_itut_mnc(ITUT_MNC_1111)
patch_itut_mnc(ITUT_MNC_1162)


def patch_itut_spc(spclist):
    print('[+] patch ITU-T list of SPC: %r' % id(spclist))
    #
    isonameset  = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    for cntr, spcs in list(spclist.items()):
        if cntr not in isonameset:
            newname = _patch_country_name(cntr)
            if newname:
                del spclist[cntr]
                spclist[newname] = spcs

patch_itut_spc(ITUT_SPC_1199)

