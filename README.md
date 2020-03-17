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

Specifically for the minimum distance between countries, here are valuable sources:
- https://egallic.fr/en/closest-distance-between-countries/
  - with updated R code and computed values:
    https://gist.github.com/mtriff/185e15be85b44547ed110e412a1771bf/
- http://nils.weidmann.ws/projects/cshapes.html (CShapes dataset and R package)
- https://zenodo.org/record/46822 for sea-distances only
  - with related information provided here:
    https://halshs.archives-ouvertes.fr/halshs-01288748/document
- https://www.transtats.bts.gov/Distance.asp for distances between airports


### Which one to use

After checking several sources, it seems Wikipedia has the must complete, up-to-date and accurate information.
Therefore, the tool primarily uses it to build the JSON / Python dictionnaries, it uses also the CIA World Factbook
to gather information related to each country, including borders and telephony-related.
Finally, the code and data provided on the _egallic_ blogpost is valuable for dealing with close countries which
do not share any borders.


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

