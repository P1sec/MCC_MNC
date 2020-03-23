#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import os
import re
import csv

from parse_wikipedia_tables import (
    REC_ISO3166,
    REC_MCC,
    REC_MNC,
    REC_BORDERS,
    )
from parse_worldfactbook_infos import (
    REC_COUNTRY,
    )

try:
    from wikip_borders      import WIKIP_BORDERS
    from wikip_iso3166      import WIKIP_ISO3166
    from wikip_mcc          import WIKIP_MCC
    from wikip_mnc          import WIKIP_MNC
    from wikip_msisdn       import WIKIP_MSISDN
    from wikip_country      import WIKIP_COUNTRY
    from wikip_territory    import WIKIP_TERRITORY
except ImportError:
    raise(Exception('error: please run first ./parse_wikipedia_tables.py'))
try:
    from world_fb           import WORLD_FB
except ImportError:
    raise(Exception('error: please run first ./parse_worldfactbook_infos.py'))


'''
This module is used as an "enhanced" loader for all Python dictionnaries generated
from raw data sources (Wikipedia, World Factbook, country_dist.csv).

It applies patches to some of the dictionnaries to solve specific conflicts and
political / geographical situations, align data values and ease further integration
'''


#------------------------------------------------------------------------------#
# functions to match country names
#------------------------------------------------------------------------------#

def country_name_canon(name):
    """returns a set of shorten / canonical names for the given country name `n'
    """
    name = name.lower()
    r = {name}
    if name.startswith('the'):
        name = name[3:].strip()
        r.add(name)
    if name.startswith('republic of'):
        r.add(name[11:].strip())
    m = re.search('\sand\s|,|\(', name)
    if m and m.start() > 10:
        r.add(name[:m.start()].strip())
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
            

#------------------------------------------------------------------------------#
# Wikipedia common changes
#------------------------------------------------------------------------------#

# Countries / CC2 for which ambiguities exist and some names and / or infos 
# of the data set need to be updated
COUNTRY_SPEC = {
    #
    # Antigua and Barbuda
    'Antigua and Barbuda': {
        'cc2' : 'AG',
        'sub' : ['Antigua', 'Barbuda'],
        },
    #
    # Eswatini / Swaziland
    'Eswatini': {
        'cc2' : 'SZ',
        'url' : 'https://en.wikipedia.org/wiki/Eswatini',
        },
    #
    # France
    'France': {
        'cc2'   : 'FR',
        'sub' : ['Saint Martin', 'French Guiana', 'French Polynesia', 'French Southern Territories',
            'Guadeloupe', 'Martinique', 'Mayotte', 'New Caledonia', 'Réunion', 'Saint Barthélemy',
            'Saint Pierre and Miquelon', 'Wallis and Futuna',
            'Clipperton Island', # no CC2 for it
            ],
        'sub_cc2': ['MF', 'GF', 'PF', 'TF', 'GP', 'MQ', 'YT', 'NC', 'RE', 'BL', 'PM', 'WF']
        },
    #
    'Saint Martin': {
        'cc2' : 'MF',
        'bord': ['Sint Maarten'],
        },
    #
    'French Guiana': {
        'cc2' : 'GF',
        'bord': ['Brazil', 'Suriname'],
        },
    #
    'French Southern Territories': {
        'cc2' : 'TF',
        'sub' : ['Kerguelen Islands', 'St. Paul Island', 'Amsterdam Island', 'Crozet Islands', 'Adélie Land', 'Scattered Islands'],
        },
    #
    # Netherlands
    'Netherlands': {
        'cc2' : 'NL',
        'url' : 'https://en.wikipedia.org/wiki/Netherlands',
        'sub' : ['Aruba', 'Bonaire, Saba and Sint Eustatius', 'Curaçao', 'Sint Maarten'],
        'sub_cc2': ['AW', 'BQ', 'CW', 'SX'],
        },
    #
    'Bonaire, Saba and Sint Eustatius': {
        'cc2' : 'BQ',
        'url' : 'https://en.wikipedia.org/wiki/Caribbean_Netherlands',
        'sub' : ['Bonaire', 'Saba', 'Sint Eustatius'],
        },
    #
    'Sint Maarten': {
        'cc2' : 'SX',
        'bord': ['Saint Martin'],
        },
    #
    # Saint Kitts and Nevis
    'Saint Kitts and Nevis': {
       'cc2' : 'KN',
       'sub' : ['Saint Kitts', 'Nevis'],
       },
    #
    # Saint Vincent
    'Saint Vincent and the Grenadines': {
        'cc2' : 'VC',
        'sub' : ['Saint Vincent', 'Grenadines'],
        },
    #
    # Spain
    'Spain': {
        'cc2' : 'ES',
        'sub' : ['Canary Islands', 'Balearic Islands']
        },
    #
    # Palestine
    'State of Palestine': {
        'cc2' : 'PS', 
        'url' : 'https://en.wikipedia.org/wiki/State_of_Palestine',
        'sub' : ['Gaza Strip', 'West Bank'],
        },
    #
    # Portugal
    'Portugal': {
        'cc2' : 'PT',
        'sub' : ['Madeira', 'Azores'],
        },
    #
    # United Kingdom
    'United Kingdom': {
        'cc2' : 'GB',
        'sub' : ['Akrotiri and Dhekelia', 'Anguilla', 'Bermuda', 'British Indian Ocean Territory', 'British Virgin Islands',
            'Cayman Islands', 'Falkland Islands', 'Gibraltar', 'Guernsey', 'Isle of Man', 'Jersey', 'Montserrat',
            'Pitcairn Islands', 'Saint Helena, Ascension and Tristan da Cunha', 'South Georgia and the South Sandwich Islands',
            'Turks and Caicos Islands'],
        'sub_cc2': ['AK', 'BM', 'IO', 'VG', 'KY', 'FK', 'GI', 'GG', 'IM', 'JE', 'MS', 'PN', 'SH', 'GS', 'TC'],
        },
    #
    'Akrotiri and Dhekelia': {
        'cc2' : 'AK',
        'sub' : ['Akrotiri', 'Dhekelia'],
        'bord': ['Cyprus'],
        },
    #
    'British Indian Ocean Territory': {
        'cc2': 'IO',
        'sub': ['Chagos Archipelago', 'Diego Garcia']
        },
    #
    'Gibraltar': {
        'cc2' : 'GI',
        'bord': ['Spain'],
        },
    #
    'Saint Helena, Ascension and Tristan da Cunha': {
        'cc2' : 'SH',
        'sub' : ['Saint Helena', 'Ascension', 'Tristan da Cunha'],
        },
    #
    'South Georgia and the South Sandwich Islands': {
        'cc2' : 'GS',
        'sub' : ['South Georgia', 'South Sandwich Islands'],
        },
    #
    # Trinidad and Tobago
    'Trinidad and Tobago': {
        'cc2' : 'TT',
        'sub' : ['Trinidad', 'Tobago'],
        },
    #
    # Vatican
    'Vatican' : {
        'cc2' : 'VA',
        'url' : 'https://en.wikipedia.org/wiki/Holy_See',
        },
    }


SUBTERR_TO_COUNTRY = {}
for name, infos in COUNTRY_SPEC.items(): 
    if 'sub' in infos:
        for subname in infos['sub']:
            SUBTERR_TO_COUNTRY[subname] = name


COUNTRY_RENAME = {
    'Bailiwick of Guernsey'     : 'Guernsey',
    'Caribbean Netherlands'     : 'Bonaire, Saba and Sint Eustatius',
    'Curacao'                   : 'Curaçao',
    'Cocos (Keeling) Islands'   : 'Cocos Islands',
    'Keeling Islands'           : 'Cocos Islands',
    'Palestine'                 : 'State of Palestine',
    'The Islamic Republic of Iran'  : 'Iran',
    'Iran (Islamic Republic of)'    : 'Iran',
    'The Kingdom of the Netherlands': 'Netherlands',
    'Collectivity of Saint Martin'  : 'Saint Martin',
    #'France, Metropolitan'      : 'France',
    'São Tomé and Príncipe'     : 'Sao Tome and Principe',
    'Somaliland'                : 'Somalia',
    'Swaziland'                 : 'Eswatini',
    #'Congo, Republic'           : 'Republic of the Congo',
    'Vatican City'              : 'Vatican',
    'Holy See'                  : 'Vatican',
    #'Holy See (Vatican City)'   : 'Vatican',
    'French Southern and Antarctic Lands'   : 'French Southern Territories',
    'Macedonia'                 : 'North Macedonia',
    'Micronesia'                : 'Federated States of Micronesia',
    #'Republic of Congo'         : 'Republic of the Congo',
    'Reunion'                   : 'Réunion',
    'Saint Barthelemy'          : 'Saint Barthélemy',
    'Timor-Leste'               : 'East Timor',
    'UK'                        : 'United Kingdom',
    'US'                        : 'United States',
    'USA'                       : 'United States',
    'Virgin Islands, British'   : 'British Virgin Islands',
    'Virgin Islands, US'        : 'United States Virgin Islands',
    #'Virgin Islands'            : 'United States Virgin Islands',
    'Madeira Islands'           : 'Madeira',
    #'Cote d\'Ivoire'            : 'Ivory Coast',
    #'Burma'                     : 'Myanmar',
    
    }


#------------------------------------------------------------------------------#
# Wikipedia ISO3166 dict
#------------------------------------------------------------------------------#

# code alpha 2 to be added to ISO3166 dict
CC2_TO_ADD = [
    {
    # Kosovo: not yet formally approved
    "cc_tld": ".xk",
    "cc_tld_url": "https://en.wikipedia.org/wiki/.xk", # does not exist (yet)
    "code_alpha_2": "XK", # not formally approved
    "code_alpha_3": "XKS",
    "country_name": "Kosovo",
    "country_url": "https://en.wikipedia.org/wiki/kosovo",
    "sovereignity": "disputed",
    "state_name": "Republic of Kosovo"
    },
    {
    # Abkhazia (autonomous part of Georgia): unoffical code
    "code_alpha_2": "AB", # unofficial
    "country_name": "Abkhazia",
    "country_url": "https://en.wikipedia.org/wiki/abkhazia",
    "sovereignity": "disputed",
    "state_name": "Republic of Abkhazia"
    },
    {
    # Akrotiri (military base in Cyprus): arbitrary code
    "code_alpha_2": "AK", # arbitrary assignment
    "country_name": "Akrotiri and Dhekelia",
    "country_url": "https://en.wikipedia.org/wiki/akrotiri_and_dhekelia",
    "state_name": "Akrotiri"
    },
    ]


# code alpha 2 to be added, which is an alias for another code
CC2_ALIAS = {
    'UK' : 'GB',
    }


def patch_wikip_iso3166():
    print('[+] patch Wikipedia ISO3166 dict: WIKIP_ISO3166')
    #
    # 1) add entries
    for new in CC2_TO_ADD:
        r = dict(REC_ISO3166)
        r.update(new)
        if r['code_alpha_2'] in WIKIP_ISO3166:
            print('> CC2 %s already exists, %s not added' % (r['code_alpha_2'], r['country_name']))
        else:
            WIKIP_ISO3166[r['code_alpha_2']] = r
            print('> CC2 %s, %s added' % (r['code_alpha_2'], r['country_name']))
    for new, old in CC2_ALIAS.items():
        if new not in WIKIP_ISO3166:
            WIKIP_ISO3166[new] = WIKIP_ISO3166[old]
            print('> CC2 %s, alias to %s' % (new, old))
    #
    # 1bis) add more entries, extracted from the international telephone numbering listing
    for pref, infos in WIKIP_MSISDN.items():
        for cc2, name, url in infos:
            if cc2 not in WIKIP_ISO3166:
                r = dict(REC_ISO3166)
                r['code_alpha_2']  = cc2
                r['country_name']  = name
                r['country_url']   = url
                WIKIP_ISO3166[cc2] = r
                print('> CC2 %s, %s added from WIKIP_MSISDN' % (cc2, name))
    #
    # 2) patch country names
    for cc2, infos in WIKIP_ISO3166.items():
        for oldname, newname in COUNTRY_RENAME.items():
            if country_match(infos['country_name'], oldname): 
                infos['country_name'] = newname
                if newname in COUNTRY_SPEC:
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
    # are referenced correctly
    for country in COUNTRY_SPEC:
        cc2 = COUNTRY_SPEC[country]['cc2']
        if cc2 not in WIKIP_ISO3166:
            print('> missing CC2 %s, %s' % (cc2, country))
        else:
            if country != WIKIP_ISO3166[cc2]['country_name']:
                print('> CC2 %s, country name changed from %s to %s' % (cc2, WIKIP_ISO3166[cc2]['country_name'], country))
                WIKIP_ISO3166[cc2]['country_name'] = country
                if 'url' in COUNTRY_SPEC[country]:
                    WIKIP_ISO3166[cc2]['country_url'] = COUNTRY_SPEC[country]['url']
            if 'sub_cc2' in COUNTRY_SPEC[country]:
                for cc2_s in COUNTRY_SPEC[country]['sub_cc2']:
                    if cc2_s not in WIKIP_ISO3166:
                        print('> missing CC2 %s, part of %s' % (cc2_s, country))
    #
    # 6) keep track of country name variants
    for cc2, infos in WIKIP_ISO3166.items():
        infos['nameset'] = country_name_canon(infos['country_name'])
        infos['nameset'].update( country_name_canon(infos['state_name']) )

patch_wikip_iso3166()


#------------------------------------------------------------------------------#
# Wikipedia territory borders list
#------------------------------------------------------------------------------#

# territory name that needs to be deleted
BORD_COUNTRY_DEL = [
    #
    # South Ossetia:
    # within Georgia, borders with Georgia and Russia,
    # no ref in other sources, no specific CC2
    # => delete entry, and neighbours entry within Georgia and Russia
    'South Ossetia',
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
    'Netherlands',
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
        for oldname, newname in COUNTRY_RENAME.items():
            if country_match(r['country_name'], oldname): 
                r['country_name'] = newname
                if newname in COUNTRY_SPEC and 'url' in COUNTRY_SPEC[newname]:
                    r['country_url'] = COUNTRY_SPEC[newname]['url']
                print('> country name changed from %s to %s' % (oldname, newname))
        for n in r['neigh'][:]:
            for oldname, newname in COUNTRY_RENAME.items():
                if country_match(n[0], oldname): 
                    if newname in COUNTRY_SPEC and 'url' in COUNTRY_SPEC[newname]:
                        new_n = (newname, COUNTRY_SPEC[newname]['url'])
                    else:
                        new_n = (newname, n[1])
                    r['neigh'].remove(n)
                    r['neigh'].append( new_n )
                    r['neigh'].sort(key=lambda t: t[0])
                    print('> country %s, border changed from %s to %s'\
                          % (r['country_name'], oldname, newname))
        for s in r['country_sub'][:]:
            if country_match(s[0], r['country_name']):
                # simply remove territory
                r['country_sub'].remove(s)
            for oldname, newname in COUNTRY_RENAME.items():
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
    # convert WIKIP_BORDERS into a dict
    BD = {r['country_name']: r for r in WIKIP_BORDERS}
    assert( len(BD) == len(WIKIP_BORDERS) )
    for name in ('France', 'Netherlands', 'United Kingdom'):
        neighs = [name for (name, url) in BD[name]['neigh']]
        for r in WIKIP_BORDERS:
            for r_neigh in r['neigh'][:]:
                if country_match(r_neigh[0], name) \
                and not country_present(r['country_name'], neighs):
                    # delete entry
                    r['neigh'].remove(r_neigh)
                    print('> country %s, neighbour %s removed' % (r['country_name'], r_neigh[0]))
    #
    # 5) ensure all country / borders are in the ISO3166 dict
    isonames = set()
    [isonames.update(country_name_canon(r['country_name'])) for r in WIKIP_ISO3166.values()]
    for r in WIKIP_BORDERS:
        if not any([name in isonames for name in country_name_canon(r['country_name'])]):
            if country_present(r['country_name'], SUBTERR_TO_COUNTRY):
                # warning: SUBTERR_TO_COUNTRY lookup could fail here
                print('> country %s, not present in ISO3166 dict but referenced as sub of %s'\
                      % (r['country_name'], SUBTERR_TO_COUNTRY[r['country_name']]))
            else:
                print('> country %s, not present in ISO3166 dict' % r['country_name'])
        for n in r['neigh']:
            if not any([name in isonames for name in country_name_canon(n[0])]):
                if country_present(n[0], SUBTERR_TO_COUNTRY):
                    # warning: SUBTERR_TO_COUNTRY lookup could fail here
                    print('> country %s, border %s in not present in ISO3166 dict but referenced as sub of %s'\
                          % (r['country_name'], n[0], SUBTERR_TO_COUNTRY[n[0]]))
                else:
                    print('> country %s, border %s in not present in ISO3166 dict'\
                          % (r['country_name'], n[0]))

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


def patch_wikip_mcc():
    print('[+] patch Wikipedia list of MCC: WIKIP_MCC')
    # patch country names and crappy CC2
    # ensure CC codes are upper case
    # and CC2 is in WIKIP_ISO3166 otherwise intl mcc
    for r in WIKIP_MCC:
        for oldname, newname in COUNTRY_RENAME.items():
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
    for mcc0 in WIKIP_MNC:
        for r in WIKIP_MNC[mcc0]:
            for oldname, newname in COUNTRY_RENAME.items():
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
    for log in sorted(logs):
        print(log)

patch_wikip_mnc()


#------------------------------------------------------------------------------#
# Wikipedia MSISDN prefix dict
#------------------------------------------------------------------------------#

# it maybe needed to add CC2 for specific country prefix
# AB, check with Georgia
# KX, check with countries around Serbia
# AK, check with Cyprus and UK

def verif_wikip_msisdn():
    print('[+] verify Wikipedia list of country prefix: WIKIP_MSISDN')
    # verify all CC2 exist
    for pref, infos in WIKIP_MSISDN.items():
        assert( pref.isdigit() )
        for cc2, name, url in infos:
            if cc2 not in WIKIP_ISO3166:
                print('> MSISDN +%s, CC2 %s not in ISO3166 dict' % (pref, cc2))

# actually all missing CC2 are already added into ISO3166 dict
# see patch_wikip_iso3166(), step 1bis)
#verif_wikip_msisdn()


#------------------------------------------------------------------------------#
# get minimum distance between countries and verify the dataset
#------------------------------------------------------------------------------#

# addingthe dataset with minimum distance between countries, from here
URL_MIN_DIST = 'https://gist.githubusercontent.com/mtriff/185e15be85b44547ed110e412a1771bf/'\
               'raw/1bb4d287f79ca07f63d4c56110099c26e7c6ee7d/countries_distances.csv'
# which is an updated version of the dataset computed here:
# http://egallic.fr/en/closest-distance-between-countries/


# some country name must be attached to there proper country name
# required to match those from Wikipedia

def get_egal_min_dist():
    print('[+] read Egallic country_dist.csv to EGAL_MIN_DIST')
    #
    if not os.path.exists('./country_dist.csv'):
        resp = urllib.request.urlopen(URL_MIN_DIST)
        if resp.code != 200:
            raise(Exception('resource %s not available, HTTP code %i' % (url, resp.code)))
        with open('country_dist.csv', 'w') as fd:
            fd.write(resp.read())
    #
    with open('country_dist.csv', encoding='utf-8') as fd:
        csv_lines = fd.readlines()
        if 'pays1' in csv_lines[0]:
            # remove header
            del csv_lines[0]
        while not csv_lines[-1].strip():
            # remove blank lines
            del csv_lines[-1]
        D = {}
        for n, src, dst, dist in csv.reader(csv_lines, delimiter=','):
            src, dst, dist = map(lambda t: t.replace('"', '').strip(), (src, dst, dist))
            if src in COUNTRY_RENAME:
                src = COUNTRY_RENAME[src]
            if dst in COUNTRY_RENAME:
                dst = COUNTRY_RENAME[dst]
            if src not in D:
                D[src] = {}
            elif dst in D[src]:
                print('> duplicate entry for %s in %s' % (dst, src))
            D[src][dst] = float(dist)
        return D

EGAL_MIN_DIST = get_egal_min_dist()


def verif_egal_min_dist():
    print('[+] patch egallic country distance dataset: EGAL_MIN_DIST')
    #
    nameset    = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    #namesetext = set()
    #[namesetext.update(country_name_canon(name)) for name in nameset]
    #[namesetext.update(country_name_canon(name)) for name in [r['state_name'] for r in WIKIP_ISO3166.values()]]
    #
    for src, dst_dist in EGAL_MIN_DIST.items():
        for dst in dst_dist:
            if dst not in EGAL_MIN_DIST:
                print('> dst country %s in %s, not in src' % (dst, src))
        if not country_present(src, nameset):
            if country_present(src, SUBTERR_TO_COUNTRY):
                print('> country %s, matching a sub-territory from %s' % (src, SUBTERR_TO_COUNTRY[src]))
            else:
                print('> country %s, not matching any country name from ISO3166 dict' % src)

verif_egal_min_dist()


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


def patch_wfb():
    print('[+] patch the World Factbook dataset: WORLD_FB')
    #
    isonameset    = set([r['country_name'] for r in WIKIP_ISO3166.values()])
    #
    for name, infos in list(WORLD_FB.items()):
        for k in ('cc2', 'cc3', 'ccn', 'gec'):
            if infos[k] == '-':
                infos[k] = ''
        if name in WFB_COUNTRY_DEL:
            del WORLD_FB[name]
            print('> country %s deleted' % name)
        if name in COUNTRY_RENAME:
            newname = COUNTRY_RENAME[name]
            assert( newname not in WORLD_FB )
            WORLD_FB[newname] = infos
            del WORLD_FB[name]
            print('> country name changed from %s to %s' % (name, newname))
    #
    for name, infos in list(WORLD_FB.items()):
        if name not in isonameset:
            if name in SUBTERR_TO_COUNTRY:
                country = SUBTERR_TO_COUNTRY[name]
                if infos['cc2'] and infos['cc2'] != COUNTRY_SPEC[country]['cc2']:
                    print('> country %s, exists as sub-territory, CC2 mismatch %s / %s'\
                          % (name, infos['cc2'], COUNTRY_SPEC[country]['cc2']))
                else:
                    print('> country %s, exists as sub-territory of %s' % (name, country))
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
                else:
                    print('> country %s, no CC2, not referenced' % name)


patch_wfb()

'''TODO:
> country Juan de Nova Island, no CC2, not referenced
> country Baker Island, no CC2, not referenced
> country Bassas da India, no CC2, not referenced
> country Coral Sea Islands, no CC2, not referenced
> country Palmyra Atoll, no CC2, not referenced
> country Paracel Islands, no CC2, not referenced
> country Wake Island, no CC2, not referenced
> country Tromelin Island, no CC2, not referenced
> country Jan Mayen, no CC2, not referenced
> country Glorioso Islands, no CC2, not referenced
> country Ashmore and Cartier Islands, no CC2, not referenced
> country Navassa Island, no CC2, not referenced
> country Midway Islands, no CC2, not referenced
> country Western Samoa, no CC2, not referenced
> country Johnston Atoll, no CC2, not referenced
> country Europa Island, no CC2, not referenced
> country Jarvis Island, no CC2, not referenced
> country Spratly Islands, no CC2, not referenced
> country Howland Island, no CC2, not referenced
> country Kingman Reef, no CC2, not referenced
'''
