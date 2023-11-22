# ITU-T bulletins

Parses incremental changes to ISPC tarting from bulletin 1200, and create an incremental change on top of the 1199 extract.
'''
grep -Ei "^[[:blank:]]{0,}ISPC[[:blank:]]{1,}DEC[[:blank:]]{1,}Unique name of the signalling point[[:blank:]]{1,}Name of the signalling point operator[[:blank:]]{0,}$" itut/*.txt
'''


# Additional sources

## Enterprises

Wikipedia lists administrative companies with number of subscribers: https://en.wikipedia.org/wiki/List_of_mobile_network_operators
And revenues: https://en.wikipedia.org/wiki/List_of_telephone_operating_companies
Those 2 generally encompasses several national MNOs.

See if / how the list of national MNO can be linked to companies listed in this table.


## Cables

All submarine cables and landing points: 
https://www.submarinecablemap.com/


