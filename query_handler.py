from file_system_data_handler import save_index
from data_handler import get_audio_ids, get_index, save_audio_ids
from functools import cache
from string import ascii_lowercase
import pickle
import os
import json
from collections import Counter
from random import random, sample, shuffle

index = get_index()
audio_ids = get_audio_ids()


def preprocess(text: str) -> dict:
    # N-gram based search
    text = text.lower()
    #text = '^' + text  + '$'
    res = {}
    res['l'] = max(len(text)-2, 1) + 10
    res['tri'] = dict(Counter([text[i:i+3] for i in range(len(text)-3)]))
    res['two'] = dict(Counter([text[i:i+2] for i in range(len(text)-2)]))
    return res

def similarity(query: dict, item: dict) -> float:
    res = 0
    res += 2*sum(min(query['tri'][e], item['tri'][e]) for e in query['tri'].keys() & item['tri'].keys())
    res += sum(min(query['two'][e], item['two'][e]) for e in query['two'].keys() & item['two'].keys())
    res /= item['l']
    return res

def find(query: str) -> list:
    if (':' not in query): query=':' +query
    query = query.split(':')
    query_tf2class, query_line = (query[0], ':'.join(query[1:]))
    res = []
    for tf2class in index:
        if (query_tf2class.lower() in tf2class.lower()):
            res += index[tf2class]
    shuffle(res)
    query_line_preprocessed = preprocess(query_line)
    res = sorted(res, key=lambda e: -similarity(query_line_preprocessed, e['text']))[:20]
    return [e['file_id'] for e in res]


def save_ids(new_data):
    global audio_ids
    audio_ids = new_data
    save_audio_ids(audio_ids)
    generate_index(audio_ids)


def generate_index(audio_ids):
    global index
    index = {}
    for tf2class in audio_ids:
        index[tf2class] = []
        for e in audio_ids[tf2class]:
            index[tf2class].append({'text': preprocess(e['text']), 'file_id': e['file_id']})
    save_index(index)


if (index is None and audio_ids is not None):
    generate_index(audio_ids)