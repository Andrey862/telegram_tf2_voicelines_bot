import logging
import os
import pickle
import re
from urllib.parse import urlparse

import psycopg2

# ------- Loggging-----------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


url = os.environ.get('DATABASE_URL')
url = urlparse(url)
username = url.username
password = url.password
database = url.path[1:]
hostname = url.hostname
port = url.port

conn = None


def refresh_conn():
    global conn
    new_conn = psycopg2.connect(
        host=hostname,
        port=port,
        database=database,
        user=username,
        password=password,
    )
    conn = new_conn


def get_by_name(name):
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DATA
                FROM MAIN
                WHERE NAME = %s
                """, (name,))

            result = cur.fetchone()
            if (not result):
                logger.info('creating table')
                cur.execute("""
                INSERT INTO main
                VALUES (%s, %s);
                """, (name, pickle.dumps('')))
                logger.debug(f'get_by_name ({name}) = ""')
                return ''
            else:
                logger.debug(
                    f'get_by_name ({name}) = {pickle.loads(result[0])}')
                return pickle.loads(result[0])


def save_by_name(data, name):
    logger.debug(f'save_by_name ({name}, {data})')
    get_by_name(name)  # to create table if it doesn't exist yet
    with conn:
        with conn.cursor() as cur:
            cur.execute("""
            UPDATE MAIN
            SET DATA = %s
            WHERE NAME = %s;
            """, (pickle.dumps(data), name))


def get_index():
    return get_by_name('index')


def get_audio_ids():
    return get_by_name('audio_ids')


def get_scrap_conf():
    return get_by_name('scrap_conf')


def save_index(index):
    return save_by_name(index, 'index')


def save_audio_ids(audio_ids):
    return save_by_name(audio_ids, 'audio_ids')


def save_scrap_conf(conf):
    return save_by_name(conf, 'scrap_conf')


# Connect to DB
refresh_conn()

# Create table if doesnt exist
with conn:
    with conn.cursor() as cur:
        # Check if the table exists
        cur.execute("""
        SELECT table_name 
        FROM information_schema.tables
        WHERE table_schema = 'public'
        """)
        tables = cur.fetchone()
        if (tables is None or 'main' not in tables):
            logger.info('creating table')
            cur.execute("""
            CREATE TABLE MAIN(
            NAME CHAR(50) PRIMARY KEY NOT NULL,
            DATA BYTEA NOT NULL
            );
            """)
