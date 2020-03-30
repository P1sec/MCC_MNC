# MCC_MNC

Scrap available information on the Internet related to:
- Mobile Network Operators (such as MCC, MNC, brand, network type, countries of operation...)
- countries (such as country name, 2 and 3-chars ISO codes, sovereignity, tld...)
- international dialplan (such as msisdn prefix and associated countries)


And generate re-engineered JSON and Python dictionnaries from them.


## Data sources

Several sources are available on the Internet:


### For country codes:
- ISO website:
  - https://www.iso.org/obp/ui/#search
  - https://www.iso.org/obp/ui/#iso:pub:PUB500001:en
- Wikipedia:
  - https://en.wikipedia.org/wiki/Mobile_country_code


### For MNO-related information:
- ITU-T documents:
  - List of MCC: https://www.itu.int/pub/T-SP-E.212A
  - List of MNC: https://www.itu.int/pub/T-SP-E.212B
- Wikipedia:
  - List of MCC: https://en.wikipedia.org/wiki/Mobile_country_code
  - List of MNC: international networks listed in the MCC page, and 6 pages linked from there, one per world region
- Other websites:
  - https://www.mcc-mnc.com/ (contains several errors, e.g. related to country codes)
  - https://clients.txtnation.com/hc/en-us/articles/218719768-MCCMNC-mobile-country-code-and-mobile-network-code-list (csv file)
  - https://clients.txtnation.com/hc/en-us/articles/218719468-Operator-Details-Operator-Network-CC-MCC-MNC (xls file)
  - https://cellidfinder.com/mcc-mnc
  - https://docs.routee.net/docs/list-of-mccmnc-codes


### For MSISDN numbering prefixes:
- ITU-T documents:
  - https://www.itu.int/pub/T-SP-E.164D
- Wikipedia:
  - https://en.wikipedia.org/wiki/List_of_country_calling_codes
  - https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country#International_prefixes_table
  - https://en.wikipedia.org/wiki/International_Networks_(country_code) (for international networks)
- Other websites:
  - https://github.com/google/libphonenumber/tree/master/resources/geocoding/en
  - https://phonenum.info/en/country-code/


### For geographical countries and borders:
- Wikipedia:
  - https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_land_borders
- Other websites:
  - http://www.naturalearthdata.com/downloads/10m-cultural-vectors/ (open US-based initiative, see admin 0 data)
  - https://github.com/nvkelso/natural-earth-vector (vectorized data from naturalearthdata)
  - https://www.cia.gov/library/publications/the-world-factbook/appendix/appendix-d.html (CIA open data)
  - https://developers.google.com/maps/documentation/javascript/geocoding (Google maps API)

The CIA World Factbook is more complete than Wikipedia when coming to geography and borders referencement.

Specifically for the minimum distance between countries, here are valuable sources:
- https://egallic.fr/en/closest-distance-between-countries/
  - with updated R code and computed values:
    https://gist.github.com/mtriff/185e15be85b44547ed110e412a1771bf/
- http://nils.weidmann.ws/projects/cshapes.html (CShapes dataset and R package)
- https://zenodo.org/record/46822 for sea-distances only
  - with related information provided here:
    https://halshs.archives-ouvertes.fr/halshs-01288748/document
- https://www.transtats.bts.gov/Distance.asp for distances between airports


### Which one to use:
After checking several sources, it seems Wikipedia has the must complete, up-to-date and accurate information.
Therefore, the tool primarily uses it to build the JSON / Python dictionnaries, it uses also the CIA World Factbook
to gather information related to each country, including borders and telephony-related.
Finally, the code and data provided on the _egallic_ blogpost is valuable for dealing with close countries which
do not share any borders.


## Install and usage

The provided scripts require Python3, and lxml for the ones extracting data from 
web sites (parse_wikipedia_tables.py and parse_worldfactbook_infos.py).
No installation is required, just run the scripts as is.

The Wikipedia and World Factbook data can be imported by using the following commands:

```
$ ./parse_wikipedia_tables.py --help
usage: parse_wikipedia_tables.py [-h] [-j] [-p]

dump Wikipedia ISO-3166 country codes, MCC and MNC tables into JSON or Python
file

optional arguments:
  -h, --help  show this help message and exit
  -j          produce JSON files (with suffix .json)
  -p          produce Python files (with suffix .py)
```

and

```
$ ./parse_worldfactbook_infos.py --help
usage: parse_worldfactbook_infos.py [-h] [-j] [-p]

dump country-related informations from the CIA World Factbook into JSON or
Python file

optional arguments:
  -h, --help  show this help message and exit
  -j          produce JSON files (with suffix .json)
  -p          produce Python files (with suffix .py)

```

Then, in order to load all those imported data with aligned and coherent values 
(e.g. country names, ISO codes and other information and numbering), the module
*patch_dataset* can be used. It exports the Wikipedia, World Factbook and Egallic 
dataset, after applying few corrections and fixes on them:

```
>>> from patch_dataset import *
[...]
>>> WIKIP_ISO3166
[...]
```

Finally, the last script generates new JSON and Python dictionnaries based on 
those re-engineered data:
- MNC: dict of MCCMNC 5/6-digit-str, MNO(s) information
- MCC: dict of MCC 3-digit-str, Operators-related information
- MSISDN: dict of MSISDN prefixes, countries
- MSISDNEXT: dict of MSISDN prefixes, countries and extra-territories
- CC2: dict of alpha-2 code, country-related information
- CNTR: dict of country, country-related information (similar to CC2)
- TERR: dict of country or territory, borders and neighbour related information

```
$ ./gen_dataset.py
[...]
[+] p1_mnc.json file generated
[+] p1_mnc.py file generated
[+] p1_mcc.json file generated
[+] p1_mcc.py file generated
[+] p1_msisdn.json file generated
[+] p1_msisdn.py file generated
[+] p1_msisdnext.json file generated
[+] p1_msisdnext.py file generated
[+] p1_cc2.json file generated
[+] p1_cc2.py file generated
[+] p1_cntr.json file generated
[+] p1_cntr.py file generated
[+] p1_terr.json file generated
[+] p1_terr.py file generated

```

The following one-liner can be used to update the whole dataset:
```
$ ./parse_wikipedia_tables.py -j -p && $ ./parse_worldfactbook_infos.py -j -p && ./gen_dataset.py
```

Now you can use those dictionnaries to get precise information for any MCC, MNC,
MSISDN prefix, and related geographical information !

Finally, 3 little command-line tools are provided to make direct use of the 
extracted and engineered dataset:

```
$ ./chk_mnc.py --help
usage: chk_mnc.py [-h] [-x] [MCCMNC [MCCMNC ...]]

provides information related to mobile operator(s); if no argument is passed,
lists all known MCC-MNC

positional arguments:
  MCCMNC      0 or more 5/6-digit string for MCC-MNC

optional arguments:
  -h, --help  show this help message and exit
  -x          provides extended information for MNO(s)

$ ./chk_msisdn.py --help
usage: chk_msisdn.py [-h] [-x] [MSISDN [MSISDN ...]]

provides information related to international telephone prefix; if no argument
is passed, lists all known MSISDN prefixes

positional arguments:
  MSISDN      0 or more digit string for MSISDN

optional arguments:
  -h, --help  show this help message and exit
  -x          provides extended country-related information

$ ./chk_cntr.py --help
usage: chk_cntr.py [-h] [-x] [COUNTRY [COUNTRY ...]]

provides information related to a given country or territory; if no argument
is passed, lists all known countries and territories

positional arguments:
  COUNTRY     0 or more string for country (can be an alpha-2 code too)

optional arguments:
  -h, --help  show this help message and exit
  -x          provides extended country-related information
```

