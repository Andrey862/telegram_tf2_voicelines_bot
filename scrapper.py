import io
import json
import logging
import multiprocessing as mp
import os
from base64 import b64decode, b64encode
from functools import partial
from multiprocessing.pool import ThreadPool
from time import sleep
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from pydub import AudioSegment

from data_handler import get_scrap_conf, save_scrap_conf

audio_ext = [
    '.3gp',
    '.aa',
    '.aac',
    '.aax',
    '.act',
    '.aiff',
    '.alac',
    '.amr',
    '.ape',
    '.au',
    '.awb',
    '.dss',
    '.dvf',
    '.flac',
    '.gsm',
    '.iklax',
    '.ivs',
    '.m4a',
    '.m4b',
    '.m4p',
    '.mmf',
    '.mp3',
    '.mpc',
    '.msv',
    '.nmf',
    '.ogg',
    '.oga',
    '.mogg',
    '.opus',
    '.org',
    '.ra',
    '.rm',
    '.raw',
    '.rf64',
    '.sln',
    '.tta',
    '.voc',
    '.vox',
    '.wav',
    '.wma',
    '.wv',
    '.webm',
    '.8svx',
    '.cda']


# ------- Loggging-----------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


class Config():
    conf = None
    conf_default_location = 'static/default_scrapping.json'

    @classmethod
    def get(cls):
        if (cls.conf is None):
            logger.debug(
                f'scrap config not found in memory, taking from local storage')
            if (not get_scrap_conf()):
                logger.debug(f'not found locally, creating from default')
                with open(cls.conf_default_location, 'r') as r:
                    save_scrap_conf(r.read())

            cls.conf = json.loads(get_scrap_conf())
        return cls.conf

    @classmethod
    def save(cls, data):
        cls.conf = data
        save_scrap_conf(json.dumps(cls.conf))


def to_mp3(audio):
    return AudioSegment.from_file(io.BytesIO(audio)).export(format='mp3').read()


def get_content(url):
    while True:
        try:
            return requests.get(url).content
        except Exception as error:
            sleep(0.05)
            logger.warning(f'acces to {url} failed, retrying')


def get_encoded_audio(res, base_url):
    def parce(e, base_url):
        logger.debug('start ', e['data'])
        attempts = 0
        while(True):
            try:
                res = {'text': e['text'], 'data': get_content(
                    urljoin(base_url, e['data']))}
                logger.debug('finish', e['data'])
                return res

            except Exception as error:
                attempts += 1
                logging.warning('fail ', e['data'], repr(error))
                sleep(0.1)
                if (attempts > 15):
                    logging.error(f'failed to fetch {e["data"]} {repr(error)}')
                    break

    with ThreadPool(max(1, min(len(res), 1000))) as pool:
        return pool.map(partial(parce, base_url=base_url),  res)


def parce_voice_lines(url):
    soup = BeautifulSoup(get_content(url),  "html.parser")
    found = set()

    def audio_url(url):
        if (url is None):
            # skip <a> tags with no href attribute
            return False
        if (any(url.endswith(ext) for ext in audio_ext)):
            if (url in found):
                # skip repetition
                return False
            found.add(url)
            return True
    res = [{'text': e.text, 'data': e.get('href')} for e in soup.findAll(
        'a') if audio_url(e.get('href'))]
    # return res
    return get_encoded_audio(res, url)


def scrap_process(q, urls):
    for tf2class, urls in urls.items():
        data = []
        # There's room for optimization by downloading and converting to mp3 in parallel
        for url in urls:
            data += parce_voice_lines(url)
        for e in data:
            # For some reason "to_mp3" doesn't parallelize
            e['data'] = to_mp3(e['data'])
        q.put((tf2class, data))
    q.put(None)


def scrap():
    urls = Config.get()
    q = mp.Queue()
    p = mp.Process(target=scrap_process, args=(q, urls))
    p.daemon = True
    p.start()
    while(True):
        res = q.get()
        if res is None:
            p.join()
            return
        yield res


# if (__name__ == "__main__"):
#     from time import time
#     s = time()
#     for e in scrap():
#         #print(e)
#         print(time()-s)
