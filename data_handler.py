from functools import cache
from string import ascii_lowercase
import pickle
import os
from collections import Counter
from random import random, sample, shuffle
raw_data = None
index = None
audio_ids = None

with open('tf_audio_raw.pickle', 'rb') as f:
    raw_data = pickle.load(f)

if os.path.exists('index.pickle'):
    with open('index.pickle', 'rb') as f:
        index = pickle.load(f)

if os.path.exists('audio_ids.pickle'):
    with open('audio_ids.pickle', 'rb') as f:
        audio_ids = pickle.load(f)

def preprocess(text: str) -> dict:
    text = text.lower()
    text = '^' + text  + '$'
    res = {}
    res['l'] = max(len(text)-2, 1) + 10
    res['tri'] = dict(Counter([text[i:i+3] for i in range(len(text)-3)]))
    res['two'] = dict(Counter([text[i:i+2] for i in range(len(text)-2)]))
    return res

def compare(query: str, item: dict) -> float:
    query = preprocess(query)
    res = 0
    res += 2*sum(min(query['tri'][e], item['tri'][e]) for e in query['tri'].keys() & item['tri'].keys())
    res += sum(min(query['two'][e], item['two'][e]) for e in query['two'].keys() & item['two'].keys())
    res /= item['l']
    return res

def Nmaxelements(list1, N, key = lambda x:x):
    final_list = []
    for _ in range(0, N): 
        max1 = key(list1[0])
        max_key = list1[0]
          
        for j in range(len(list1)): 
            k = key(list1[j])   
            if k > max1:
                max1 = k
                max_key = list1[j]
                  
        list1.remove(max_key)
        final_list.append(max_key)
          
    return final_list


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
    res = Nmaxelements(res, 20, key=lambda e: compare(query_line, e['text']))
    return [e['file_id'] for e in res]


def save_ids(new_data):
    global audio_ids
    audio_ids = new_data
    with open('audio_ids.pickle', 'wb') as f:
        pickle.dump(audio_ids, f)
    generate_index(audio_ids)


def generate_index(audio_ids):
    global index
    index = {}
    for tf2class in audio_ids:
        index[tf2class] = []
        for e in audio_ids[tf2class]:
            index[tf2class].append({'text': preprocess(e['text']), 'file_id': e['file_id']})
    with open('index.pickle', 'wb') as f:
        pickle.dump(index, f)