# MCC_MNC

Scrap available information on the Internet related to:
- mobile network operators (such as MCC, MNC, brand, network type, countries of operation...)
- countries (such as country name, 2 and 3-chars ISO codes, tld, boundaries and neighbours...)
- international dialplan (such as MSISDN prefix and associated countries, signaling point codes...)

Using public data from the the following websites:
- Wikipedia
- ITU-T
- The CIA World Factbook
- txtNation
- Ewen Gallic blog

All raw content extracted is available in *raw/* as JSON and Python dictionnaries.
This project aggregates and generates re-engineered dictionnaries from all those sources.
All re-engineered content is available in *mcc_mnc_lut/*, as JSON and Python dictionnaries too.

Finally, it provides additionally command-line tools to request those dictionnaries:
- `chk_cntr.py`: to get information related to a country
- `chk_mnc.py`: to get information related to an Mobile Country Code - Mobile Network Code
- `chk_msisdn.py`: to get information related to a phone prefix
- `chk_ispc.py`: to get information related to an international Signaling Point Code
- `conv_pc_383.py`: to convert signaling point code in different formatting


## License

The code from this repository that is used to generate the dataset, and the command-line tools, is licensed under the terms of the AGPLv3.
The data downloaded from Wikipedia is licensed under the terms of the Creative Commons Attribution-ShareAlike license.
The 4 other websites used as source do not indicate any specific licensing for the data provided however, we provide an explicit indication 
of the data sources used in each JSON and Python dictionnary.


## Data sources

Several sources are available on the Internet to learn on the countries' geopraphy, and international mobile and telephony identifiers:


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
  - Operational bulletins: https://www.itu.int/pub/T-SP-OB
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
  - Per-country numbering plan: https://www.itu.int/oth/T0202.aspx?parent=T0202
- Wikipedia:
  - https://en.wikipedia.org/wiki/List_of_country_calling_codes
  - https://en.wikipedia.org/wiki/List_of_mobile_telephone_prefixes_by_country#International_prefixes_table
  - https://en.wikipedia.org/wiki/International_Networks_(country_code) (for international networks)
- Other websites:
  - https://github.com/google/libphonenumber/tree/master/resources/geocoding/en
  - https://phonenum.info/en/country-code/


### For geographical countries and borders:

Mobile networks and other sorts of telephony networks being regulated nationally, it is important for analysts to have
accurate information related to borders and proximity between countries. This helps to evaluate e.g., the feasibility of
certain mobility events for mobile subscribers.

- Wikipedia:
  - https://en.wikipedia.org/wiki/List_of_countries_and_territories_by_land_borders
- Other websites:
  - https://www.cia.gov/the-world-factbook/countries/
  - http://www.naturalearthdata.com/downloads/10m-cultural-vectors/ (open US-based initiative, see admin 0 data)
  - https://github.com/nvkelso/natural-earth-vector (vectorized data from naturalearthdata)
  - https://developers.google.com/maps/documentation/javascript/geocoding (Google maps API)
  - https://pypi.org/project/leafmap/ (Python notebook based project for geography and maps)

The CIA World Factbook looks more complete and less prone to periodic changes than Wikipedia when coming to geography and borders' referencement.

Specifically for the minimum distance between countries, here are valuable sources:
- https://egallic.fr/en/closest-distance-between-countries/
  - with updated R code and computed values:
    https://gist.github.com/mtriff/185e15be85b44547ed110e412a1771bf/
- https://zenodo.org/record/46822 for sea-distances only
  - with related information provided here:
    https://halshs.archives-ouvertes.fr/halshs-01288748/document

Some other sources may be found online; additionally, it seems the R programming language has nice geography-related packages.


## The case of international signaling point codes

ITU-T seems to be the only entity to maintain the list of International Signalling Point Codes.
Point codes are addresses used by each routing equipment at the MTP3 / M3UA layer for fixed telephony and SS7 signalling.
That means ISPC correspond most often to STP used by telecom operators for international routing of SS7 signaling.

The geographical relation between ISCP prefixes (most significant bits), also called Signaling Area Network Codes (SANC),
and countries are provided in the operational bulletin 1125 from 2017.
Additionally, the operational bulletin 1199 from 2020 provides the complete list of those ISPC at the time.
This is however evolving with differences provided from time to time in other operational bulletins.


### Working with ITU-T operational bulletins

ITU-T is publishing bi-mensual bulletins (23 or 24 a year, depends...), containing
all additions and modifications to numbering plans, MNC identifiers and other signaling-related
information. Complete lists of MCC-MNC can be found in bulletin 1111 from 2016 and 
bulletin 1162 from 2018. Moreover, differentials can be provided into individual bulletin.

The script `parse_itut_bulletins.py` can be used to download all bulletins (starting from 1111
or whatever numbering after) and convert them to text using the Linux command ```pdftotext```.
All resulting documents are available in the *itut/* directory.

Bulletins 1111 from 2016 and 1162 from 2018 contain a full list of declared MCC-MNC which is extracted.
Additionally, all MCC-MNC incremental updates from bulletins after the 1162 are also extracted.
Finally, bulletin 1199 contains a full list of declared international signaling point codes which is extracted too.
The script put all resulting JSON and Python files into the *raw/* directory for further integration.


### Which ones to use:

After checking several sources, it seems Wikipedia has the most complete, up-to-date and accurate information.
Therefore, the tool primarily uses it to build the JSON / Python dictionnaries.
Information related to MCC-MNC is completed with the csv listing from the txtNation website 
and the ITU-T operational bulletins 1162 and all following incremental updates.
The list of Signaling Point Codes is extracted from ITU-T bulletin 1199.
Geographical information are taken from the CIA World Factbook to gather information related to each country,
including borders and telephony-related.
This is completed with the data provided on the _egallic_ blogpost for getting countries' proximity in addition to neighbours one.


## Directory structure

All command-line tools are available straight in the root directory of the project.
Data downloaded and extracted from Internet are put in the *raw/* directory, except 
document from the ITU-T which are downloaded as PDF and converted to text in the *itut/*
directory.
Re-engineered look-up tables put in the *mcc_mnc_gen/* directory.


## Install and usage

### Install

The provided scripts all require Python3.
For rebuilding / updating the source dataset (the files in the *raw/* subdirectory),
the following packages are required: `urllib`, `lxml` and `csv`.
For generating the aggregated dataset (the files in the *mcc_mnc_lut/* subdirectory),
no specific packages are required.

If you want, you can run `python setup.py install` to install the *chk\_\*.py* scripts
together with the look-up tables (in the `./mcc_mnc_lut/` subdirectory) in your system or user
environment. The extraction and table generation scripts won't be installed however, 
and you will need to reinstall the package each time you update the tables.

Generally, installation is not required and every scripts can be run as-is.


### Source dataset update

The Wikipedia, World Factbook and ITU-T bulletins source datasets can be updated with the
following scripts:

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
[...]
```

```
$ ./parse_itut_bulletins.py --help
usage: parse_itut_bulletins.py [-h] [-d] [-b B] [-j] [-p]

download ITU-T operational bulletins, convert them to text, extract lists of MNC and SPC

optional arguments:
  -h, --help  show this help message and exit
  -d          download and convert from pdf to text all ITU-T bulletins (requires pdftotext)
  -b B        ITU-T bulletin number to start with, default is 1111
  -j          produce a JSON file listing all MNC and SPC (with suffix .json)
  -p          produce a Python file listing all MNC and SPC (with suffix .py)
```

The script extracting information from Wikipedia tables may fail sometimes, as the layout on
Wikipedia can be modified or adjusted. Nothing magic here, it's then require to patch the `parse_wikipedia_tables.py`
script to make it work again against the new Wikipedia layout.

The Egallic and txtNation data can be processed with the following script (it won't download anything 
from the Internet, as both CSV files are provided directly in the project and do not change anymore):

```
$ ./parse_various_csv.py --help
usage: parse_various_csv.py [-h] [-j] [-p]

dump csv files from the Egallic blog (distance between countries) and the
txtNation website (list of MCC-MNC)
[...]
```


### Aggregated dataset generation

In order to load all those imported data with aligned and coherent values 
(e.g. country names, ISO codes and other information and numbering), the module
*patch_dataset* can be used. It exports the Wikipedia, World Factbook, Egallic, 
txtNation and ITU-T datasets, after applying few corrections and fixes on them:

```
>>> from patch_dataset import *
[...]
>>> WIKIP_ISO3166
[...]
```

The module *gen_dataset.py* then generates new JSON and Python dictionnaries based on 
those re-engineered data and store them in new files prefixed with "p1":
- MNC: dict of MCCMNC 5/6-digit-str, MNO(s) information
- MCC: dict of MCC 3-digit-str, Operators-related information
- MSISDN: dict of MSISDN prefixes, countries
- MSISDNEXT: dict of MSISDN prefixes, countries and extra-territories
- ISPC: dict of international signaling point codes, countries and operators
- CC2: dict of alpha-2 code, country-related information
- CNTR: dict of country, country-related information (similar to CC2)
- TERR: dict of country or territory, borders and neighbour related information

```
$ ./gen_dataset.py
[...]
[+] mcc_mnc_lut/p1_mnc.json file generated
[+] mcc_mnc_lut/p1_mnc.py file generated
[+] mcc_mnc_lut/p1_mcc.json file generated
[+] mcc_mnc_lut/p1_mcc.py file generated
[+] mcc_mnc_lut/p1_msisdn.json file generated
[+] mcc_mnc_lut/p1_msisdn.py file generated
[+] mcc_mnc_lut/p1_msisdnext.json file generated
[+] mcc_mnc_lut/p1_msisdnext.py file generated
[+] mcc_mnc_lut/p1_ispc.json file generated
[+] mcc_mnc_lut/p1_ispc.py file generated
[+] mcc_mnc_lut/p1_sanc.json file generated
[+] mcc_mnc_lut/p1_sanc.py file generated
[+] mcc_mnc_lut/p1_cc2.json file generated
[+] mcc_mnc_lut/p1_cc2.py file generated
[+] mcc_mnc_lut/p1_cntr.json file generated
[+] mcc_mnc_lut/p1_cntr.py file generated
[+] mcc_mnc_lut/p1_terr.json file generated
[+] mcc_mnc_lut/p1_terr.py file generated
```

The following one-liner can be used to update the whole final dataset (without downloading new ITU-T bulletins):
```
$ ./parse_wikipedia_tables.py -j -p && ./parse_worldfactbook_infos.py -j -p && ./parse_various_csv.py -j -p && ./parse_itut_bulletins.py -j -p && ./gen_dataset.py
```

### Usage

Now you can use those dictionnaries to get complete information for any MCC, MNC, MSISDN prefix, 
and related geographical information, directly in your application as much as you want
(do not forget to comply with the licensing).

Finally, 4 little command-line tools are provided to make direct use of the aggregated 
datasets straight from the CLI:

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


$ chk_ispc.py --help
usage: chk_ispc.py [-h] [-x] [ISPC [ISPC ...]]

provides information related to ISPC (International Signaling Point Code); if no 
argument is passed, lists all known ISPC

positional arguments:
  ISPC        0 or more 3-8-3 formatted or integer ISPC values

optional arguments:
  -h, --help  show this help message and exit
  -x          provides extended information for associated country
```

