from functools import cache
from string import ascii_lowercase
import pickle
import os
from collections import Counter

raw_data = None
index = None

with open('tf_audio_raw.pickle', 'rb') as f:
    raw_data = pickle.load(f)

if os.path.exists('index.pickle'):
    with open('index.pickle', 'rb') as f:
        index = pickle.load(f)

# @cache
# def get_trigrams():
#     res = []
#     for l1 in ascii_lowercase:
#         for l2 in ascii_lowercase:
#             for l3 in ascii_lowercase:
#                 res.append(l1+l2+l3)
#     return res

def preprocess(text: str) -> dict:
    text = text.lower()
    res = {}
    res['l'] = max(len(text)-2, 1)
    res['tri'] = dict(Counter([text[i:i+2] for i in range(len(text)-2)]))
    res['two'] = dict(Counter([text[i:i+1] for i in range(len(text)-1)]))
    return res

def find(query):
    if (':' not in query): query=':' +query
    query = query.split(':')
    query_tf2class, query_line = (query[0], ':'.join(query[1:]))
    res = []
    for tf2class in index:
        if (query_tf2class.lower() in tf2class.lower()):
            for e in index[tf2class]:
                if (query_line.lower() in e['text'].lower()):
                    res.append(e['file_id'])
                    if (len(res)>10): return res
    return res


def generate_index(new_data):
    global index
    index = new_data
    with open('index.pickle', 'wb') as f:
        pickle.dump(index, f)