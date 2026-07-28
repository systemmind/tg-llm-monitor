from __future__ import annotations

import weakref
from typing import Any, TYPE_CHECKING

from redis.asyncio import Redis
from redis.exceptions import ResponseError

from worker.logger import logger
from worker.settings import getConfig
from worker.strings import *

if TYPE_CHECKING:
  from worker.app import Application


class MessageBroker:
  def __init__(self, app: Application):
    self._app_ref = weakref.ref(app)
    redis_url = getConfig(at_redis, at_url)
    self.redis = Redis.from_url(redis_url, decode_responses=True)
    self.stream_key = getConfig(at_redis, at_stream, at_key)
    self.stream_group = getConfig(at_redis, at_stream, at_group)
    self.stream_consumer = getConfig(at_redis, at_stream, at_consumer)
    self.batch_size = getConfig(at_redis, at_batch_size)
    self.block_ms = getConfig(at_redis, at_block_ms)

  async def ensure_group(self) -> None:
    try:
      await self.redis.xgroup_create(self.stream_key, self.stream_group, id="0-0", mkstream=True)
    except ResponseError as e:
      if "BUSYGROUP" in str(e):
        return
      raise

  async def read_batch(self) -> list[tuple[str, dict[str, Any]]]:
    import json

    resp = await self.redis.xreadgroup(
      groupname=self.stream_group,
      consumername=self.stream_consumer,
      streams={self.stream_key: ">"},
      count=self.batch_size,
      block=self.block_ms,
    )

    if not resp:
      return []

    _, items = resp[0]
    out = []
    for stream_id, kv in items:
      payload_raw = kv.get("payload") or "{}"
      try:
        payload = json.loads(payload_raw)
      except Exception:
        payload = {"text": "", "_bad_payload": payload_raw}

      out.append((stream_id, payload))

    return out

  async def ack(self, stream_ids: list[str]) -> int:
    if not stream_ids:
      return 0

    return await self.redis.xack(self.stream_key, self.stream_group, *stream_ids)

  async def run(self, stop_event) -> None:
    await self.ensure_group()

    logger.info(
      f"worker loop started: stream={self.stream_key}, "
      f"group={self.stream_group}, consumer={self.stream_consumer}"
    )

    while not stop_event.is_set():
      batch = await self.read_batch()

      if not batch:
        continue

      app = self._app_ref()
      if app is None:
        break

      processed_ids = []
      for stream_id, payload in batch:
        try:
          result = await app.handleMessage(payload, stream_id)

          text = payload.get("text") or ""
          chat_title = payload.get("chat_title") or "undefined"
          chat_username = payload.get("chat_username") or "undefined"
          score = result.get('score')
          reason = result.get('reason')
          saved = result.get('_saved', False)

          if saved:
            logger.info(f"save message score={score}: \"{text[:100]}\" from chat \"{chat_title}\", user: {chat_username}, reason: {reason}")
          else:
            logger.debug(f"skip message score={score}: \"{text[:100]}\" from chat \"{chat_title}\", user: {chat_username}, reason: {reason}")

          processed_ids.append(stream_id)
        except Exception as e:
          logger.error(f"error processing {stream_id}: {e}")

      if processed_ids:
        await self.ack(processed_ids)

  async def close(self):
    await self.redis.aclose()
