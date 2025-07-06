import os
from dotenv import load_dotenv
from logging_config import LOGGING_CONFIG
from logging.config import dictConfig
import logging

dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("__config.py__")


load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
logger.info(f"GOOGLE_CLIENT_ID loaded from environment variables")
logger.info(f"{GOOGLE_CLIENT_ID}")