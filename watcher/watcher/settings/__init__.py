import os
import json

import yaml

from watcher.strings import *


settings = {
  at_telegram: {
    at_id: int(os.environ.get(at_TELEGRAM_API_ID) or 0),
    at_hash: os.environ.get(at_TELEGRAM_API_HASH) or '',
  },
  at_redis_url: os.environ.get(at_REDIS_URL) or 'redis://redis:6379/0',
  at_stream_key: 'tg:messages',
  at_session_dir: '/data/session',
  at_config_path: '/etc/tg-monitor/config.yml',
}

config = {}


def _helper(cfg, path, *args):
  if path in cfg:
    value = cfg[path]
    return _helper(value, *args) if len(args) > 0 else value

  return None


def _setHelper(cfg, value, path, *args):
  cfg[path] = _setHelper(cfg[path], value, *args) if len(args) > 0 else value
  return cfg


def getSettings(*args):
  return _helper(settings, *args) if len(args) else settings


def setSettings(value, *args):
  _setHelper(settings, value, *args)


def getConfig(*args):
  return _helper(config, *args) if len(args) else config


def setConfig(value, *args):
  _setHelper(config, value, *args)


def updateSettings(file):
  with open(file, 'r') as f:
    settings.update(json.loads(f.read()))


def updateConfig(path=None):
  global config
  config_path = path or settings[at_config_path]

  with open(config_path, 'r', encoding='utf-8') as f:
    config.update(yaml.safe_load(f) or {})