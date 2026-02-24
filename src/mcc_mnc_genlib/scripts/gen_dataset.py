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
# * File Name : gen_dataset.py
# * Created : 2020-09-14
# * Authors : Benoit Michau 
# *--------------------------------------------------------
# */


__all__ = [
    'MNC',      # dict of MNC: operator infos
    'MCC',      # dict of MCC: operators infos
    'MSISDN',   # dict of MSISDN prefix: list of countries
    'MSISDNEXT', # dict of MSISDN prefix: list of countries and extra-territories
    'CC2',      # dict of CC2: country info
    'CNTR',     # dict of country: country info (values identical to CC2 dict, but different key)
    'TERR',     # dict of territory (incl. country): neighbour info
    ]


from os.path import dirname, realpath, join
import sys
import re

from mcc_mnc_genlib.core.patch_dataset import *
from mcc_mnc_genlib.scripts.parse_wikipedia_tables import generate_json, generate_python


SCRIPT_DIR = dirname(realpath(__file__))
MODULE_DIR = dirname(realpath(SCRIPT_DIR))
SRC_DIR = dirname(realpath(MODULE_DIR))
PATH_PRE = join(SRC_DIR, 'mcc_mnc_lut', '')

#------------------------------------------------------------------------------#
# utility functions
#------------------------------------------------------------------------------#

def name_norm(name):
    return re.sub(r'\s{1,}', ' ', name).strip()


def name_match(n1, n2):
    if name_norm(n1.lower()) != name_norm(n2.lower()):
        return False
    else:
        return True


#------------------------------------------------------------------------------#
# MNO dict
#------------------------------------------------------------------------------#

_BAND_ORDER     = ['MVNO', 'GSM', 'CDMA', 'UMTS', 'LTE', 'TD-LTE', '5G']
_ITUT_CC2_ALIAS = ['UK', 'TW']


def sort_bands(bands):
    r = []
    for pat in _BAND_ORDER:
        for b in bands[:]:
            if b.upper().startswith(pat):
                r.append(b.upper())
                bands.remove(b)
    r.extend(bands)
    return r


def mnc_merge(mnco, mncn):
    """checks the status of each network to decide whether to merge them or not
    """
    if isinstance(mnco, list):
        stat = mnco[0]['ope']
        if stat:
            if not mncn['ope']:
                return mnco
            else:
                mnco.append(mncn)
                return mnco
        else:
            if not mncn['ope']:
                mnco.append(mncn)
                return mnco
            else:
                return mncn
    elif isinstance(mnco, dict):
        if mnco['ope']:
            if not mncn['ope']:
                return mnco
            else:
                return [mnco, mncn]
        else:
            if not mncn['ope']:
                return [mnco, mncn]
            else:
                return mncn
    else:
        assert()


def gen_dict_mnc():
    """generates a dict of {MCC-MNC: MNO infos}
    MNO infos is a dict, or a list of dict in case several MNOs use the same MCC-MNC
    
    MNO info dict keys:
    - ope      : bool, operational or not
    - bands    : list of str
    - brand    : str
    - operator : str
    - country  : str
    - cc2s     : list of CC2
    - notes    : str
    """
    print('[+] generate MNC dict')
    R = {}
    #
    # 1) flatten the lists of MNC
    MNC = []
    [MNC.extend(mnc_list) for mnc_list in WIKIP_MNC.values()]
    #
    for r in MNC:
        mno     = {}
        mccmnc  = r['mcc'] + r['mnc']
        mno['ope']      = True if r['status'] == 'operational' else False
        mno['bands']    = sort_bands(list(map(str.strip, r['bands'].split('/'))))
        mno['brand']    = name_norm(r['brand'])
        mno['operator'] = name_norm(r['operator'])
        mno['country']  = name_norm(r['country_name'])
        mno['cc2s']     = list(sorted(r['codes_alpha_2']))
        mno['src']      = 'Wikipedia'
        #
        if mccmnc in R:
            # duplicate entry
            print('> merging MNOs with same MCC-MNC %s' % mccmnc)
            R[mccmnc] = mnc_merge(R[mccmnc], mno)
        else:
            R[mccmnc] = mno
    #
    return R

MNC = gen_dict_mnc()


def mnc_txtn(mccmnc, inf):
    mno = {
        'country'   : inf[0],
        'bands'     : '',       # no info on bands
        'ope'       : False,    # consider the MNO as operational (?)
        'src'       : 'txtNation',
        }
    #
    # add set of CC2
    mcc  = mccmnc[:3]
    cc2s = set()
    for r in WIKIP_MCC:
        if r['mcc'] == mcc:
            cc2s.add(r['code_alpha_2'])
    if not cc2s:
        print('> no country info found for %s, %s' % (mccmnc, inf[0]))
    mno['cc2s'] = list(sorted(cc2s))
    #
    # handle operator / brand info
    for mccmnc_ex, mno_ex in MNC.items():
        if mccmnc_ex[:3] != mccmnc[:3]:
            continue
        #
        if isinstance(mno_ex, list):
            # this is dirty
            mno_ex = mno_ex[0]
        if mno_ex['brand'].lower() == inf[1].lower():
            mno['brand']    = mno_ex['brand']
            mno['operator'] = mno_ex['operator']
            break
        elif mno_ex['operator'].lower() == inf[1].lower():
            mno['brand']    = mno_ex['brand']
            mno['operator'] = mno_ex['operator']
            break
    if 'brand' not in mno:
        #print('> no existing brand / operator found for %s (%s), %s' % (mccmnc, inf[1], inf[0]))
        mno['brand']    = inf[1]
        mno['operator'] = ''
    #
    return mno


def mnc_itut(cntr, mno, mccmnc):
    # get the CC2 code for the country
    found = False
    for cc2, cinf in WIKIP_ISO3166.items():
        if cc2 in _ITUT_CC2_ALIAS:
            # do not consider CC2 alias
            continue
        if cntr.lower() in cinf['nameset']:
            found = True
            break
    if found:
        cc2s = [cc2]
    else:
        print('> MNO from ITU-T bulletin with MCC-MNC %s (%s), no CC2 found' % (mccmnc, cntr))
        cc2s = []
    #
    return {
        'country'   : cntr,
        'bands'     : '',       # no info on bands
        'ope'       : False,    # consider the MNO as operational (?)
        'cc2s'      : cc2s,
        'operator'  : mno,
        'brand'     : '',
        'src'       : 'ITU-T',
        }


def gen_dict_mnc_compl():
    #
    R = {}
    #
    # 1) complete MNC dict with new MNC from ITU-T 1162 bulletin (2018)
    # and incremental updates from 1162 to the last one downloaded
    for cntr, inf in sorted(ITUT_MNC_1162.items()):
        for mno, mccmnc in inf:
            if mccmnc not in MNC:
                print('> adding MNO from ITU-T bulletin with MCC-MNC %s (%s)' % (mccmnc, cntr))
                R[mccmnc] = mnc_itut(cntr, mno, mccmnc)
            else:
                # get the CC2 code for the country
                found = False
                for cc2, cinf in WIKIP_ISO3166.items():
                    if cc2 in _ITUT_CC2_ALIAS:
                        # do not consider CC2 alias
                        continue
                    if cntr.lower() in cinf['nameset']:
                        found = True
                        break
                if found:
                    if isinstance(MNC[mccmnc], list):
                        # TODO
                        pass
                    else:
                        if cc2 not in MNC[mccmnc]['cc2s']:
                            print('> adding cc2 %s (%s) from ITU-T bulletin to MCC-MNC %s' % (cc2, cntr, mccmnc))
                            MNC[mccmnc]['cc2s'].append(cc2)
                            MNC[mccmnc]['cc2s'] = list(sorted(MNC[mccmnc]['cc2s']))
    #
    # 2) complete MNC dict with new MNC from txtNation
    for mccmnc, inf in sorted(CSV_TXTN_MCCMNC.items()):
        if mccmnc not in MNC and mccmnc not in R:
            if isinstance(inf, list):
                infs = inf
                mno  = []
                for inf in infs:
                    mno.append( mnc_txtn(mccmnc, inf) )
            else:
                mno = mnc_txtn(mccmnc, inf)
            #
            print('> adding MNO from txtNation with MCC-MNC %s' % mccmnc)
            R[mccmnc] = mno
    #
    return R

MNC.update( gen_dict_mnc_compl() )


#------------------------------------------------------------------------------#
# MCC dict
#------------------------------------------------------------------------------#

def gen_dict_mcc():
    """generates a dict of {MCC: MCC infos}
    MCC infos is a dict, or a list of dict in case several declaration exists for
    the same MCC
    
    MCC infos dict keys:
    - cc2   : CC2 or None
    - url   : str, wikipedia URL to MCC infos
    - reg   : str, regulator
    - mncs  : list of 5/6 digit-str
    - notes : str
    """
    print('[+] generate MCC dict')
    R = {}
    #
    for r in WIKIP_MCC:
        mcc = r['mcc']
        assert(len(mcc) == 3 and mcc.isdigit())
        inf = {
            'cc2'   : r['code_alpha_2'],
            'url'   : r['mcc_url'],
            'reg'   : name_norm(r['authority']),
            'notes' : name_norm(r['notes']),
            'mncs'  : set()
            }
        for mccmnc, mno in MNC.items():
            if mccmnc[:3] == r['mcc']:
                if isinstance(mno, list):
                    for mno_s in mno:
                        if inf['cc2'] in mno_s['cc2s']:
                            inf['mncs'].add(mccmnc)
                else:
                    if inf['cc2'] in mno['cc2s']:
                        inf['mncs'].add(mccmnc)
        inf['mncs'] = list(sorted(inf['mncs']))
        #
        if mcc in R:
            if isinstance(R[mcc], list):
                R[mcc].append(inf)
            elif isinstance(R[mcc], dict):
                R[mcc] = [R[mcc], inf]
            else:
                assert()
        else:
            R[mcc] = inf
    #
    # add also MCC corresponding to non-listed MCC-MNC from MNC dict
    mccset = {mccmnc[:3] for mccmnc in MNC}
    for mcc in R:
        try:
            mccset.remove(mcc)
        except KeyError:
            pass
    #print(mccset)
    for mcc in sorted(mccset):
        R[mcc] = {
            'cc2'   : None,
            'url'   : '',
            'reg'   : '',
            'notes' : '',
            'mncs'  : [],
            }
        if mcc == '001':
            R[mcc]['notes'] = 'test networks'
        #elif mcc[0] == '999':
        #    R[mcc]['notes'] = 'handset special networks'
        elif mcc[0] == '9':
            R[mcc]['notes'] = 'international networks'
        else:
            print('> missing MCC %s' % mcc)
        #
        for mccmnc in MNC:
            if mccmnc[:3] == mcc:
                assert( len(MNC[mccmnc]['cc2s']) == 0 )
                R[mcc]['mncs'].append(mccmnc)
                R[mcc]['mncs'].sort()
    #
    return R
    
MCC = gen_dict_mcc()


#------------------------------------------------------------------------------#
# MSISDN dict
#------------------------------------------------------------------------------#

def gen_dict_msisdn():
    """generates two dict of {msisdn prefix: list of countries}
    
    The 2nd one includes extra-territories compared to the 1st one
    """
    print('[+] generate MSISDN dict')
    R, Rext = {}, {}
    #
    for pref, listinf in WIKIP_MSISDN.items():
        if pref not in R:
            R[pref] = set()
        for cc2, name, url, urlpref in listinf:
            R[pref].add(name)
    #
    for name, listpref in WIKIP_COUNTRY.items():
        for pref in listpref:
            if pref not in R:
                R[pref] = set()
            R[pref].add(name)
    #
    # copy R into Rext
    Rext = {pref: set(names) for pref, names in R.items()}
    #
    for name, (pref, country, url) in WIKIP_TERRITORY.items():
        if pref not in Rext:
            print('> unknown prefix +%s for %s, %s' % (pref, name, country))
            Rext[pref] = set()
        elif country not in Rext[pref]:
            print('> special territory prefix +%s for %s, %s' % (pref, name, country))
        # do not append the country, but only the territory name
        Rext[pref].add(name)
    #
    for pref, countries in list(R.items()):
        R[pref] = list(sorted(countries))
    for pref, countries in list(Rext.items()):
        Rext[pref] = list(sorted(countries))
    #
    return R, Rext

MSISDN, MSISDNEXT = gen_dict_msisdn()


#------------------------------------------------------------------------------#
# SANC dict
#------------------------------------------------------------------------------#

# no transform is required for the SANC dict

SANC = ITUT_SANC_1125


#------------------------------------------------------------------------------#
# SPC dict
#------------------------------------------------------------------------------#

def gen_dict_ispc():
    """generates a dict of Internation Signaling Point Codes {SPC_383-num: SPC_infos}
    """
    print('[+] generate ISPC dict')
    R_383, R_dec = {}, {}
    #
    for cntr, spcs in sorted(ITUT_SPC_1199.items()):
        for spc_info in spcs:
            if spc_info[0] in R_383:
                print('> duplicated ISPC: %s' % spc_info[0])
            else:
                R_383[spc_info[0]] = [cntr, spc_info[3], spc_info[2], spc_info[1]]
    return R_383
    #
    # no need for an additional dict with PC in integer format as key
    #        if spc[1] in R_dec:
    #            print('> duplicated ISPC: %s' % spc[1])
    #        else:
    #            R_dec[spc[1]] = [cntr, spc[3], spc[2], spc[0]]
    #return R_383, R_dec

ISPC = gen_dict_ispc()


#------------------------------------------------------------------------------#
# CC2 dict
#------------------------------------------------------------------------------#

def gen_dict_cc2():
    """generates a dict of {cc2: country infos}
    
    mandatory country infos:
        - name   : str, country name
        - url    : str, wikipedia url
        - mccmnc : list of 5/6-digit-str
        - msisdn : list of digit-str
        - infos  : dict with various country-related informations
    """
    print('[+] generate CC2 dict')
    R = {}
    #
    for cc2, infos in sorted(WIKIP_ISO3166.items()):
        D = {
            'cc2'       : cc2,
            'name'      : infos['country_name'],
            'url'       : infos['country_url'],
            'mcc'       : set(),
            'mccmnc'    : set(),
            'msisdn'    : [],
            'msisdn_url': [],
            }
        #
        # 1) populate mccmnc
        mccset = set()
        for mcc, mccinf in MCC.items():
            if isinstance(mccinf, list):
                for mccinf_s in mccinf:
                    if mccinf_s['cc2'] == cc2:
                        mccset.add(mcc)
            else:
                if mccinf['cc2'] == cc2:
                    mccset.add(mcc)
        D['mcc'] = list(sorted(mccset))
        #
        for mccmnc, mno in MNC.items():
            if isinstance(mno, list):
                for mno_s in mno:
                    if cc2 in mno_s['cc2s']:
                        D['mccmnc'].add(mccmnc)
                        if mccmnc[:3] in mccset:
                            mccset.remove(mccmnc[:3])
            else:
                if cc2 in mno['cc2s']:
                    D['mccmnc'].add(mccmnc)
                    if mccmnc[:3] in mccset:
                        mccset.remove(mccmnc[:3])
        #
        if mccset:
            print('> CC2 %s, country %s, MCC %s unused' % (cc2, D['name'], ', '.join(mccset)))
        #
        D['mcc']    = list(sorted(D['mcc']))
        D['mccmnc'] = list(sorted(D['mccmnc']))
        #
        # 2) additional infos from Wikipedia
        # - nameset
        # - codes: cc3, ccn, gec, stan
        # - geo: coord, region, capital, coastline, boundaries, population, ports, airports, regurl,
        # - tel: telephone, subs_*, users_internet, tld, tldurl, 
        codes, geo, tel, subs, nameset = {}, {}, {}, {}, set(infos['nameset'])
        if infos['cc_tld']:
            tel['tld']          = infos['cc_tld']
        if infos['cc_tld_url']:
            tel['url_tld']      = infos['cc_tld_url']
        if infos['code_alpha_3']:
            codes['cc3']        = infos['code_alpha_3']
        if infos['code_num']:
            codes['ccn']        = infos['code_num']
        if infos['regions_url']:
            geo['url_region']   = infos['regions_url']
        #
        # 3) additional infos from the World Factbook
        if D['name'] in WORLD_FB:
            wfb = WORLD_FB[D['name']]
            if wfb['genc']:
                codes['genc'] = wfb['genc']
            if wfb['stan']:
                codes['stan'] = wfb['stan']
            if wfb['cmt']:
                geo['cmt'] = name_norm(wfb['cmt'])
            if 'infos' in wfb and wfb['infos']:
                geo['url_wfb'] = wfb['url']
                if 'country_name' in wfb['infos']:
                    for v in wfb['infos']['country_name'].values():
                        nameset.update( country_name_canon(v) ) 
                #
                wfbinf = wfb['infos']
                # more info from WFB
                if 'airports' in wfbinf and wfbinf['airports']:
                    geo['airports'] = wfbinf['airports']
                if 'boundaries' in wfbinf and wfbinf['boundaries']:
                    geo['bound']    = wfbinf['boundaries']
                if 'capital' in wfbinf and wfbinf['capital']:
                    geo['capital']  = wfbinf['capital']
                if 'coastline' in wfbinf and wfbinf['coastline']:
                    geo['coast']    = wfbinf['coastline']
                if 'coord' in wfbinf and wfbinf['coord']:
                    geo['coord']    = wfbinf['coord']
                if 'population' in wfbinf and wfbinf['population']:
                    geo['popul']    = wfbinf['population']
                if 'ports' in wfbinf and wfbinf['ports']:
                    geo['ports']    = wfbinf['ports']
                if 'region' in wfbinf and wfbinf['region']:
                    if len(wfbinf['region']) > 1:
                        geo['region'] = wfbinf['region'][0][1]
                    else:
                        geo['region'] = wfbinf['region'][0]
                if 'subs_broadband' in wfbinf and wfbinf['subs_broadband']:
                    subs['bb']      = wfbinf['subs_broadband']
                if 'subs_fixed' in wfbinf and wfbinf['subs_fixed']:
                    subs['fix']     = wfbinf['subs_fixed']
                if 'subs_mobile' in wfbinf and wfbinf['subs_mobile']:
                    subs['mob']     = wfbinf['subs_mobile']
                if 'users_internet' in wfbinf and wfbinf['users_internet']:
                    subs['internet'] = wfbinf['users_internet']
                if subs:
                    tel['subs'] = subs
                if 'telecom' in wfbinf and wfbinf['telecom']:
                    tel.update(wfbinf['telecom'])     
        #
        if 'none' in nameset:
            nameset.remove('none')
        if '' in nameset:
            nameset.remove('')
        D['infos'] = {
            'nameset' : list(sorted(nameset)),
            'codes'   : codes,
            'geo'     : geo,
            'tel'     : tel,
            }
        #
        # 4) populate msisdn, use the most precise information available from 
        # WIKIP_MSISDN first
        for pref, listinf in WIKIP_MSISDN.items():
            for w_cc2, cntr, url, urlpref in listinf:
                if w_cc2 == cc2 and pref not in D['msisdn']:
                    D['msisdn'].append(pref)
                    if urlpref not in D['msisdn_url']:
                        D['msisdn_url'].append(urlpref)
        if not D['msisdn']:
            # only lookup the extended MSISDN dict if required
            for pref, terrs in MSISDN.items():
                for terr in terrs:
                    if terr == D['name'] or terr in nameset:
                        if pref not in D['msisdn']:
                            D['msisdn'].append(pref)
        if not D['msisdn'] and cc2 not in CC2_ALIAS:
            print('> MSISDN prefix: prefix not found for %s, %s' % (cc2, D['name']))
        #
        R[cc2] = D
    #
    for k, v in CC2_ALIAS.items():
        R[k] = R[v]
    #
    return R

CC2 = gen_dict_cc2()


# CC2-like dict, but with country name as key
# take care to exclude CC2 aliases
CNTR = {inf['name']: inf for inf in CC2.values() if inf['cc2'] not in CC2_ALIAS and inf['cc2'] not in CC2_INTL} 


#------------------------------------------------------------------------------#
# Territory dict
#------------------------------------------------------------------------------#

def gen_dict_terr():
    """generates a dict of {territory name: territory infos}
    
    territory infos:
    - cc2: CC2 or None
    - dependency (sovereignity or geographical dependency): CC2 or None
    - neighbours:
        - borders
        - less than 30 km
        - less than 100 km
    - msisdn prefix
    """
    print('[+] generate TERR dict')
    R = {}
    #
    # CSV_EGAL_MIN_DIST, COUNTRY_SPEC
    #
    # 1) initialize R and set sovereignity
    for name, inf in CNTR.items():
        R[name] = {'cc2': inf['cc2']}
    #
    # dependency / sovereignity
    for name, inf in COUNTRY_SPEC.items():
        if name not in R:
            # territory without CC2
            assert( 'cc2' not in inf )
            R[name] = {'cc2': None}
        if 'sub' in inf:
            for sub in inf['sub']:
                if sub not in R:
                    R[sub] = {'cc2': None}
                if 'cc2' in inf:
                    R[sub]['dep'] = inf['cc2']
    for name, inf in COUNTRY_SPEC.items():
        if 'dep' in inf and 'dep' not in R[name]:
            R[name]['dep'] = inf['dep']
    #
    # 2) add borders and neighbours
    WBORD = wikip_borders_todict(WIKIP_BORDERS)
    #
    for name, inf in sorted(R.items()):
        bord, less30, less100 = set(), set(), set()
        #
        # 2.1) WIKIP_BORDERS
        if name in WBORD and WBORD[name]['neigh']:
            bord.update([b for b in WBORD[name]['neigh']])
        # do a reverse search within all neighbours
        for rname, rinf in WBORD.items():
            if name in rinf['neigh']:
                bord.add(rname)
        #
        # 2.2) WORLD_FB
        try:
            wfbb = set(CNTR[name]['infos']['geo']['bound']['bord'])
        except KeyError:
            pass
        else:
            bnew = wfbb.difference(bord)
            if bnew:
                bord.update(bnew)
                print('> %s, wfb has additional borders: %s' % (name, ', '.join(sorted(bnew))))
        #
        # 2.3) COUNTRY_SPEC
        for n, i in COUNTRY_SPEC.items():
            if n == name and 'bord' in i:
                csb = set(i['bord'])
                bnew = csb.difference(bord)
                if bnew:
                    bord.update(bnew)
                    print('> %s, cs has additional borders: %s' % (name, ', '.join(sorted(bnew))))
                break
        #
        # 2.4) CSV_EGAL_MIN_DIST
        if name in CSV_EGAL_MIN_DIST:
            mdist = CSV_EGAL_MIN_DIST[name]
            mdb = set()
            for n, dist in mdist.items():
                if dist == 0.0:
                    mdb.add(n)
                elif dist <= 30.0:
                    less30.add(n)
                elif dist <= 100.0:
                    less100.add(n)
            #
            bnew = mdb.difference(bord)
            if bnew:
                bord.update(bnew)
                print('> %s, emd has additional borders: %s' % (name, ', '.join(sorted(bnew))))
        #
        less30.difference_update(bord)
        less100.difference_update(less30)
        less100.difference_update(bord)
        #
        inf['neigh'] = {
            'bord'    : list(sorted(bord)),
            'less30'  : list(sorted(less30)),
            'less100' : list(sorted(less100))
            }
    #
    return R

TERR = gen_dict_terr()


# go over CC2 / CNTR dict to add potential sovereignity / dependency info in there 
# and complete MCC and MSISDN if empty

def complete_cc2():
    for cc2, inf in CC2.items():
        if inf['name'] in TERR and 'dep' in TERR[inf['name']]:
            inf['dep'] = TERR[inf['name']]['dep']
        else:
            inf['dep'] = None
    #
    for cc2, inf in CC2.items():
        if not inf['mcc'] and inf['dep']:
            # go check sovereign country for MCC
            inf['mcc'].extend(CC2[inf['dep']]['mcc'])
        if not inf['msisdn'] and inf['dep']:
            # go check sovereign country for MCC
            inf['msisdn'].extend(CC2[inf['dep']]['msisdn'])
    
# run it twice (?) as sovereign / dependency relationships can be 2-stages
complete_cc2()
#complete_cc2()


#------------------------------------------------------------------------------#
# main
#------------------------------------------------------------------------------#

def generate_init(path_pre):
    with open(path_pre + '__init__.py', 'w') as fd:
        fd.write('''
            __all__ = ['p1_mnc', 'p1_mcc', 'p1_msisdn', 'p1_msisdnext', 'p1_ispc', 'p1_sanc', 'p1_cc2', 'p1_cntr', 'p1_terr']
            '''.strip())
        fd.write('\n')


def main():
            
    URL_SRC = 'data aggregated from Wikipedia, The World Factbook, ITU-T, Egallic blog and txtNation'
    URL_LIC = 'produced by P1 Security, based on openly available data'

    generate_json(MNC, PATH_PRE + 'p1_mnc.json', [URL_SRC], URL_LIC)
    generate_python(MNC, PATH_PRE + 'p1_mnc.py', [URL_SRC], URL_LIC)
    generate_json(MCC, PATH_PRE + 'p1_mcc.json', [URL_SRC], URL_LIC)
    generate_python(MCC, PATH_PRE + 'p1_mcc.py', [URL_SRC], URL_LIC)
    generate_json(MSISDN, PATH_PRE + 'p1_msisdn.json', [URL_SRC], URL_LIC)
    generate_python(MSISDN, PATH_PRE + 'p1_msisdn.py', [URL_SRC], URL_LIC)
    generate_json(MSISDNEXT, PATH_PRE + 'p1_msisdnext.json', [URL_SRC], URL_LIC)
    generate_python(MSISDNEXT, PATH_PRE + 'p1_msisdnext.py', [URL_SRC], URL_LIC)
    generate_json(ISPC, PATH_PRE + 'p1_ispc.json', [URL_SRC], URL_LIC)
    generate_python(ISPC, PATH_PRE + 'p1_ispc.py', [URL_SRC], URL_LIC)
    generate_json(SANC, PATH_PRE + 'p1_sanc.json', [URL_SRC], URL_LIC)
    generate_python(SANC, PATH_PRE + 'p1_sanc.py', [URL_SRC], URL_LIC)
    generate_json(CC2, PATH_PRE + 'p1_cc2.json', [URL_SRC], URL_LIC)
    generate_python(CC2, PATH_PRE + 'p1_cc2.py', [URL_SRC], URL_LIC)
    generate_json(CNTR, PATH_PRE + 'p1_cntr.json', [URL_SRC], URL_LIC)
    generate_python(CNTR, PATH_PRE + 'p1_cntr.py', [URL_SRC], URL_LIC)
    generate_json(TERR, PATH_PRE + 'p1_terr.json', [URL_SRC], URL_LIC)
    generate_python(TERR, PATH_PRE + 'p1_terr.py', [URL_SRC], URL_LIC)
    
    generate_init(PATH_PRE)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())

