import os
import json

from worker.strings import *


settings = {
  at_redis: {
    at_url: os.environ.get(at_REDIS_URL) or 'redis://redis:6379/0',
    at_stream: {
      at_key: 'tg:messages',
      at_group: 'tg-classifiers',
      at_consumer: 'worker-1',
    },
    at_batch_size: 8,
    at_block_ms: 5000,
    at_claim_idle_ms: 60000,
  },
  at_pg_dsn: os.environ.get(at_PG_DSN) or '',
  at_llm: {
    at_url: os.environ.get(at_OLLAMA_HOST) or 'http://ollama:11434',
    at_model: os.environ.get(at_LLM_MODEL) or 'llama3.2',
    at_prompt: '/etc/tg-monitor/prompt.txt',
    at_local: True,
  },
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