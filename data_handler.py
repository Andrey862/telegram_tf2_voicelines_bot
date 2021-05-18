from functools import cache
from string import ascii_lowercase
import pickle
import os
from collections import Counter
from random import random, sample, shuffle

raw_data = None
index = None
audio_ids = None

raw_data_location = 'data/tf_audio_raw.pickle'
index_location = 'data/index.pickle'
audio_ids_location = 'data/audio_ids.pickle'

if os.path.exists(raw_data_location):
    with open(raw_data_location, 'rb') as f:
        raw_data = pickle.load(f)

if os.path.exists(index_location):
    with open(index_location, 'rb') as f:
        index = pickle.load(f)

if os.path.exists(audio_ids_location):
    with open(audio_ids_location, 'rb') as f:
        audio_ids = pickle.load(f)

def preprocess(text: str) -> dict:
    text = text.lower()
    text = '^' + text  + '$'
    res = {}
    res['l'] = max(len(text)-2, 1) + 10
    res['tri'] = dict(Counter([text[i:i+3] for i in range(len(text)-3)]))
    res['two'] = dict(Counter([text[i:i+2] for i in range(len(text)-2)]))
    return res

def similarity(query: str, item: dict) -> float:
    query = preprocess(query)
    res = 0
    res += 2*sum(min(query['tri'][e], item['tri'][e]) for e in query['tri'].keys() & item['tri'].keys())
    res += sum(min(query['two'][e], item['two'][e]) for e in query['two'].keys() & item['two'].keys())
    res /= item['l']
    return res

def find(query):
    if (':' not in query): query=':' +query
    query = query.split(':')
    query_tf2class, query_line = (query[0], ':'.join(query[1:]))
    res = []
    for tf2class in index:
        if (query_tf2class.lower() in tf2class.lower()):
            for e in index[tf2class]:
                res.append(e)

    shuffle(res)
    res = sorted(res, key=lambda e: -similarity(query_line, e['text']))[:20]
    return [e['file_id'] for e in res]


def save_ids(new_data):
    global audio_ids
    audio_ids = new_data
    with open(audio_ids_location, 'wb') as f:
        pickle.dump(audio_ids, f)
    generate_index(audio_ids)


def generate_index(audio_ids):
    global index
    index = {}
    for tf2class in audio_ids:
        index[tf2class] = []
        for e in audio_ids[tf2class]:
            index[tf2class].append({'text': preprocess(e['text']), 'file_id': e['file_id']})
    with open(index_location, 'wb') as f:
        pickle.dump(index, f)


if (index is None and audio_ids is not None):
    generate_index(audio_ids)


