import os
import json

from watcher.strings import *


settings = {
  at_telegram_api_id: int(os.environ.get(at_TELEGRAM_API_ID) or 0),
  at_telegram_api_hash: os.environ.get(at_TELEGRAM_API_HASH) or '',
  at_redis_url: os.environ.get(at_REDIS_URL) or 'redis://redis:6379/0',
  at_stream_key: 'tg:messages',
  at_session_dir: '/data/session',
  at_config_path: '/config/config.yml',
}


def getConfigHelper(cfg, path, *args):
  if path in cfg:
    value = cfg[path]
    return getConfigHelper(value, *args) if len(args) > 0 else value

  return None


def getConfig(*args):
  return getConfigHelper(settings, *args) if len(args) else settings


def setConfigHelper(cfg, value, path, *args):
  cfg[path] = setConfigHelper(cfg[path], value, *args) if len(args) > 0 else value
  return cfg


def setConfig(value, *args):
  setConfigHelper(settings, value, *args)


def updateConfig(file):
  with open(file, 'r') as f:
    settings.update(json.loads(f.read()))