from nomenklatura import Dataset
from utils import KorboDataset


NOMENKLATURA_URL = 'http://nomenklatura.venturi.fbk.eu/'
NOMENKLATURA_PROJ = 'pois'

KORBO_URL = 'http://korbo.netseven.it/'
KORBO_PROJ = '101'


nk_dataset = Dataset(NOMENKLATURA_PROJ, host=NOMENKLATURA_URL)
ko_dataset = KorboDataset(KORBO_PROJ, host=KORBO_URL)
nk_values = sorted(nk_dataset.values(), key=lambda x: x.value)
ko_values = sorted(ko_dataset.values(), key=lambda x: x.value)

nk_values_set = frozenset(nk_values)
ko_values_set = frozenset(ko_values)
if len(nk_values) != len(nk_values_set):
    print "FOUND DUPLICATES ON NOMENKLATURA: ", nk_values - nk_values_set
if len(ko_values) != len(ko_values_set):
    print "FOUND DUPLICATES ON KORBO: ", nk_values - nk_values_set


cnt = 0
for nk_value in nk_values:
    if nk_value.value not in ko_values:
        cnt += 1
        print nk_value, "NOT FOUND ON KORBO"
print "KORBO PROJ:", cnt, "issues found"

def validate_label(label):
    if not label[0:1].isupper():
        return False
    if not label[1:].islower():
        return False
    return True

cnt = 0
for ko_value in ko_values:
    if ko_value.value not in [x.value for x in nk_values]:
        cnt += 1
        print ko_value, "NOT FOUND ON NOMENKLATURA"
    else:
        for lang in ('en', 'it'):
            if not lang in ko_value.labels:
                cnt += 1
                print ko_value, "SHOULD HAVE", lang, "LABEL"
            elif not validate_label(ko_value.labels[lang]):
                cnt += 1
                print ko_value, "HAS INVALID", lang, "LABEL:", ko_value.labels[lang]
                
print "NOMENKLATURA PROJ:", cnt, "issues found"
