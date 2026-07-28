from __future__ import annotations

import json

from redis.asyncio import Redis

from watcher.settings import getSettings
from watcher.logger import logger
from watcher.strings import *


class MessageBroker:
  def __init__(self):
    redis_url = getSettings(at_redis_url)
    stream_key = getSettings(at_stream_key)
    self.redis = Redis.from_url(redis_url, decode_responses=True)
    self.stream_key = stream_key

  async def handleMessage(self, payload: dict) -> str:
    data = {"payload": json.dumps(payload, ensure_ascii=False)}
    msg_id = await self.redis.xadd(self.stream_key, data, maxlen=200_000, approximate=True)
    return msg_id

  async def close(self):
    await self.redis.aclose()
