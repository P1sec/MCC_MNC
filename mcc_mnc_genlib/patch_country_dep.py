#!/usr/bin/env python3
# -*- coding: UTF-8 -*-

# /**
# * Software Name : MCC_MNC
# * Version : 0.2
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
# * File Name : patch_country_dep.py
# * Created : 2021-04-08
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


# Countries / CC2 for which ambiguities exist and some names and / or infos 
# of the data set need to be updated
# There are also territories which correspond to multiple CC2, and not a single
# one

COUNTRY_SPEC = {
    #
    # Antigua and Barbuda
    'Antigua and Barbuda': {
        'cc2' : 'AG',
        'sub' : ['Antigua', 'Barbuda'],
        },
    #
    # Australia
    'Australia': {
        'cc2' : 'AU',
        'sub' : [ # automatically filled from WIKIP_ISO3166, see patch_dataset.py
            'Australian Antarctic Territory',  # should correspond to CC2 AC (Antarctic)
            'Australian External Territories', # group of multiple islands
            ],
        'sub_cc2'       : [], # automatically filled from WIKIP_ISO3166, see patch_dataset.py
        },
    #
    # Chile
    'Chile': {
        'cc2' : 'CL',
        'sub' : ['Easter Island'],
        },
    #
    # Eswatini / Swaziland
    'Eswatini': {
        'cc2' : 'SZ',
        'url' : 'https://en.wikipedia.org/wiki/Eswatini',
        },
    #
    # Finland
    'Åland Islands': {
        'cc2' : 'AX',
        'dep' : 'FI',
        },
    #
    # France
    'France': {
        'cc2' : 'FR',
        'sub' : [ # automatically filled from WIKIP_ISO3166, see patch_dataset.py
            'Clipperton Island', # no CC2
            'French Antilles',   # group of multiple CC2
            ],
        'sub_cc2'       : [], # automatically filled from WIKIP_ISO3166, see patch_dataset.py
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
    # group of French territories
    'French Antilles': {
        'url' : 'https://en.wikipedia.org/wiki/French_West_Indies',
        'sub' : ['Saint Barthélemy', 'French Guiana', 'Guadeloupe', 'Saint Martin', 'Martinique'],
        'sub_cc2'       : ['BL', 'GF', 'GP', 'MF', 'MQ'],
        },
    #
    'French Departments and Territories in the Indian Ocean': {
        'url' : 'https://en.wikipedia.org/wiki/List_of_French_islands_in_the_Indian_and_Pacific_oceans',
        'sub' : ['Réunion', 'Mayotte'],
        'sub_cc2'       : ['RE', 'YT'],
        },
    #
    # Georgia, Russia, Ukraine and other autonomous region around 
    'Georgia': {
        'cc2' : 'GE',
        'sub' : ['Abkhazia', 'South Ossetia'],
        'sub_cc2'       : ['AB'],
        },
    #
    'Abkhazia': {
        'cc2' : 'AB',
        'url' : 'https://en.wikipedia.org/wiki/Abkhazia',
        'state_name'    : 'Republic of Abkhazia',
        },
    #
    'Nagorno-Karabakh': {
        'cc2' : 'QN',
        'url' : 'https://en.wikipedia.org/wiki/Nagorno-Karabakh',
        'dep' : 'AZ', # Azerbaijan
        'sovereignity'  : 'disputed',
        'state_name'    : 'Artsakh',
        },
    #
    # Kosovo
    'Kosovo': {
        'cc2' : 'XK',
        'url' : 'https://en.wikipedia.org/wiki/Kosovo',
        #
        'cc_tld'        : '.xk',
        'cc_tld_url'    : 'https://en.wikipedia.org/wiki/.xk',
        'code_alpha_3'  : 'XKS',
        'sovereignity'  : 'disputed',
        'state_name'    : 'Republic of Kosovo',
        },
    #
    # Moldova
    'Moldova': {
        'cc2' : 'MD',
        'sub' : ['Transnistria'],
        },
    #
    # Morroco
    'Western Sahara': {
        'cc2' : 'EH',
        'dep' : 'MA',
        },
    #
    # Netherlands
    'Netherlands': {
        'cc2' : 'NL',
        'url' : 'https://en.wikipedia.org/wiki/Netherlands',
        'sub' : [], # automatically filled from WIKIP_ISO3166, see patch_dataset.py
        'sub_cc2'       : [], # automatically filled from WIKIP_ISO3166, see patch_dataset.py
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
    # New Zealand
    'New Zealand': {
        'cc2' : 'NZ',
        'sub' : [ # automatically filled from WIKIP_ISO3166, see patch_dataset.py
            'Chatham Island', # no CC2
            ],
        },
    #
    # Norway
    'Svalbard and Jan Mayen': {
        'cc2' : 'SJ',
        'url' : 'https://en.wikipedia.org/wiki/Svalbard_and_Jan_Mayen',
        'sub' : ['Svalbard', 'Jan Mayen'],
        'dep' : 'NO',
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
    # Tanzania
    'Tanzania' : {
        'cc2' : 'TZ',
        'sub' : ['Zanzibar']
        },
    #
    # Trinidad and Tobago
    'Trinidad and Tobago': {
        'cc2' : 'TT',
        'sub' : ['Trinidad', 'Tobago'],
        },
    #
    # Turkey
    'Turkey': {
        'cc2' : 'TR',
        'sub' : ['Northern Cyprus'],
        'sub_cc2': ['CT'],
        },
    #
    'Northern Cyprus': {
        'cc2' : 'CT',
        'url' : 'https://en.wikipedia.org/wiki/Northern_Cyprus',
        },
    #
    # United Kingdom
    'United Kingdom': {
        'cc2' : 'GB',
        'sub' : [ # automatically filled from WIKIP_ISO3166, see patch_dataset.py
            'Northern Ireland', # no CC2
            ],
        'sub_cc2'       : ['AK', ], # automatically filled from WIKIP_ISO3166, see patch_dataset.py
        },
    #
    'Akrotiri and Dhekelia': {
        'cc2' : 'AK',
        'sub' : ['Akrotiri', 'Dhekelia'],
        'bord': ['Cyprus'],
        'state_name'    : 'Akrotiri',
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
        'sub_cc2'       : ['AC', 'TA'],
        },
    #
    'Ascension': {
        'cc2' : 'AC',
        'url' : 'https://en.wikipedia.org/wiki/Ascension_Island',
        },
    #
    'Tristan da Cunha': {
        'cc2' : 'TA',
        'url' : 'https://en.wikipedia.org/wiki/Tristan_da_Cunha',
        },
    #
    'South Georgia and the South Sandwich Islands': {
        'cc2' : 'GS',
        'sub' : ['South Georgia', 'South Sandwich Islands'],
        },
    #
    # United States
    'United States': {
        'cc2' : 'US',
        'sub' : [ # automatically filled from WIKIP_ISO3166, see patch_dataset.py
            'Midway Island', 'Wake Island', # no CC2
            ],
        'sub_cc2'       : [], # automatically filled from WIKIP_ISO3166, see patch_dataset.py
        },
    #
    # Vatican
    'Vatican' : {
        'cc2' : 'VA',
        'url' : 'https://en.wikipedia.org/wiki/Holy_See',
        'dep' : 'IT',
        },
    }
