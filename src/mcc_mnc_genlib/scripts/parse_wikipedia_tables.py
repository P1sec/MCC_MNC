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
# * File Name : parse_wikipedia_tables.py
# * Created : 2020-09-14
# * Authors : Benoit Michau
# *--------------------------------------------------------
# */


import argparse
import json
import re
import sys
import urllib.request
from os.path import dirname, join, realpath
from pprint import PrettyPrinter

from lxml import etree

SCRIPT_DIR = dirname(realpath(__file__))
MODULE_DIR = dirname(realpath(SCRIPT_DIR))

PATH_PRE = join(MODULE_DIR, 'raw', '')

HTTP_USER_AGENT = (
    'Mozilla/5.0 (X11; Linux x86_64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/126.0.0.0 Safari/537.36'
)

RE_WIKI_REF = re.compile(r'.*(\[.*\]){1,}$')


def _strip_wiki_ref(s):
    m = RE_WIKI_REF.match(s)
    if m:
        return s[: s.find('[')].strip()
    else:
        return s.strip()


RE_WIKI_REFNOTE = re.compile(r'\[[ a-zA-Z0-9]*\]')


def _strip_wiki_refnote(s):
    m = RE_WIKI_REFNOTE.match(s)
    if m:
        return s[m.end() :].strip()
    else:
        return s.strip()


# ------------------------------------------------------------------------------#
# parsing Wikipedia ISO-3166 codes
# ------------------------------------------------------------------------------#

URL_PREF = 'https://en.wikipedia.org'
URL_CODE_ALPHA_2 = (
    'https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes'
)


REC_ISO3166 = {
    'country_name': '',  # str, ISO 3166 country name
    'country_url': '',  # url to the Wikipedia page of the country
    'state_name': '',  # str
    'sovereignity': '',  # str: UN member, UN observer, antarctic, disputed or another country_name
    'code_alpha_2': '',  # 2-char
    'code_alpha_3': '',  # 3-char
    'code_num': '',  # 3-digit
    #'regions'               : {}, # dict of region code, region name
    'regions_url': '',  # url to the Wikipedia page of the regional code
    'cc_tld': '',  # str
    'cc_tld_url': '',  # url to the Wikipedia page of the ccTLD
}


RE_TEXT_INVAL = re.compile(r'[!\:\{\}]')
is_text_valid = lambda t: (
    True if t.strip() and not RE_TEXT_INVAL.search(t) else False
)


SOVEREIGNITY_LUT = {
    'finland': 'FI',
    'united states': 'US',
    'united kingdom': 'GB',
    'netherlands': 'NL',
    'norway': 'NO',
    'australia': 'AU',
    'new zealand': 'NZ',
    'denmark': 'DK',
    'france': 'FR',
    'british crown': 'GB',  # this is not exactly true, however...
    'china': 'CN',
    'un member': 'UN member',
    'un observer': 'UN observer',
    'antarctic treaty': 'Antarctica',
    'disputed': 'disputed',
}


CRAPPY_NAMES = {
    'Georgia (country)',
    'List of islands of the Netherlands Antilles',
    'List of French islands in the Indian and Pacific oceans',
}


def import_html_doc(url):
    req = urllib.request.Request(url, headers={'User-Agent': HTTP_USER_AGENT})
    resp = urllib.request.urlopen(req)
    if resp.code == 200:
        R = etree.parse(resp, etree.HTMLParser()).getroot()
    else:
        raise (
            Exception(
                'resource %s not available, HTTP code %i' % (url, resp.code)
            )
        )
    #
    # return R.xpath('//table')
    return R


def explore_text(E):
    # print(E)
    if hasattr(E, 'text') and E.text is not None and is_text_valid(E.text):
        return E
    for e in E:
        t = explore_text(e)
        if (
            t is not None
            and hasattr(t, 'text')
            and t.text is not None
            and is_text_valid(t.text)
        ):
            return t


def _normalize_wiki_url(url):
    if not url:
        return ''
    url = url.strip()
    if url.startswith('https://') or url.startswith('http://'):
        return url
    if url.startswith('/wiki/'):
        return URL_PREF + url
    if url.startswith('./'):
        return URL_PREF + '/' + url[2:]
    if url.startswith('/'):
        return URL_PREF + url
    return URL_PREF + '/' + url


def _get_first_href(e):
    if e is None:
        return ''
    if hasattr(e, 'attrib') and 'href' in e.attrib:
        return _normalize_wiki_url(e.attrib['href'])
    for a in e.xpath('.//a[@href]'):
        return _normalize_wiki_url(a.attrib['href'])
    return ''


def _get_country_url(e):
    if e is None:
        return None, None
    a = e if e.tag == 'a' and 'href' in e.attrib else None
    if a is None:
        for cand in e.xpath('.//a[@href]'):
            a = cand
            break
    if a is not None:
        url = _normalize_wiki_url(a.attrib.get('href', ''))
        name = a.attrib.get('title', '').strip()
        if not name:
            name = ''.join(a.itertext()).strip()
        if name in CRAPPY_NAMES and a.text:
            name = a.text.strip()
        return name or None, url or None
    txt = ''.join(e.itertext()).strip()
    if txt:
        return txt, ''
    return None, None


def read_entry_iso3166(T, off):
    L = T[off]
    rec = dict(REC_ISO3166)
    rec['country_name'], rec['country_url'] = _get_country_url(L[0])
    # Current layout: [country, sovereignty, alpha2, alpha3, num, regions, ccTLD]
    rec['state_name'] = ''
    rec['sovereignity'] = SOVEREIGNITY_LUT[
        explore_text(L[1]).text.strip().lower()
    ]
    rec['code_alpha_2'] = explore_text(L[2]).text.strip().upper()
    rec['code_alpha_3'] = explore_text(L[3]).text.strip().upper()
    rec['code_num'] = explore_text(L[4]).text.strip()
    # rec['regions']      =
    rec['regions_url'] = _get_first_href(L[5])
    rec['cc_tld'] = explore_text(L[6]).text.strip().lower()
    rec['cc_tld_url'] = _get_first_href(L[6])
    if rec['cc_tld'] and rec['cc_tld'][0] != '.':
        rec['cc_tld'] = ''
        rec['cc_tld_url'] = ''
    return rec


def parse_table_iso3166():
    T = import_html_doc(URL_CODE_ALPHA_2).xpath('//table')
    T_CC = T[0][0]
    D = {}
    for i in range(2, len(T_CC)):
        try:
            rec = read_entry_iso3166(T_CC, i)
        except IndexError:
            # print('no entry at rank %i, after %s' % (i, rec['country_name']))
            pass
        else:
            if rec['code_alpha_2'] in D:
                raise (
                    Exception('duplicate entries for {}'.format(rec['code_alpha_2']))
                )
            else:
                D[rec['code_alpha_2']] = rec
    print('[+] parsed %i ISO-3166 country codes' % len(D))
    return D


# ------------------------------------------------------------------------------#
# parsing Wikipedia MCC and MNC
# ------------------------------------------------------------------------------#

# MCC and international operators
URL_MCC = 'https://en.wikipedia.org/wiki/Mobile_country_code'
# national operators
URL_MNC_EU = 'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_2xx_(Europe)'
URL_MNC_NA = 'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_3xx_(North_America)'
URL_MNC_AS = 'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_4xx_(Asia)'
URL_MNC_OC = 'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_5xx_(Oceania)'
URL_MNC_AF = 'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_6xx_(Africa)'
URL_MNC_SA = 'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_7xx_(South_America)'


REC_MCC = {
    'mcc': '',  # 3-digit str
    'country_name': '',  # str
    'country_url': '',  # str
    'code_alpha_2': '',  # 2-char
    'mcc_url': '',  # str
    'authority': '',  # str
    'notes': '',  # str
}


REC_MNC = {
    'country_name': '',  # str
    'country_url': '',  # str
    'country_sub': None,  # 2-tuple of str (country_name, country_url)
    'codes_alpha_2': [],  # list of 2-char
    'mcc': '',  # 3-digit str
    'mnc': '',  # 2 or 3-digit str
    'brand': '',  # str
    'operator': '',  # str
    'status': '',  # 'operational' or 'unknown'
    'bands': '',  # str
    'notes': '',  # str
}


def read_entry_mcc(T, off):
    L = T[off]
    rec = dict(REC_MCC)
    if len(L) < 4:
        full = False
        rec['mcc'] = explore_text(L[0]).text.strip().upper()
        if len(L) > 2:
            rec['authority'] = _strip_wiki_ref(''.join(L[2].itertext()))
        if len(L) > 3:
            rec['notes'] = _strip_wiki_ref(''.join(L[3].itertext()))
    else:
        full = True
        rec['mcc'] = explore_text(L[0]).text.strip().upper()
        rec['code_alpha_2'] = explore_text(L[2]).text.strip()
        rec['country_name'], rec['country_url'] = _get_country_url(L[1])
        if rec['country_name'] is None:
            # Wikipedia layouts vary: find the first nested node with a country link.
            for e in L[1].iter():
                if e is L[1]:
                    continue
                rec['country_name'], rec['country_url'] = _get_country_url(e)
                if rec['country_name'] is not None:
                    break
        if rec['country_name'] is None:
            rec['country_name'] = re.sub(
                r'\s+', ' ', ''.join(L[1].itertext())
            ).strip()
            rec['country_url'] = ''
        rec['mcc_url'] = _get_first_href(L[3])
        if len(L) > 4:
            rec['authority'] = _strip_wiki_ref(''.join(L[4].itertext()))
        if len(L) > 5:
            rec['notes'] = _strip_wiki_ref(''.join(L[5].itertext()))
    return rec, full


def parse_table_mcc():
    # warning: for some MCC, there are duplicated entries (mostly for islands...)
    T = import_html_doc(URL_MCC).xpath('//table')
    T_MCC = T[1][1]
    L = []
    cc2 = set()
    mcc = {}
    for i in range(1, len(T_MCC)):
        rec, full = read_entry_mcc(T_MCC, i)
        if rec['mcc'] == 'YT':
            # MCC 647 entry is special, french... as usual !
            rec['mcc'] = '647'
            rec['mcc_url'] = L[-1]['mcc_url']
            rec['code_alpha_2'] = 'YT'
        if not full:
            if not rec['country_name']:
                rec['country_name'] = L[-1]['country_name']
                rec['country_url'] = L[-1]['country_url']
            if not rec['code_alpha_2']:
                rec['code_alpha_2'] = L[-1]['code_alpha_2']
            if not rec['authority'] and L[-1]['authority']:
                rec['authority'] = L[-1]['authority']
            if not rec['notes'] and L[-1]['notes']:
                rec['notes'] = L[-1]['notes']
        cc2.add(rec['code_alpha_2'])
        if rec['mcc'] in mcc:
            print(
                '> duplicate entry for MCC {}: {} // {}'.format(
                    rec['mcc'],
                    mcc[rec['mcc']]['country_name'],
                    rec['country_name'],
                )
            )
        else:
            mcc[rec['mcc']] = rec
        L.append(rec)
    L.sort(key=lambda r: (r['mcc'], r['code_alpha_2']))
    print(
        '[+] parsed %i MCC entries (%i unique MCC) for %i ISO-3166 country codes'
        % (len(L), len(mcc), len(cc2))
    )
    return L


def read_entry_mnc_title(e):
    name, url, sub, codes = '', '', None, []
    while e is not None:
        title = None
        if e.tag in ('h2', 'h3', 'h4', 'h5', 'h6'):
            title = e
        else:
            for i in e.xpath('.//h2|.//h3|.//h4|.//h5|.//h6'):
                if '\n' not in ''.join(i.itertext()):
                    title = i
                    break
        if title is not None:
            break
        else:
            e = e.getprevious()
    #
    # country name
    if title is None:
        raise (Exception('unable to find headline title for MNC country name'))
    title_txt = re.sub(r'\s+', ' ', ''.join(title.itertext())).strip()
    if title_txt.endswith('[edit]'):
        title_txt = title_txt[: -len('[edit]')].strip()
    if not title_txt:
        raise (Exception('invalid title format'))
    # country name + url
    name, url = _get_country_url(title)
    if name is None:
        for i in title.xpath('.//a'):
            name, url = _get_country_url(i)
            if name is not None:
                break
    if name is None:
        name = re.split(r'\s*[–-]\s*', title_txt, maxsplit=1)[0].strip()
        url = ''
    #
    # country alpha code
    # Warning, for EU MNC, separator is ' – ', whereas it is ' - ' for others
    m = re.search(
        r'\s*[–-]\s*([A-Za-z]{2}(?:\s*[-/]\s*[A-Za-z]{2})*)\s*$', title_txt
    )
    if not m:
        return name, url, sub, []
    codes = m.group(1)
    if '/' in codes:
        codes = [s.strip().upper() for s in sorted(codes.split('/'))]
    elif '-' in codes:
        codes = [s.strip().upper() for s in sorted(codes.split('-'))]
    else:
        codes = [codes]
    for code in codes:
        if len(code) != 2 or not code.isalpha():
            raise (Exception('invalid title format'))
    return name, url, sub, codes


def read_entry_mnc(T_MNC, off):
    L = T_MNC[off]
    rec = dict(REC_MNC)
    rec['mcc'] = explore_text(L[0]).text.strip()
    rec['mnc'] = explore_text(L[1]).text.strip()
    rec['brand'] = ''.join(L[2].itertext()).strip()
    rec['operator'] = ''.join(L[3].itertext()).strip()
    rec['status'] = explore_text(L[4]).text.strip().lower()
    rec['bands'] = ''.join(L[5].itertext()).strip()
    rec['notes'] = ''
    if len(L) == 7:
        rec['notes'] = _strip_wiki_refnote(
            _strip_wiki_ref(''.join(L[6].itertext()))
        )
    if len(rec['mcc']) > 3:
        # some HTML tab/ref in wikipedia may add the country name before the MCC
        rec['mcc'] = rec['mcc'][-3:]
    if rec['status'] != 'operational':
        rec['status'] = 'unknown'
    return rec


def parse_table_mnc(T_MNC):
    L = []
    mcc = set()
    #
    # get table title with country name
    title = T_MNC[1].getparent().getparent().getprevious()
    country_infos = read_entry_mnc_title(title)
    for i in range(1, len(T_MNC)):
        if len(T_MNC[i]) < 6:
            continue
        rec = read_entry_mnc(T_MNC, i)
        (
            rec['country_name'],
            rec['country_url'],
            rec['country_sub'],
            rec['codes_alpha_2'],
        ) = country_infos
        #
        # MNC values longer than 3 digits are typically private mobile networks (PMN).
        # MNC ranges (e.g., "100 - 190") are reserved blocks, not individual assignments.
        if (
            rec['mcc'].isdigit()
            and len(rec['mcc']) == 3
            and rec['mnc'].isdigit()
            and len(rec['mnc']) in (2, 3)
        ):
            mcc.add(rec['mcc'])
            L.append(rec)
        else:
            print(
                '> invalid MCC MNC entry {}.{}, operator {}'.format(rec['mcc'], rec['mnc'], rec['operator'])
            )
    print(
        '[+] parsed %i MNC entries for MCC %s'
        % (len(L), ', '.join(sorted(mcc)))
    )
    return L


def _insert_mnc(D, recs):
    mccmnc = set()
    for rec in recs:
        mcc0 = rec['mcc'][0]
        if mcc0 in D:
            D[mcc0].append(rec)
            mccmnc.add(rec['mcc'] + rec['mnc'])
        else:
            raise (Exception('invalid MCC {}'.format(rec['mcc'])))
    return mccmnc


def _is_mnc_table(table):
    """Detect MCC/MNC operator tables across Wikipedia layout variants."""
    header_txt = ''.join(table.itertext()).strip().upper()
    header_txt = re.sub(r'\s+', ' ', header_txt)
    if not header_txt:
        return False
    return header_txt.startswith('MCC MNC') or header_txt.startswith('MCCMNC')


def parse_table_mnc_all():
    mccmnc = set()
    D = {
        '0': [],
        '2': [],
        '3': [],
        '4': [],
        '5': [],
        '6': [],
        '7': [],
        '9': [],
    }
    #
    # 1) MNC worldwide
    T_MCC = import_html_doc(URL_MCC).xpath('//table')
    # test networks
    mccmnc.update(_insert_mnc(D, parse_table_mnc(T_MCC[0][0])))
    # intl networks
    mccmnc.update(_insert_mnc(D, parse_table_mnc(T_MCC[2][0])))
    # UK ocean territory
    mccmnc.update(_insert_mnc(D, parse_table_mnc(T_MCC[3][0])))
    for url in (
        URL_MNC_EU,
        URL_MNC_NA,
        URL_MNC_AS,
        URL_MNC_OC,
        URL_MNC_AF,
        URL_MNC_SA,
    ):
        T_MNC = import_html_doc(url).xpath('//table')
        for i in range(len(T_MNC)):
            if not _is_mnc_table(T_MNC[i]):
                continue
            try:
                mccmnc.update(_insert_mnc(D, parse_table_mnc(T_MNC[i][0])))
            except Exception as err:
                print(
                    '> unable to extract MNC table from %s (index %i): %r'
                    % (url, i, err)
                )
                raise (err)
    for L in D.values():
        L.sort(key=lambda r: (r['mcc'], r['mnc']))
    print(
        '[+] %i MCC MNC entries for %i unique MCC MNC'
        % (sum(map(len, D.values())), len(mccmnc))
    )
    return D


# ------------------------------------------------------------------------------#
# parsing Wikipedia international phone number prefixes
# ------------------------------------------------------------------------------#

# International phone number prefixes
URL_MSISDN = 'https://en.wikipedia.org/wiki/List_of_country_calling_codes'

MSISDN_CC2_ALIAS = {
    'bahamas': 'BS',
    'brunei darussalam': 'BN',
    'congo': 'CG',
    'congo, democratic republic of the': 'CD',
    'east timor': 'TL',
    'gambia': 'GM',
    'ireland': 'IE',
    'ivory coast': 'CI',
    'korea, north': 'KP',
    'korea, south': 'KR',
    'micronesia, federated states of': 'FM',
    'netherlands': 'NL',
    'united kingdom': 'GB',
    'united states': 'US',
    'us virgin islands': 'VI',
    'vatican city state': 'VA',
}

MSISDN_NAME_DROP = {
    'and',
    'darussalam',
    'democratic',
    'federated',
    'islamic',
    'kingdom',
    'of',
    'republic',
    'state',
    'states',
    'the',
}


def _canon_msisdn_name(name):
    n = name.lower()
    n = n.replace('côte', 'cote')
    n = n.replace('saint ', 'st ')
    n = n.replace('&', ' and ')
    n = re.sub(r'\(.*?\)', ' ', n)
    n = re.sub(r'[^a-z0-9, ]+', ' ', n)
    n = re.sub(r'\s+', ' ', n).strip(' ,')
    return n


def _canon_msisdn_tokens(name):
    toks = re.findall(r'[a-z0-9]+', _canon_msisdn_name(name))
    return tuple(sorted({t for t in toks if t not in MSISDN_NAME_DROP}))


def _resolve_msisdn_country_cc2(raw_name, by_name, by_tokens):
    name_key = _canon_msisdn_name(raw_name)
    if name_key in by_name:
        return by_name[name_key]
    if name_key in MSISDN_CC2_ALIAS:
        return MSISDN_CC2_ALIAS[name_key]
    toks = _canon_msisdn_tokens(raw_name)
    if toks in by_tokens and len(by_tokens[toks]) == 1:
        return by_tokens[toks][0]
    return None


def _extract_parenthetical_link_titles(cell):
    txt = re.sub(r'\s+', ' ', ''.join(cell.itertext())).strip()
    paren = re.findall(r'\(([^)]*)\)', txt)
    if not paren:
        return ()
    paren_norm = [p.lower() for p in paren]
    titles = []
    for a in cell.xpath('.//a[@title]'):
        title = a.attrib.get('title', '').strip()
        if not title:
            continue
        title_norm = title.lower()
        if any(title_norm in p for p in paren_norm) and title not in titles:
            titles.append(title)
    return tuple(titles)


RE_WIKI_MSISDN_PREF_ALL = re.compile(
    r'([1-9]{1}[0-9]{0,2})(?:\s*\(([0-9]{1,}(?:,\s*[0-9]{1,})*)\))?'
)


def _extract_msisdn_prefixes(pref_txt):
    prefs = []
    for m in RE_WIKI_MSISDN_PREF_ALL.finditer(pref_txt):
        pref, pref_exts = m.groups()
        if pref_exts:
            prefs.extend(
                [
                    pref + ext
                    for ext in sorted(map(str.strip, pref_exts.split(',')))
                ]
            )
        else:
            prefs.append(pref)
    # Keep order while removing duplicates.
    return tuple(dict.fromkeys(prefs))


# from simple 1 to 3 digits string to extended prefixes e.g., 374 (47, 97)
RE_WIKI_MSISDN_PREF = re.compile(
    r'([1-9]{1}[0-9]{0,2})(?: \(([0-9]{1,}(?:, {0,1}[0-9]{1,}){0,})\)){0,1}'
)


def parse_table_msisdn_pref_alphaord(T):
    # parse the serving/code table, with {country_or_area: tuple(prefixes)}
    D = {}
    for L in T[2:]:
        if len(L) < 2:
            continue
        name = re.sub(r'\s+', ' ', ''.join(L[0].itertext())).strip()
        prefs = re.sub(r'\s+', ' ', ''.join(L[1].itertext())).strip()
        if not name or not prefs:
            continue
        pref_list = _extract_msisdn_prefixes(prefs)
        if not pref_list:
            continue
        D[name] = pref_list
    return D


def parse_table_msisdn_pref_over(T, root=None):
    # Parse serving/code table (current Wikipedia layout).
    # Returns {prefix: [(CC2, country name, country url, prefix url), ...]}
    D = {}
    D_iso = parse_table_iso3166()
    by_cc2 = {}
    by_name = {}
    by_tokens = {}
    for cc2, rec in sorted(D_iso.items()):
        by_cc2[cc2] = rec
        by_name[_canon_msisdn_name(rec['country_name'])] = cc2
        toks = _canon_msisdn_tokens(rec['country_name'])
        if toks not in by_tokens:
            by_tokens[toks] = [cc2]
        else:
            by_tokens[toks].append(cc2)
    unresolved = set()
    for L in T[2:]:
        if len(L) < 2:
            continue
        raw_name = re.sub(r'\s+', ' ', ''.join(L[0].itertext())).strip()
        prefs_txt = re.sub(r'\s+', ' ', ''.join(L[1].itertext())).strip()
        if not raw_name or not prefs_txt:
            continue
        pref_list = _extract_msisdn_prefixes(prefs_txt)
        if not pref_list:
            continue
        cc2_list = []
        cc2_main = _resolve_msisdn_country_cc2(raw_name, by_name, by_tokens)
        if cc2_main in by_cc2:
            cc2_list.append(cc2_main)
        # Keep backward-safe behavior: only enrich from explicit links inside
        # parenthesized text, e.g. "Morocco (including Western Sahara)".
        for title in _extract_parenthetical_link_titles(L[0]):
            cc2_extra = _resolve_msisdn_country_cc2(title, by_name, by_tokens)
            if cc2_extra in by_cc2 and cc2_extra not in cc2_list:
                cc2_list.append(cc2_extra)
        if not cc2_list:
            unresolved.add(raw_name)
            continue
        pref_url = _get_first_href(L[1])
        for cc2 in cc2_list:
            rec_iso = by_cc2[cc2]
            rec_pref_url = pref_url or rec_iso['country_url'] or URL_MSISDN
            rec = (
                cc2,
                rec_iso['country_name'],
                rec_iso['country_url'],
                rec_pref_url,
            )
            for pref in pref_list:
                if pref not in D:
                    D[pref] = [rec]
                elif rec not in D[pref]:
                    D[pref].append(rec)
    for vals in D.values():
        vals.sort(key=lambda x: x[0])

    if root is not None:
        for li in root.xpath('//li'):
            txt = re.sub(r'\s+', ' ', ''.join(li.itertext())).strip()
            if not txt or '(' not in txt or 'including' not in txt.lower():
                continue
            pref_list = _extract_msisdn_prefixes(txt)
            if not pref_list:
                continue
            pref_url = _get_first_href(li)
            for title in _extract_parenthetical_link_titles(li):
                cc2 = _resolve_msisdn_country_cc2(title, by_name, by_tokens)
                if cc2 is None or cc2 not in by_cc2:
                    continue
                rec_iso = by_cc2[cc2]
                rec_pref_url = pref_url or rec_iso['country_url'] or URL_MSISDN
                rec = (
                    cc2,
                    rec_iso['country_name'],
                    rec_iso['country_url'],
                    rec_pref_url,
                )
                for pref in pref_list:
                    if pref not in D:
                        D[pref] = [rec]
                    elif rec not in D[pref]:
                        D[pref].append(rec)

    for vals in D.values():
        vals.sort(key=lambda x: x[0])

    if unresolved:
        print(
            '> unresolved MSISDN serving rows: {}'.format(', '.join(sorted(unresolved)))
        )
    return D


def parse_table_msisdn_pref_locnocount(T):
    # parse the "Locations with no country code" table, with
    # {location name: (prefix, country, location_url)}
    D = {}
    for L in T[1:]:
        if len(L) < 3:
            continue
        name = re.sub(r'\s+', ' ', ''.join(L[0].itertext())).strip()
        if not name:
            continue
        pref_txt = re.sub(r'\s+', ' ', ''.join(L[1].itertext())).strip()
        if not pref_txt:
            continue
        m = RE_WIKI_MSISDN_PREF.match(pref_txt)
        if m:
            pref, pref_exts = m.groups()
            if pref_exts:
                pref = pref + sorted(map(str.strip, pref_exts.split(',')))[0]
        else:
            pref = ''.join([c for c in pref_txt if c.isdigit()])
        if not pref:
            continue
        url = _get_first_href(L[0])
        cntr = re.sub(r'\s+', ' ', ''.join(L[2].itertext())).strip()
        if not cntr:
            cntr = name
        if name not in D:
            D[name] = (pref, cntr, url)
    return D


def parse_table_msisdn_pref():
    root = import_html_doc(URL_MSISDN)
    T = root.xpath('//table')
    #
    # Pick tables by header content from the current Wikipedia layout.
    t_alpha = None
    t_loc = None
    for table in T:
        if not len(table):
            continue
        body = table[0]
        if not len(body):
            continue
        row0 = re.sub(r'\s+', ' ', ''.join(body[0].itertext())).strip().lower()
        if 'serving' in row0 and 'code' in row0:
            t_alpha = body
        elif 'location' in row0 and 'reasons for no code' in row0:
            t_loc = body
    if t_alpha is None:
        raise Exception(
            'unable to locate required MSISDN tables on {}'.format(URL_MSISDN)
        )
    if t_loc is None:
        t_loc = []
    #
    # extract the dict of {country_or_area: calling prefixes}
    # extract the dict of {MSISDN prefix: country infos}
    # extract the dict of {location with no country code: country code info}
    return (
        parse_table_msisdn_pref_alphaord(t_alpha),
        parse_table_msisdn_pref_over(t_alpha, root),
        parse_table_msisdn_pref_locnocount(t_loc),
    )


# ------------------------------------------------------------------------------#
# parsing Wikipedia country borders
# ------------------------------------------------------------------------------#

# this is used for both Wikipedia and World Factbook
CRAPPY_BORDERS = {
    'Dahagram-Angarpota': 'India',
}


# Countries and borders
URL_BORDERS = 'https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_land_borders'


REC_BORDERS = {
    'country_name': '',  # str
    'country_url': '',  # str
    'country_sub': [],  # list of 2-tuple of str, included countries / territories (country_name, country_url)
    'border_len_km': 0,  # int
    'border_len_mi': 0,  # int
    'neigh_num': 0,  # int
    'neigh': [],  # list of 2-tuple or str, neighbour countries (country_name, country_url)
}


# list of countries for which Wikipédia count of borders does not correspond
# to the list of border countries
BORDER_ISSUE = {
    'Afghanistan',
    'China',
    'Georgia',
    'India',
    'Israel',
    'Russia',
}


BORDER_RECONCILE_RULES = {
    # Keep territorial land-border entity, drop sovereign duplicate.
    'Brazil': [('French Guiana', 'France')],
    'Suriname': [('French Guiana', 'France')],
    'Canada': [('Greenland', 'Kingdom of Denmark')],
    'Cyprus': [('Akrotiri and Dhekelia', 'United Kingdom')],
    'Sweden': [('Finland', 'Åland')],
    # Keep specific territory/crossing label, drop broader duplicate.
    'Jordan': [('State of Palestine', 'West Bank')],
    'Egypt': [('Gaza Strip', 'State of Palestine')],
    'Kingdom of the Netherlands': [('Collectivity of Saint Martin', 'France')],
    'France': [('Sint Maarten', 'Kingdom of the Netherlands')],
    # Wikipedia row currently reports 0 land neighbors for Cuba.
    'Cuba': [(None, 'United States')],
}


def _stripbordref(s):
    n = re.sub(r'\s{1,}', ' ', re.sub(r'\(.*?\)|\[.*?\]', ' ', s).strip())
    if ':' in n:
        n = n.split(':')[0].rstrip()
    if ' 0.' in n:
        n = n.split(' 0.')[0].rstrip()
    if n in CRAPPY_BORDERS:
        n = CRAPPY_BORDERS[n]
    return n


def _get_bord(e):
    # Current Wikipedia layout puts one country per hyperlink in neighbour rows.
    b = set()
    for a in e.xpath('.//a[@title]'):
        title = a.attrib.get('title', '').strip()
        if title and title[0].isupper():
            b.add(_stripbordref(title))
    return sorted(b)


def _reconcile_bord(country_name, neigh):
    rules = BORDER_RECONCILE_RULES.get(country_name, ())
    if not rules:
        return neigh
    cur = set(neigh)
    for keep, drop in rules:
        if drop not in cur:
            continue
        if keep is None or keep in cur:
            cur.remove(drop)
    return sorted(cur)


def _get_int(s):
    m = re.match('[0-9]{1,}', s)
    if not m:
        return 0
    else:
        return int(m.group())


def _get_subcntr(ec):
    subc = []
    for e in ec:
        if 'href' in e.attrib:
            subc.append(
                (e.attrib['title'].strip(), URL_PREF + e.attrib['href'])
            )
    return subc


def read_entry_borders(T, off):
    L = T[off]
    rec = dict(REC_BORDERS)
    rec['country_sub'] = []
    rec['neigh'] = []
    #
    # rec['dbg']           = L
    rec['country_name'], rec['country_url'] = _get_country_url(L[0])
    rec['border_len_km'] = int(
        explore_text(L[1]).text.strip().replace(',', '').split('.')[0]
    )
    rec['border_len_mi'] = int(
        explore_text(L[2]).text.strip().replace(',', '').split('.')[0]
    )
    rec['neigh_num'] = _get_int(explore_text(L[4]).text.strip())
    if len(L[0]) >= 3 and len(L[0][2]) >= 2 and len(L[0][2][1]) >= 2:
        # get list of sub countries
        # listed after '→includes:'
        subc = _get_subcntr(L[0][2][1])
        if subc:
            subc.sort(key=lambda t: t[0])
            rec['country_sub'] = subc
    if len(L) >= 6:
        # get list of neighbours

        rec['neigh'] = _reconcile_bord(rec['country_name'], _get_bord(L[5]))
        if rec['country_name'] not in BORDER_ISSUE and rec['neigh_num'] != len(
            rec['neigh']
        ):
            print(
                '> border count mismatch for %s: expected %i, parsed %i'
                % (rec['country_name'], rec['neigh_num'], len(rec['neigh']))
            )
    return rec


def parse_table_borders():
    T = import_html_doc(URL_BORDERS).xpath('//table')
    T_B = T[1][0]
    L = []
    cns = set()
    for i in range(2, len(T_B)):
        # Some rows have no explicit neighbours cell (5 columns only):
        # keep them and rely on default empty neighbour list.
        if len(T_B[i]) < 5:
            continue
        rec = read_entry_borders(T_B, i)
        if rec['country_name'] in cns:
            print('> duplicate borders entry for {}'.format(rec['country_name']))
        else:
            cns.add(rec['country_name'])
        L.append(rec)
    assert L
    L.sort(key=lambda r: r['country_name'])
    return L


# ------------------------------------------------------------------------------#
# Main
# ------------------------------------------------------------------------------#


def get_wiki_infos():
    try:
        D_iso = parse_table_iso3166()
    except Exception as err:
        print(
            'parse_table_iso3166: unable to download and / or parse Wikipedia HTML tables ; exception: {!r}'.format(err)
        )
        return None, None, None, None, None, None, None
    try:
        L_mcc = parse_table_mcc()
    except Exception as err:
        print(
            'parse_table_mcc: unable to download and / or parse Wikipedia HTML tables ; exception: {!r}'.format(err)
        )
        return None, None, None, None, None, None, None
    try:
        D_mnc = parse_table_mnc_all()
    except Exception as err:
        print(
            'parse_table_mnc_all: unable to download and / or parse Wikipedia HTML tables ; exception: {!r}'.format(err)
        )
        return None, None, None, None, None, None, None
    try:
        D_count, D_pref, D_terr = parse_table_msisdn_pref()
    except Exception as err:
        print(
            'parse_table_msisdn_pref: unable to download and / or parse Wikipedia HTML tables ; exception: {!r}'.format(err)
        )
        return None, None, None, None, None, None, None
    try:
        L_bord = parse_table_borders()
    except Exception as err:
        print(
            'parse_table_borders: unable to download and / or parse Wikipedia HTML tables ; exception: {!r}'.format(err)
        )
        return None, None, None, None, None, None, None
    return D_iso, L_mcc, D_mnc, D_pref, D_count, D_terr, L_bord


def generate_json(d, destfile, src, license):
    meta = {'source': src, 'license': license}
    with open(destfile, 'w', encoding='utf-8') as fd:
        json.dump([meta, d], fp=fd, sort_keys=True, indent=2)
        fd.write('\n')
    print('[+] {} file generated'.format(destfile))


def generate_python(d, destfile, src, license):
    pp = PrettyPrinter(indent=2, width=120)
    varname = destfile[:-3].split('/')[-1].upper()
    with open(destfile, 'w', encoding='utf-8') as fd:
        fd.write('# -*- coding: UTF-8 -*-\n')
        fd.write('# source: {}\n'.format(',\n#         '.join(src)))
        fd.write('# license: {}\n\n'.format(license))
        fd.write('{} = \\\n{}\n'.format(varname, pp.pformat(d)))
    print('[+] {} file generated'.format(destfile))


URL_LICENSE = 'https://en.wikipedia.org/wiki/Wikipedia:Text_of_Creative_Commons_Attribution-ShareAlike_3.0_Unported_License'


def main():
    parser = argparse.ArgumentParser(
        description='dump Wikipedia ISO-3166 country codes, MCC, MNC, numbering prefix and country borders tables into JSON or Python file'
    )
    parser.add_argument(
        '-j',
        action='store_true',
        help='produce JSON files (with suffix .json)',
    )
    parser.add_argument(
        '-p',
        action='store_true',
        help='produce Python files (with suffix .py)',
    )
    args = parser.parse_args()
    D_iso, L_mcc, D_mnc, D_pref, D_count, D_terr, L_bord = get_wiki_infos()
    if D_iso is None:
        return 1
    if args.j:
        generate_json(
            D_iso,
            PATH_PRE + 'wikip_iso3166.json',
            [URL_CODE_ALPHA_2],
            URL_LICENSE,
        )
        generate_json(
            L_mcc, PATH_PRE + 'wikip_mcc.json', [URL_MCC], URL_LICENSE
        )
        generate_json(
            D_mnc,
            PATH_PRE + 'wikip_mnc.json',
            [
                URL_MNC_EU,
                URL_MNC_NA,
                URL_MNC_AS,
                URL_MNC_OC,
                URL_MNC_AF,
                URL_MNC_SA,
            ],
            URL_LICENSE,
        )
        generate_json(
            D_pref, PATH_PRE + 'wikip_msisdn.json', [URL_MSISDN], URL_LICENSE
        )
        generate_json(
            D_count, PATH_PRE + 'wikip_country.json', [URL_MSISDN], URL_LICENSE
        )
        generate_json(
            D_terr,
            PATH_PRE + 'wikip_territory.json',
            [URL_MSISDN],
            URL_LICENSE,
        )
        generate_json(
            L_bord, PATH_PRE + 'wikip_borders.json', [URL_BORDERS], URL_LICENSE
        )
    if args.p:
        generate_python(
            D_iso,
            PATH_PRE + 'wikip_iso3166.py',
            [URL_CODE_ALPHA_2],
            URL_LICENSE,
        )
        generate_python(
            L_mcc, PATH_PRE + 'wikip_mcc.py', [URL_MCC], URL_LICENSE
        )
        generate_python(
            D_mnc,
            PATH_PRE + 'wikip_mnc.py',
            [
                URL_MNC_EU,
                URL_MNC_NA,
                URL_MNC_AS,
                URL_MNC_OC,
                URL_MNC_AF,
                URL_MNC_SA,
            ],
            URL_LICENSE,
        )
        generate_python(
            D_pref, PATH_PRE + 'wikip_msisdn.py', [URL_MSISDN], URL_LICENSE
        )
        generate_python(
            D_count, PATH_PRE + 'wikip_country.py', [URL_MSISDN], URL_LICENSE
        )
        generate_python(
            D_terr, PATH_PRE + 'wikip_territory.py', [URL_MSISDN], URL_LICENSE
        )
        generate_python(
            L_bord, PATH_PRE + 'wikip_borders.py', [URL_BORDERS], URL_LICENSE
        )
    return 0


if __name__ == '__main__':
    sys.exit(main())
