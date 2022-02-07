# ITU-T bulletins
Parses incremental changes to:

## ISPC
grep -Ei "^[[::blank:]]{0,}ISPC[[:blank:]]{1,}DEC[[:blank:]]{1,}Unique name of the signalling point[[:blank:]]{1,}Name of the signalling point operator[[:blank:]]{0,}$" itut/*.txt

## MCC MNC
grep -Ei "^[[:blank:]]{0,}Country\/Geographical area[[:blank:]]{1,}MCC\+MNC( {1,}\*){0,1}[[:blank:]]{1,}Operator\/Network[[:blank:]]{0,}$" itut/*.txt


