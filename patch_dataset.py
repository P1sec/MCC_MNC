#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

import re

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
    from wikip_borders  import WIKIP_BORDERS
    from wikip_iso3166  import WIKIP_ISO3166
    from wikip_mcc      import WIKIP_MCC
    from wikip_mnc      import WIKIP_MNC
    from wikip_msisdn   import WIKIP_MSISDN
except ImportError:
    raise(Exception('error: please run first ./parse_wikipedia_tables.py'))
try:
    from world_fb       import WORLD_FB
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

# territory name that needs to be changed
COUNTRY_NAME_CHANGE = {
    #    
    # Caribbean Netherlands main island name is Bonaire, for which there is a CC2 
    'Caribbean Netherlands':
        ('Bonaire', 'https://en.wikipedia.org/wiki/bonaire'),
    #
    # Gaza Strip is part of Palestine, only appears as a neighbour
    'Gaza Strip':
        ('State of Palestine', 'https://en.wikipedia.org/wiki/state_of_palestine'),
    #
    # São Tomé and Príncipe, removing accent
    'São Tomé and Príncipe':
        ('Sao Tome and Principe', 'https://en.wikipedia.org/wiki/sao_tome_and_principe'),
    #
    # Somaliland, self-declared state within Somali, only appears as a neighbour territory in WIKIP_BORDERS
    'Somaliland':
        ('Somalia', 'https://en.wikipedia.org/wiki/somalia'),
    #
    # Swaziland, renamed to Eswatini in 2018
    # warning: kept as Swaziland in wfb and country_dist
    'Swaziland':
        ('Eswatini', 'https://en.wikipedia.org/wiki/eswatini'),
    #
    # Iran / Islamic Republic of
    'The Islamic Republic of Iran':
        ('Iran', 'https://en.wikipedia.org/wiki/iran'),
    'Iran (Islamic Republic of)':
        ('Iran', 'https://en.wikipedia.org/wiki/iran'),
    #
    # Netherlands / The Kingdom of the Netherlands
    'The Kingdom of the Netherlands':
        ('Netherlands', 'https://en.wikipedia.org/wiki/netherlands'),
    #
    # Vatican official country name is Holy See, from which Vatican City is the capital
    # warning: kept as Vatican in country_dist
    'Vatican City':
        ('Holy See', 'https://en.wikipedia.org/wiki/holy_see'),
    #
    # West Bank is the name of the main part of Palestine
    'West Bank':
        ('State of Palestine', 'https://en.wikipedia.org/wiki/state_of_palestine'),
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
    }
    ]


# France overseas territories with independent CC2:
#   and corresponding names and borders
CC2_FR = {
    'MF': ('Saint Martin', [
        ('Sint Maarten', 'https://en.wikipedia.org/wiki/sint_maarten'),
        ]), # next to Anguilla, Saint Barthelemy
    'GF': ('French Guiana', [
        ('Brazil', 'https://en.wikipedia.org/wiki/Brazil'),
        ('Suriname', 'https://en.wikipedia.org/wiki/Suriname'),
        ]),
    'PF': ('French Polynesia', []),
    'TF': ('French Southern and Antarctic Lands', []),
    'GP': ('Guadeloupe', []), # next to Dominica, Montserrat, Antigua and Barbuda
    'MQ': ('Martinique', []), # next to Dominica, Saint Lucia
    'YT': ('Mayotte', []), # next to Comoros
    'NC': ('New Caledonia', []),
    'RE': ('Reunion', []),
    'BL': ('Saint Barthelemy', []), # next to Saint Martin, Sint Maarten, Anguilla
    'PM': ('Saint Pierre and Miquelon', []), # next to Canada
    'WF': ('Wallis and Futuna', [])
    }


# Kingdom of the Netherlands overseas territories with independent CC2:
#   and corresponding names and borders
CC2_NL = {
    'AW': ('Aruba', []),   # next to Venezuela
    'BQ': ('Bonaire', []), # next to Venezuela, also called Caribbean Netherlands
    'CW': ('Curaçao', []), # next to Venezuela
    'SX': ('Sint Maarten', [
        ('Saint Martin', 'https://en.wikipedia.org/wiki/collectivity_of_saint_martin'),
        ]) # next to Anguilla, Saint Barthelemy
    }


# United Kingdom overseas territories with independent CC2
#   and corresponding names and borders
CC2_UK = {
    'AK': ('Akrotiri and Dhekelia', [
        ('Cyprus', 'https://en.wikipedia.org/wiki/cyprus'),
        ]), # arbitrary CC2 assignment
    'AI': ('Anguilla', []), # next to Saint Martin, Sint Maarten, Saint Barthelemy
    'BM': ('Bermuda', []),
    'IO': ('British Indian Ocean Territory', []),
    'VG': ('British Virgin Islands', []), # next to Virgin Islands (VI)
    'KY': ('Cayman Islands', []),
    'FK': ('Falkland Islands', []),
    'GI': ('Gibraltar', [
        ('Spain', 'https://en.wikipedia.org/wiki/spain')
        ]), # next to Morroco
    'GG': ('Guernsey', []), # next to Jersey, France
    'IM': ('Isle of Man', []), # next to United Kingdom, Republic of Ireland
    'JE': ('Jersey', []), # next to Guernsey, France
    'MS': ('Montserrat', []), # next to Guadeloupe, Saint Kitts and Nevis, Antigua and Barbuda
    'PN': ('Pitcairn Islands', []),
    'SH': ('Saint Helena', []), # also called Saint Helena, Ascension and Tristan da Cunha
    'GS': ('South Georgia and the South Sandwich Islands', []), # also called South Georgia and the Islands in WFB
    'TC': ('Turks and Caicos Islands', []), # next to Bahamas
    }


def patch_wikip_iso3166():
    print('[+] patch Wikipedia ISO3166 dict')
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
    #
    # 2) patch country names
    for cc2, infos in WIKIP_ISO3166.items():
        for oldname, (newname, newurl) in COUNTRY_NAME_CHANGE.items():
            if country_match(infos['country_name'], oldname): 
                infos['country_name'], infos['country_url'] = newname, newurl
                print('> CC2 %s, country name changed to %s' % (cc2, newname))
    #
    # 3) ensure all url and tld are lower case, and CC codes are upper case
    for infos in WIKIP_ISO3166.values():
        infos['country_url']  = infos['country_url'].lower()
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
    # 5) ensure all oversea territories from FR, NL and UK are there
    for cc2_os in (CC2_FR, CC2_NL, CC2_UK):
        for cc2 in cc2_os:
            if cc2 not in WIKIP_ISO3166:
                print('> missing CC2 %s' % cc2)

patch_wikip_iso3166()


#------------------------------------------------------------------------------#
# Wikipedia territory borders list
#------------------------------------------------------------------------------#

# territory name that needs to be deleted
BORD_COUNTRY_DEL = [
    #
    # Madeira:
    # part of Portugal, no borders,
    # no ref in other sources, no specific CC2
    # => delete entry
    'Madeira',
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
    print('[+] patch Wikipedia territory borders list')
    #
    # 1) patch names
    for r in WIKIP_BORDERS:
        for oldname, (newname, newurl) in COUNTRY_NAME_CHANGE.items():
            if country_match(r['country_name'], oldname):
                r['country_name'], r['country_url'] = newname, newurl
                print('> country name changed to %s' % newname)
        for n in r['neigh'][:]:
            for oldname, (newname, newurl) in COUNTRY_NAME_CHANGE.items():
                if country_match(n[0], oldname): 
                    r['neigh'].remove(n)
                    r['neigh'].append( (newname, newurl) )
                    r['neigh'].sort(key=lambda t: t[0])
                    print('> country %s, border changed to %s'\
                          % (r['country_name'], newname))
    #
    # 2) delete entries
    for r in WIKIP_BORDERS[:]:
        if r['country_name'] in BORD_COUNTRY_DEL:
            WIKIP_BORDERS.remove(r)
            print('> country %s deleted' % r['country_name'])
        elif r['country_name'] in BORD_DUP_DEL and r['country_sub']:
            WIKIP_BORDERS.remove(r)
            print('> duplicated country %s deleted' % r['country_name'])
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
                    print('> removed neighbour %s from %s' % (r_neigh[0], r['country_name']))
    #
    # 5) ensure all country / borders are in the ISO3166 dict
    isonames = set()
    [isonames.update(country_name_canon(r['country_name'])) for r in WIKIP_ISO3166.values()]
    for r in WIKIP_BORDERS:
        if not any([name in isonames for name in country_name_canon(r['country_name'])]):
            print('> country %s not present in ISO3166 dict' % r['country_name'])
        for n in r['neigh']:
            if not any([name in isonames for name in country_name_canon(n[0])]):
                print('> border %s in country %s not present in ISO3166 dict'\
                      % (n[0], r['country_name']))

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
    'GE-AB': 'AB',
    }


def patch_wikip_mcc():
    print('[+] patch Wikipedia list of MCC')
    # patch country names and crappy CC2
    # ensure country_url is lower case, and CC codes are upper case
    # and CC2 is in WIKIP_ISO3166 otherwise intl mcc
    for r in WIKIP_MCC:
        for oldname, (newname, newurl) in COUNTRY_NAME_CHANGE.items():
            if country_match(r['country_name'], oldname): 
                r['country_name'], r['country_url'] = newname, newurl
                print('> MCC %s, country name changed to %s' % (r['mcc'], newname))
        if r['code_alpha_2'] in MCC_CC2_LUT:
            r['code_alpha_2'] = MCC_CC2_LUT[r['code_alpha_2']]
        #
        r['country_url']  = r['country_url'].lower()
        r['code_alpha_2'] = r['code_alpha_2'].upper()
        if r['code_alpha_2']:
            assert( r['code_alpha_2'] in WIKIP_ISO3166 )
        else:
            assert( r['mcc'] in MCC_INTL )

patch_wikip_mcc()


def patch_wikip_mnc():
    print('[+] patch Wikipedia list of MCC-MNC')
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
            for oldname, (newname, newurl) in COUNTRY_NAME_CHANGE.items():
                if country_match(r['country_name'], oldname):
                    r['country_name'] = newname
                    print('> MCC %s MNC %s, country name changed to %s' % (r['mcc'], r['mnc'], newname))
            r['codes_alpha_2'] = list(sorted(map(str.upper, r['codes_alpha_2'])))
            #
            if r['codes_alpha_2']:
                if len(r['codes_alpha_2']) == 1 and not country_present(r['country_name'], nameset):
                    r['country_name'] = WIKIP_ISO3166[r['codes_alpha_2'][0]]['country_name']
                    logs.add('> MCC %s, all MNC, country name updated to %s, CC2 %s'\
                          % (r['mcc'], r['country_name'], r['codes_alpha_2'][0]))
                for cc2 in r['codes_alpha_2']:
                    if cc2 not in WIKIP_ISO3166:
                        print('> MCC %s MNC %s, CC2 %s unknown' % (r['mcc'], r['mnc'], cc2))
            elif r['mcc'] not in MCC_INTL:
                print('> MCC %s MNC %s, no CC2 but not intl network' % (r['mcc'], r['mnc']))
    #
    for log in sorted(logs):
        print(log)

patch_wikip_mnc()

