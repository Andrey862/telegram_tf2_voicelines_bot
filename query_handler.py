import random
from collections import Counter
from math import sqrt

import vptree
from unidecode import unidecode

from data_handler import get_audio_ids, save_audio_ids

index = None
audio_ids = get_audio_ids()

weight_tri = 2
weight_two = 1


def preprocess(text: str, jitter = 0) -> dict:
    # N-gram based search
    text = unidecode(text).lower()
    #text = '^' + text  + '$'
    text = "'" + text + "'"  # Why not? it works
    res = {}
    res['tri'] = dict(Counter([text[i:i+3] for i in range(len(text)-2)]))
    res['two'] = dict(Counter([text[i:i+2] for i in range(len(text)-1)]))
    #res['l'] = len(res['tri'])*weight_tri + len(res['two'])*weight_two
    res['l'] = sqrt(max(len(text)-2, 1) + 10)
    #res['text'] = text
    
    #add random number to similarity metric
    res['jitter'] = jitter
    return res


def similarity(item_1: dict, item_2: dict) -> float:
    res = 0
    res += weight_tri * sum(min(item_1['tri'][e], item_2['tri'][e])
                            for e in item_1['tri'].keys() & item_2['tri'].keys())

    res += weight_two * sum(min(item_1['two'][e], item_2['two'][e])
                            for e in item_1['two'].keys() & item_2['two'].keys())

    res /= item_2['l']* item_1['l']
    res = res + (item_1['jitter'] + item_2['jitter'])*random.random()
    return res


class NNS():
    # VPtree wrapper

    def __init__(self, data: list) -> None:
        data = [(preprocess(k), v) for k, v in data]
        def distance(a, b): return 1-similarity(a, b)
        # Yes, this is not a metric function. But it works!
        self.tree = vptree.VPTree(data, lambda a, b: distance(a[0], b[0]))

    def get(self, query: str, n: int = None):
        query = preprocess(query, jitter=0.01)
        if (n is None):
            return self.tree.get_nearest_neighbor((query, None))[1][1]
        else:
            #print([e[0] for e in self.tree.get_n_nearest_neighbors((query, None), n)])
            return [e[1][1] for e in self.tree.get_n_nearest_neighbors((query, None), n)]


def find(query: str) -> list:
    if (':' not in query):
        query = ':' + query
    query = query.split(':')
    query_tf2class, query_line = (query[0], ':'.join(query[1:]))

    if (query_tf2class == ''):
        search_tree = index['all']
    else:
        search_tree = index['class'].get(query_tf2class)
    return search_tree.get(query_line, 20)


def save_ids(new_data):
    global audio_ids
    audio_ids = new_data
    save_audio_ids(audio_ids)
    generate_index(audio_ids)


def generate_index(audio_ids):
    global index
    index = {}
    for tf2class in audio_ids:
        index[tf2class] = NNS([(e['text'], e['file_id'])
                              for e in audio_ids[tf2class]])

    all_ = NNS([(e['text'], e['file_id'])
               for tf2class in audio_ids for e in audio_ids[tf2class]])
    index = {'class': NNS(list(index.items())), 'all': all_}


generate_index(audio_ids)
