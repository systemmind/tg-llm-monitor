from __future__ import annotations

import asyncio

from redis.asyncio import Redis

from watcher.filters import build_filters
from watcher.tg_client import TgClient
from watcher.settings import getSettings, getConfig
from watcher.utils import cancel_tasks
from watcher.logger import logger
from watcher.strings import *


class Application:
  def __init__(self):
    self.tasks = set()
    self.exitCode = 0
    self.tg_client = None

  def createTask(self, coro):
    task = asyncio.create_task(coro)
    self.tasks.add(task)
    task.add_done_callback(self.tasks.discard)
    return task

  async def __call__(self):
    try:
      logger.info("application started")
      try:
        await self.createTask(self._run())
      except asyncio.CancelledError:
        logger.debug("application loop task cancelled")

      return self.exitCode
    except Exception as error:
      logger.exception(error)
      return 1
    finally:
      logger.info("application exit")

  async def cleanup(self):
    if self.tg_client:
      await self.tg_client.disconnect()

    await cancel_tasks(self.tasks)

  async def _run(self):
    cfg = getConfig()
    filters = build_filters(cfg)
    matched_only = bool((cfg.get(at_routing) or {}).get(at_matched_only, True))

    session_dir = getSettings(at_session_dir)
    session_path = f"{session_dir}/telegram"
    api_id = getSettings(at_telegram, at_id)
    api_hash = getSettings(at_telegram, at_hash)
    stream_key = getSettings(at_stream_key)
    redis_url = getSettings(at_redis_url)

    r = Redis.from_url(redis_url, decode_responses=True)

    self.tg_client = TgClient(
      session_path=session_path,
      api_id=api_id,
      api_hash=api_hash,
      redis=r,
      stream_key=stream_key,
      filters=filters,
      matched_only=matched_only,
    )

    await self.tg_client.start()
    config_path = getSettings(at_config_path)
    logger.info(f"watcher started. stream={stream_key}, config={config_path}")
    await self.tg_client.run_until_disconnected()
