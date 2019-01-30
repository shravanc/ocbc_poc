import logging
import os
import pathlib
import time
from datetime import datetime
from logging import Filter, Formatter
from logging.handlers import TimedRotatingFileHandler
from os import path

from flask import request

from constant import APP_ROOT

DE_LOG_FILE_PATH = os.path.join(APP_ROOT, "logs/de.log")
PDF_QUALITY_LOG_FILE_PATH = "/var/data/api-data/logs/qf.log"
SPLIT_PDF_LOG_FILE_PATH = "/var/data/api-data/logs/split_pdf.log"

LOG_FORMAT = '''
Level:              %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(utcnow)s
Url:                %(url)s
Method:             %(method)s
Ip:                 %(ip)s

Message:
%(message)s
'''


class ContextualLogFilter(Filter):
    def filter(self, record):
        record.utcnow = (datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S,%f %Z'))
        record.url = request.path
        record.method = request.method
        record.ip = request.environ.get('HTTP_X_REAL_IP', request.remote_addr)
        return True


def configure_logger(logger, level, log_file_path):
    ensure_parent_directories_exist(log_file_path)
    file_handler = TimedRotatingFileHandler(log_file_path, when="D", interval=7, backupCount=5, encoding="UTF-8",
                                            utc=True)
    file_handler.setFormatter(Formatter(LOG_FORMAT))
    logger.addHandler(file_handler)

    # stream_handler = StreamHandler(sys.stdout)
    # stream_handler.setFormatter(Formatter(LOG_FORMAT))
    # logger.addHandler(stream_handler)

    logger.setLevel(level)
    logger.addFilter(ContextualLogFilter())


def ensure_parent_directories_exist(file_name):
    pathlib.Path(path.dirname(file_name)).mkdir(parents=True, exist_ok=True)


def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        logging.info('%r %2.2f sec' % (method.__name__, te - ts))
        print('%r %2.2f sec' % (method.__name__, te - ts))
        return result

    return timed
