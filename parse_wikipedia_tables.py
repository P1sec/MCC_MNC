#!/usr/bin/env python3

import sys
import argparse
import urllib.request
import json
import re

from pprint import PrettyPrinter
from lxml   import etree



RE_WIKI_REF = re.compile(r'.*(\[.*\]){1,}$')

def _strip_wiki_ref(s):
    m = RE_WIKI_REF.match(s)
    if m:
        
        return s[:s.find('[')].strip()
    else:
        return s


#------------------------------------------------------------------------------#
# parsing Wikipedia ISO-3166 codes
#------------------------------------------------------------------------------#

URL_PREF          = "https://en.wikipedia.org"
URL_CODE_ALPHA_2  = "https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes"


REC_ISO3166 = {
    'country_name'          : '', # str, ISO 3166 country name
    'country_url'           : '', # url to the Wikipedia page of the country
    'state_name'            : '', # str
    'sovereignity'          : '', # str: UN member, UN observer, antarctic, disputed or another country_name
    'code_alpha_2'          : '', # 2-char
    'code_alpha_3'          : '', # 3-char
    'code_num'              : '', # 3-digit
    #'regions'               : {}, # dict of region code, region name
    'regions_url'           : '', # url to the Wikipedia page of the regional code
    'cc_tld'                : '', # str
    'cc_tld_url'            : '', # url to the Wikipedia page of the ccTLD
    }


RE_TEXT_INVAL   = re.compile(r'[!\:\{\}]')
is_text_valid   = lambda t: True if t.strip() and not RE_TEXT_INVAL.search(t) else False


SOVEREIGNITY_LUT = {
    'Finland'           : 'FI',
    'United States'     : 'US',
    'United Kingdom'    : 'GB',
    'Netherlands'       : 'NL',
    'Norway'            : 'NO',
    'Australia'         : 'AU',
    'New Zealand'       : 'NZ',
    'Denmark'           : 'DK',
    'France'            : 'FR',
    'British Crown'     : 'GB', # this is not exactly true, however...
    'China'             : 'CN',
    'UN member state'   : 'UN member',
    'UN observer'       : 'UN observer',
    'Antarctic Treaty'  : 'Antarctica',
    'disputed'          : 'disputed'
    }


def import_wikipedia_table(url):
    resp = urllib.request.urlopen(url)
    if resp.code == 200:
        R = etree.parse(resp, etree.HTMLParser()).getroot()
    else:
        raise(Exception('resource %s not available, HTTP code %i' % (url, resp.code)))
    #
    return R.xpath('//table')


def explore_text(E):
    #print(E)
    if E.text is not None and is_text_valid(E.text):
        return E
    for e in E:
        t = explore_text(e)
        if t is not None and t.text is not None and is_text_valid(t.text):
            return t


def _get_country_url(e):
    e = explore_text(e)
    if e is not None:
        if len(e.values()) == 2:
            url, name = e.values()
            if name == 'List of French islands in the Indian and Pacific oceans':
                name = e.text.strip()
            return name, URL_PREF + url
        elif len(e.values()) == 3:
            url, _, name = e.values()
            if name == 'List of French islands in the Indian and Pacific oceans':
                name = e.text.strip()
            return name, URL_PREF + url
        #print(e.text)
    return None, None


def read_entry_iso3166(T, off):
    L   = T[off]
    rec = dict(REC_ISO3166)
    #
    rec['country_name'], rec['country_url'] = _get_country_url(L[0])
    rec['state_name']   = explore_text(L[1]).text.strip()
    rec['sovereignity'] = SOVEREIGNITY_LUT[explore_text(L[2]).text.strip()]
    rec['code_alpha_2'] = explore_text(L[3]).text.strip().upper()
    rec['code_alpha_3'] = explore_text(L[4]).text.strip().upper()
    rec['code_num']     = explore_text(L[5]).text.strip()
    #rec['regions']      =
    rec['regions_url']  = URL_PREF + L[6][0].values()[0]
    rec['cc_tld']       = explore_text(L[7]).text.strip().lower()
    rec['cc_tld_url']   = URL_PREF + explore_text(L[7]).values()[0]
    return rec


def parse_table_iso3166():
    T    = import_wikipedia_table(URL_CODE_ALPHA_2)
    T_CC = T[0][0]
    D    = {}
    for i in range(2, len(T_CC)):
        try:
            rec = read_entry_iso3166(T_CC, i)
        except IndexError:
            #print('no entry at rank %i, after %s' % (i, rec['country_name']))
            pass
        else:
            if rec['code_alpha_2'] in D:
                raise(Exception('duplicate entries for %s' % rec['code_alpha_2']))
            else:
                D[rec['code_alpha_2']] = rec
    print('[+] parsed %i ISO-3166 country codes' % len(D))
    return D


#------------------------------------------------------------------------------#
# parsing Wikipedia MCC and MNC
#------------------------------------------------------------------------------#

# MCC and international operators
URL_MCC     = "https://en.wikipedia.org/wiki/Mobile_country_code"
# nationa operators
URL_MNC_EU  = "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_2xx_(Europe)"
URL_MNC_NA  = "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_3xx_(North_America)"
URL_MNC_AS  = "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_4xx_(Asia)"
URL_MNC_OC  = "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_5xx_(Oceania)"
URL_MNC_AF  = "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_6xx_(Africa)"
URL_MNC_SA  = "https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_7xx_(South_America)"


REC_MCC = {
    'mcc'           : '', # 3-digit str
    'country_name'  : '', # str
    'country_url'   : '', # str
    'code_alpha_2'  : '', # 2-char
    'mcc_url'       : '', # str
    'authority'     : '', # str
    'notes'         : '', # str
    }


REC_MNC = {
    'country_name'  : '', # str
    'codes_alpha_2' : [], # list of 2-char
    'mcc'           : '', # 3-digit str
    'mnc'           : '', # 2 or 3-digit str
    'brand'         : '', # str
    'operator'      : '', # str
    'status'        : '', # 'operational' or 'unknown'
    'bands'         : '', # str
    'notes'         : '', # str
    }


# for status: unknown
NET_STATUS_UNKOWN = {
    'allocated',
    'implement / design',
    'not operational',
    'ongoing',
    'planned',
    'reserved',
    'returned spare',
    'temporary operational',
    'test network',
    'testing',
    'unknown'
    }


def read_entry_mcc(T, off):
    L   = T[off]
    rec = dict(REC_MCC)
    if len(L) < 4:
        full                = False
        rec['mcc']          = explore_text(L[0]).text.strip().upper()
        if len(L) > 2:
            rec['authority'] = _strip_wiki_ref(''.join(L[2].itertext()))
        if len(L) > 3:
            rec['notes']     = _strip_wiki_ref(''.join(L[3].itertext()))
    else:
        full                = True
        rec['mcc']          = explore_text(L[0]).text.strip().upper()
        rec['code_alpha_2'] = explore_text(L[2]).text.strip()
        rec['country_name'], rec['country_url'] = _get_country_url(L[1])
        if len(rec['country_name']) == 1:
            # hidden HTML element with 1st letter of the country, jump over it
            rec['country_name'], rec['country_url'] = _get_country_url(L[1][1])
        mcc_url = explore_text(L[3]).values()
        if mcc_url:
            rec['mcc_url']      = URL_PREF + mcc_url[0]
        if len(L) > 4:
            rec['authority'] = _strip_wiki_ref(''.join(L[4].itertext()))
        if len(L) > 5:
            rec['notes']     = _strip_wiki_ref(''.join(L[5].itertext()))
    return rec, full


def parse_table_mcc():
    # warning: for some MCC, there are duplicated entries (mostly for islands...)
    T     = import_wikipedia_table(URL_MCC)
    T_MCC = T[1][0]
    L     = []
    cc2   = set()
    mcc   = {}
    for i in range(1, len(T_MCC)):
        rec, full = read_entry_mcc(T_MCC, i)
        if rec['mcc'] == 'YT':
            # MCC 647 entry is special, french... as usual !
            rec['mcc']          = '647'
            rec['mcc_url']      = L[-1]['mcc_url']
            rec['code_alpha_2'] = 'YT'
        #
        if not full:
            if not rec['country_name']:
                rec['country_name'] = L[-1]['country_name']
                rec['country_url']  = L[-1]['country_url']
            if not rec['code_alpha_2']:
                rec['code_alpha_2'] = L[-1]['code_alpha_2']
            if not rec['authority'] and L[-1]['authority']:
                rec['authority'] = L[-1]['authority']
            if not rec['notes'] and L[-1]['notes']:
                rec['notes']     = L[-1]['notes']
        #
        if len(rec['country_name']) == 1:
            rec['L'] = T_MCC[i]
        
        cc2.add(rec['code_alpha_2'])
        if rec['mcc'] in mcc:
            print('> duplicate entry for MCC %s: %s // %s'\
                  % (rec['mcc'], mcc[rec['mcc']]['country_name'], rec['country_name']))
        else:
            mcc[rec['mcc']] = rec
        L.append(rec)
    #
    L.sort(key=lambda r: (r['mcc'], r['code_alpha_2']))
    print('[+] parsed %i MCC entries (%i unique MCC) for %i ISO-3166 country codes'\
          % (len(L), len(mcc), len(cc2)))
    return L


def read_entry_mnc_title(e):
    
    
    # TODO: for the country name, get country name and url with _get_country_url()
    
    
    text = _strip_wiki_ref(''.join(e.itertext()).strip())
    country, codes = map(str.strip, text.split(' - '))
    if '/' in codes:
        codes = list(map(str.upper, sorted(codes.split('/'))))
    elif '-' in codes:
        codes = list(map(str.upper, sorted(codes.split('-'))))
    else:
        codes = [codes]
    for code in codes:
        if len(code) != 2 or not code.isalpha():
            raise(Exception('invalid title format'))
    return country, codes
    

def read_entry_mnc(T_MNC, off):
    L   = T_MNC[off]
    rec = dict(REC_MNC)
    rec['mcc']          = explore_text(L[0]).text.strip()
    rec['mnc']          = explore_text(L[1]).text.strip()
    rec['brand']        = ''.join(L[2].itertext()).strip()
    rec['operator']     = ''.join(L[3].itertext()).strip()
    rec['status']       = explore_text(L[4]).text.strip().lower()
    rec['bands']        = ''.join(L[5].itertext()).strip()
    rec['notes']        = _strip_wiki_ref(''.join(L[6].itertext()).strip())
    if len(rec['mcc']) > 3:
        # some HTML tab/ref in wikipedia may add the country name before the MCC
        rec['mcc'] = rec['mcc'][-3:]
    if rec['status'] in NET_STATUS_UNKOWN:
        rec['status']   = 'unknown'
    elif rec['status'] != 'operational':
        raise(Exception('invalid status %s for %s.%s'\
              % (rec['status'], rec['mcc'], rec['mnc'])))
    #
    # get country name and alpha code from the tab title
    country, code, title = None, None, L.getparent().getparent().getprevious()
    while country is None and code is None:
        try:
            country, codes = read_entry_mnc_title(title)
        except Exception:
            try:
                title = title.getprevious()
            except Exception:
                break
        else:
            rec['country_name'], rec['codes_alpha_2'] = country, codes
    return rec


def parse_table_mnc(T_MNC):
    L       = []
    mcc     = set()
    mccmnc  = {}
    for i in range(1, len(T_MNC)):
        rec = read_entry_mnc(T_MNC, i)
        if rec['mcc'].isdigit() and len(rec['mcc']) == 3 \
        and rec['mnc'].isdigit() and len(rec['mnc']) in (2, 3):
            mcc.add(rec['mcc'])
            L.append(rec)
        else:
            print('> invalid MCC MNC entry %s.%s, operator %s' % (rec['mcc'], rec['mnc'], rec['operator']))
    print('[+] parsed %i MNC entries for MCC %s' % (len(L), ', '.join(sorted(mcc))))
    return L


def _insert_mnc(D, recs):
    mccmnc = set()
    for rec in recs:
        mcc0 = rec['mcc'][0]
        if mcc0 in D:
            D[mcc0].append(rec)
            mccmnc.add( rec['mcc'] + rec['mnc'] )
        else:
            raise(Exception('invalid MCC %s' % rec['mcc']))
    return mccmnc


def parse_table_mnc_all():
    mccmnc = set()
    D = {'0': [], '2': [], '3': [], '4': [], '5': [], '6': [], '7': [], '9': []}
    #
    # 1) MNC worldwide
    T_MCC = import_wikipedia_table(URL_MCC)
    # test networks
    mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MCC[0][0])) )
    # intl networks
    mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MCC[2][0])) )
    # UK ocean territory
    mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MCC[3][0])) )
    #
    # 2) MNC for EU
    T_MNC_EU = import_wikipedia_table(URL_MNC_EU)
    for i in range(0, len(T_MNC_EU)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_EU[i][0])) )
    #
    # 3) MNC for North America
    T_MNC_NA = import_wikipedia_table(URL_MNC_NA)
    for i in range(0, len(T_MNC_NA)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_NA[i][0])) )
    #
    # 4) MNC for Asia
    T_MNC_AS = import_wikipedia_table(URL_MNC_AS)
    for i in range(0, len(T_MNC_AS)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_AS[i][0])) )
    #
    # 5) MNC for Oceania
    T_MNC_OC = import_wikipedia_table(URL_MNC_OC)
    for i in range(0, len(T_MNC_OC)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_OC[i][0])) )
    #
    # 6) MNC for Africa
    T_MNC_AF = import_wikipedia_table(URL_MNC_AF)
    for i in range(0, len(T_MNC_AF)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_AF[i][0])) )
    #
    # 7) MNC for South America
    T_MNC_SA = import_wikipedia_table(URL_MNC_SA)
    for i in range(0, len(T_MNC_SA)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_SA[i][0])) )
    #
    for L in D.values():
        L.sort(key=lambda r: (r['mcc'], r['mnc']))
    #
    print('[+] %i MCC MNC entries for %i unique MCC MNC'\
          % (sum(map(len, D.values())), len(mccmnc)))
    return D


#------------------------------------------------------------------------------#
# parsing Wikipedia international phone number prefixes
#------------------------------------------------------------------------------#

# International phone number prefixes
URL_MSISDN = "https://en.wikipedia.org/wiki/List_of_country_calling_codes"

# regexp to match "+123: AA"-like pattern
RE_WIKI_MSISDN_PREF = re.compile(r'^\+([0-9 ]{1,})\:[ ]{0,}([A-Z]{2}(,\s{0,}[A-Z]{2}){0,})$')


def parse_table_msisdn_pref():
    T   = import_wikipedia_table(URL_MSISDN)
    D   = {}
    T_P = T[0][0]
    #
    # 2nd line: +1 prefix (North America)
    T_NA = T_P[2][1][0]
    ccs  = set()
    for i in range(3, len(T_NA)):
        cc = T_NA[i].text.strip()
        if cc:
            ccs.add(cc)
    D['1'] = ccs
    #
    # other prefixes
    for i in range(3, len(T_P)):
        for j in range(0, len(T_P[i])):
            for infos in ''.join(T_P[i][j].itertext()).split('\n'):
                m = RE_WIKI_MSISDN_PREF.match(infos)
                if m:
                    pref, ccs = m.group(1), [c for c in map(str.strip, m.group(2).split(','))]
                    pref = pref.replace(' ', '')
                    if pref in D:
                        D[pref].update(ccs)
                    else:
                        D[pref] = ccs
                #elif infos:
                #    print(infos)
    #
    # convert set to list
    for pref, ccs in D.items():
        D[pref] = list(sorted(ccs))
    #
    return D


#------------------------------------------------------------------------------#
# parsing Wikipedia country borders
#------------------------------------------------------------------------------#

# Countries and borders
URL_BORDERS = "https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_land_borders"


REC_BORDERS = {
    'country_name'  : '', # str
    'country_url'   : '', # str
    'country_sub'   : [], # list of 2-tuple, included countries / territories (country_name, country_url)
    'border_len_km' : 0,  # int
    'border_len_mi' : 0,  # int
    'neigh_num'     : 0,  # int
    'neigh'         : [], # list of 2-tuple, neighbour countries (country_name, country_url)
    }


def read_entry_borders(T, off):
    L   = T[off]
    rec = dict(REC_BORDERS)
    #
    
    
    # TODO: for country name and url, use _get_country_url()
    
    
    url, name = explore_text(L[0]).values()
    neigh_num = explore_text(L[4]).text.strip()
    rec['country_url']   = URL_PREF + url.strip()
    rec['country_name']  = name.strip()
    rec['border_len_km'] = int(explore_text(L[1]).text.strip().replace(',', '').split('.')[0])
    rec['border_len_mi'] = int(explore_text(L[2]).text.strip().replace(',', '').split('.')[0])
    if '(' in neigh_num:
        rec['neigh_num'] = int(neigh_num.split('(')[0].strip())
    else:
        rec['neigh_num'] = int(neigh_num.strip())
    #
    if len(L[0]) >= 2 and len(L[0][1]) >= 2 and len(L[0][1][1]) >= 2:
        # sub countries
        sub = []
        for e in L[0][1][1]:
            e = explore_text(e)
            if e is not None:
                if len(e.values()) == 2:
                    url, name = e.values()
                    sub.append( (name, URL_PREF + url) )
                elif len(e.values()) == 3:
                    url, _, name = e.values()
                    sub.append( (name, URL_PREF + url) )
                #else:
                #    print(e.text)
        if sub:
            sub.sort(key=lambda t: t[0])
            rec['country_sub'] = sub
    #
    if len(L) >= 6 and len(L[5]) >= 1 and len(L[5][0]) >= 2:
        # neighbours
        neigh = []
        for e in L[5][0][1]:
            e = explore_text(e)
            if e is not None:
                if len(e.values()) == 2:
                    url, name = e.values()
                    neigh.append( (name, URL_PREF + url) )
                elif len(e.values()) == 3:
                    url, _, name = e.values()
                    neigh.append( (name, URL_PREF + url) )
                #else:
                #    print(e.text)
        if neigh:
            neigh.sort(key=lambda t: t[0])
            rec['neigh'] = neigh
    #
    return rec


def parse_table_borders():
    T   = import_wikipedia_table(URL_BORDERS)
    T_B = T[0][0]
    L   = []
    cns = set()
    for i in range(3, len(T_B)):
        rec = read_entry_borders(T_B, i)
        if rec['country_name'] in cns:
            print('> duplicate borders entry for %s' % rec['country_name'])
        else:
            cns.add(rec['country_name'])
        L.append(rec)
    L.sort(key=lambda r: r['country_name'])
    return L


'''to be moved to another Python script
#------------------------------------------------------------------------------#
# Consolidate
#------------------------------------------------------------------------------#

def consolidate_dict_mnc(D_mnc, L_mcc, D_iso):
    # consolidate the list / dicts produced by parse_table_mnc_all
    # 1) get all country codes
    MccIso = {}
    
    
    MccMnc = {'0': {}, '2': {}, '3': {}, '4': {}, '5': {}, '6': {}, '7': {}, '9': {}}
    #
    
    #
    for (mcc0, recs) in sorted(D_mnc.items()):
        for rec in sorted(recs, key=lambda r: r['operator']):
            mccmnc = rec['mcc'] + rec['mnc']
            # consolidate the set of countries / country codes for the given MCC MNC
            consolidate_country(rec, [], [])
            if mccmnc in MccMnc[mcc0]:
                # consolidate against MCC MNC duplicates
                MccMnc[mcc0][mccmnc] = consolidate_duplicate(MccMnc[mcc0][mccmnc], rec) 
            else:
                MccMnc[mcc0][mccmnc] = rec
    return MccMnc


def consolidate_country(rec_mnc, rec_mcc, rec_iso):
    # From the 
    pass


def consolidate_duplicate(rec_n, rec_o):
    # 1) keep only the operational one
    if rec_o['status'] == 'unknown' and rec_n['status'] == 'operational':
        return rec_n
    elif rec_n['status'] == 'unknown' and rec_o['status'] == 'operational':
        return rec_o
    #
    # 2) 
    if rec_o['operator'] == rec_n['operator']:
        # same operator, both are unknown or operational
        
        
        pass
    
    else:
        # different operator
        
        
        print('> duplicate entry for MCC %s MNC %s: {%s} %s %s (%s) // {%s} %s %s (%s)'\
              % (rec_o['mcc'], rec_o['mnc'],
                 ', '.join(rec_o['codes_alpha_2']), rec_o['operator'], rec_o['bands'], rec_o['status'],
                 ', '.join(rec_n['codes_alpha_2']), rec_n['operator'], rec_n['bands'], rec_n['status']))
    
    
    return rec_n
'''

#------------------------------------------------------------------------------#
# Main
#------------------------------------------------------------------------------#

def get_wiki_infos():
    try:
        D_iso  = parse_table_iso3166()
        L_mcc  = parse_table_mcc()
        D_mnc  = parse_table_mnc_all()
        D_pref = parse_table_msisdn_pref()
        L_bord = parse_table_borders()
    except Exception as err:
        print('unable to download and / or parse Wikipedia HTML tables ; exception: %s' % err)
        return None, None, None, None, None
    else:
        return D_iso, L_mcc, D_mnc, D_pref, L_bord


def generate_json(d, destfile):
    with open(destfile, 'w') as fd:
        json.dump(d, fp=fd, sort_keys=True, indent=2)
        fd.write('\n')
    print('[+] %s file generated' % destfile)


def generate_python(d, destfile):
    pp = PrettyPrinter(indent=2, width=120)
    varname = destfile[:-3].upper()
    with open(destfile, 'w') as fd:
        fd.write('%s = \\\n%s\n' % (varname, pp.pformat(d)))
    print('[+] %s file generated' % destfile)


def main():
    parser = argparse.ArgumentParser(description=
        'dump Wikipedia ISO-3166 country codes, MCC, MNC, numbering prefix and country borders tables into JSON or Python file')
    parser.add_argument('-j', action='store_true', help='produce JSON files (with suffix .json)')
    parser.add_argument('-p', action='store_true', help='produce Python files (with suffix .py)')
    args = parser.parse_args()
    D_iso, L_mcc, D_mnc, D_pref, L_bord = get_wiki_infos()
    if D_iso is None:
        return 1
    #
    if args.j:
        generate_json(D_iso, 'wikip_iso3166.json')
        generate_json(L_mcc, 'wikip_mcc.json')
        generate_json(D_mnc, 'wikip_mnc.json')
        generate_json(D_pref, 'wikip_msisdn.json')
        generate_json(L_bord, 'wikip_borders.json')
    if args.p:
        generate_python(D_iso, 'wikip_iso3166.py')
        generate_python(L_mcc, 'wikip_mcc.py')
        generate_python(D_mnc, 'wikip_mnc.py')
        generate_python(D_pref, 'wikip_msisdn.py')
        generate_python(L_bord, 'wikip_borders.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
