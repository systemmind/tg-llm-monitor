import os

TELEGRAM_API_ID = int(os.environ["TELEGRAM_API_ID"])
TELEGRAM_API_HASH = os.environ["TELEGRAM_API_HASH"]

REDIS_URL = os.environ["REDIS_URL"]
STREAM_KEY = os.environ.get("STREAM_KEY", "tg:messages")

SESSION_DIR = os.environ.get("SESSION_DIR", "/data/session")
CONFIG_PATH = os.environ.get("CONFIG_PATH", "/config/config.yml")