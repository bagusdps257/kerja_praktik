import logging
import os
from logging.handlers import RotatingFileHandler

from config.settings import LOG_PATH

# Ensure directory for LOG_PATH exists
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

# Module-level logger setup
logger = logging.getLogger("ocr_logger")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8"
    )
    formatter = logging.Formatter("[%(asctime)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def catat_log(pesan):
    logger.info(pesan)

    try:
        print(f"[LOG] {pesan}")
    except UnicodeEncodeError:
        print(f"[LOG] {pesan.encode('ascii', errors='replace').decode('ascii')}")