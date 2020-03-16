# MCC_MNC

Scrap available information on the Internet related to:
- Mobile Network Operators (such as MCC, MNC, brand, network type, countries of operation...)
- countries (such as country name, 2 and 3-chars ISO codes, sovereignity, tld...)
- international dialplan (such as msisdn prefix and associated countries)
And generate JSON and Python dictionnaries from them.


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
- Other websites:
  - https://github.com/google/libphonenumber/tree/master/resources/geocoding/en
  - https://phonenum.info/en/country-code/


### For geographical countries and borders
- Wikipedia:
  - https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_land_borders
- Other websites:
  - http://www.naturalearthdata.com/downloads/10m-cultural-vectors/ (open US-based initiative, see admin 0 data)
  - https://github.com/nvkelso/natural-earth-vector (vectorized data from naturalearthdata)
  - https://www.cia.gov/library/publications/the-world-factbook/appendix/appendix-d.html (CIA open data)
  - https://developers.google.com/maps/documentation/javascript/geocoding (Google maps API)

The CIA World Factbook is more complete than Wikipedia when coming to geography and borders referencement.
 

### Which one to use

After checking several sources, it seems Wikipedia has the must complete, up-to-date and accurate information.
Therefore, the tool primarily uses it to build the JSON / Python dictionnaries.


## Install and usage

The following requirements must be fullfil for the script to work: Python3 and lxml are required.
No installation of the script is required, just run it as is.

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

