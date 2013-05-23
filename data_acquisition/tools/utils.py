import json
import requests


class KorboValue(object):
    def __init__(self, a_dict):
        self.value = a_dict['rdftype'][0]
        self.labels = {'en': a_dict['label']}
        try:
            self.labels.update({
                lang.strip(): lab.strip() 
                for lang, lab in (
                    x.split(":", 1) 
                    for x in a_dict['description'].strip().split('\n')
                    if x
                )
            })
        except:
            raise Exception("Unable to parse description: " + a_dict['description'])

    def __eq__(self, obj):
        return str(obj) == self.value

    def __str__(self):
        return self.value


class KorboDataset(object):
    _values = None

    def __init__(self, proj, host='http://korbo.netseven.it/'):
        self.url = host + proj

    def values(self):
        if self._values is None:
            result = requests.get(self.url)
            res_obj = json.loads(result.content)
            self._values = [KorboValue(x) for x in res_obj['result']['items']]

        return self._values
