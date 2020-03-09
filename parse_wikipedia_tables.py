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


def read_entry_iso3166(T, off):
    L   = T[off]
    rec = dict(REC_ISO3166)
    #
    rec['country_name'] = explore_text(L[0]).text.strip()
    rec['country_url']  = URL_PREF + explore_text(L[0]).values()[0]
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
    D    = {}
    T_CC = T[0][0]
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
# parsing Wikipedia ISO-3166 codes
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
            try:
                rec['authority'] = _strip_wiki_ref(''.join(L[2].itertext()).strip())
            except AttributeError:
                pass
        if len(L) > 3:
            try:
                rec['notes']     = _strip_wiki_ref(explore_text(L[3]).text.strip())
            except AttributeError:
                pass
    else:
        full                = True
        rec['mcc']          = explore_text(L[0]).text.strip().upper()
        rec['country_name'] = ''.join(L[1].itertext()).strip()
        rec['code_alpha_2'] = explore_text(L[2]).text.strip()
        if '\n' in rec['country_name']:
            rec['country_name'] = rec['country_name'].split('\n')[1].strip()
        if len(L) > 4:
            try:
                rec['authority'] = _strip_wiki_ref(''.join(L[4].itertext()).strip())
            except AttributeError:
                pass
        if len(L) > 5:
            try:
                rec['notes']     = _strip_wiki_ref(explore_text(L[5]).text.strip())
            except AttributeError:
                pass
    return rec, full


def parse_table_mcc():
    # warning: for some MCC, there are duplicated entries (mostly for islands...)
    T     = import_wikipedia_table(URL_MCC)
    L     = []
    T_MCC = T[1][0]
    cc2   = set()
    mcc   = set()
    for i in range(1, len(T_MCC)):
        try:
            rec, full = read_entry_mcc(T_MCC, i)
        except IndexError:
            #print('no entry at rank %i, after %s' % (i, d['mcc']))
            pass
        else:
            if not full:
                rec['country_name'] = L[-1]['country_name']
                rec['code_alpha_2'] = L[-1]['code_alpha_2']
                if L[-1]['authority']:
                    rec['authority'] = L[-1]['authority']
                if L[-1]['notes']:
                    rec['notes']     = L[-1]['notes']
            cc2.add(rec['code_alpha_2'])
            if rec['mcc'] in mcc:
                print('> duplicate entry for MCC %s' % rec['mcc'])
            else:
                mcc.add(rec['mcc'])
            L.append(rec)
    print('[+] parsed %i MCC entries (%i unique MCC) for %i ISO-3166 country codes'\
          % (len(L), len(mcc), len(cc2)))
    return L



def read_entry_mnc_title(e):
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
    mccmnc  = set()
    for i in range(1, len(T_MNC)):
        try:
            rec = read_entry_mnc(T_MNC, i)
        except IndexError:
            print('no entry at rank %i, after %s.%s' % (i, d['mcc'], d['mnc']))
            pass
        else:
            if rec['mcc'].isdigit() and len(rec['mcc']) == 3 \
            and rec['mnc'].isdigit() and len(rec['mnc']) in (2, 3):
                mcc.add(rec['mcc'])
                if rec['mcc'] + rec['mnc'] in mccmnc:
                    print('> duplicate entry for MCC %s MNC %s' % (rec['mcc'], rec['mnc']))
                else:
                    mccmnc.add( rec['mcc'] + rec['mnc'] )
                L.append(rec)
            #else:
            #    print('invalid MCC %s MNC %s: %r' % (rec['mcc'], rec['mnc'], rec))
    print('[+] parsed %i MNC mobile country codes for MCC %s' % (len(L), ', '.join(sorted(mcc))))
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
    # 3) MNC for South America
    T_MNC_SA = import_wikipedia_table(URL_MNC_SA)
    for i in range(0, len(T_MNC_SA)):
        mccmnc.update( _insert_mnc(D, parse_table_mnc(T_MNC_SA[i][0])) )
    #
    print('[+] %i MCC MNC entries for %i unique MCC MNC'\
          % (sum(map(len, D.values())), len(mccmnc)))
    return D


#------------------------------------------------------------------------------#
# Main
#------------------------------------------------------------------------------#


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
    parser = argparse.ArgumentParser(description='dump Wikipedia ISO-3166 country codes, MCC and MNC tables into JSON or Python file')
    parser.add_argument('-j', action='store_true', help='produce JSON files (with suffix .json)')
    parser.add_argument('-p', action='store_true', help='produce Python files (with suffix .py)')
    args = parser.parse_args()
    try:
        D_iso = parse_table_iso3166()
        L_mcc = parse_table_mcc()
        D_mnc = parse_table_mnc_all()
    except Exception as err:
        print('unable to download and / or parse Wikipedia HTML table ; exception: %s' % err)
        return 1
    if args.j:
        generate_json(D_iso, 'iso3166.json')
        generate_json(L_mcc, 'mcc.json')
        generate_json(D_mnc, 'mnc.json')
    if args.p:
        generate_python(D_iso, 'iso3166.py')
        generate_python(L_mcc, 'mcc.py')
        generate_python(D_mnc, 'mnc.py')
    return 0


if __name__ == '__main__':
    sys.exit(main())
