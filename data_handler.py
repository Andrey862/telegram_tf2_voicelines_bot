import logging
import os

# ------- Loggging-----------
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)


if (os.environ.get('DATABASE_URL') is None):
    logger.info('using file data handler')
    from data_handlers.file_system_data_handler import *
else:
    logger.info('using postgres data handler')
    from data_handlers.postgres_data_handler import *
