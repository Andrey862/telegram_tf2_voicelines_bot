import os
import pickle

from dotenv import load_dotenv

load_dotenv()

#raw_data_location = 'data/tf_audio_raw.pickle'
index_location = 'data/index.pickle'
audio_ids_location = 'data/audio_ids.pickle'
conf_location = 'data/scrapping.json'


def get_index():
    try:
        with open(index_location, 'rb') as f:
            return pickle.load(f)
    except IOError:
        return None


def get_audio_ids():
    try:
        with open(audio_ids_location, 'rb') as f:
            return pickle.load(f)
    except IOError:
        return None


def save_index(index):
    with open(index_location, 'wb') as f:
        pickle.dump(index, f)


def save_audio_ids(audio_ids):
    with open(audio_ids_location, 'wb') as f:
        pickle.dump(audio_ids, f)


def get_scrap_conf():
    try:
        with open(conf_location, 'r') as f:
            return f.read()
    except IOError:
        return None


def save_scrap_conf(conf):
    with open(conf_location, 'w') as f:
        f.write(conf)
