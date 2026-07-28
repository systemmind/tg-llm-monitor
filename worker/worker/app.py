from __future__ import annotations

import asyncio

import asyncpg
import httpx
from redis.asyncio import Redis

from worker.llm.ollama import Ollama
from worker.llm.openai import OpenAi
from worker.db.pg import init_db, insert_result
from worker.redis_in import ensure_group, read_batch, ack
from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


class Application:
  def __init__(self):
    self.llm = Ollama() if getConfig(at_llm, at_local) else OpenAi()
    self.tasks = set()
    self.exitCode = 0
    self._stop = asyncio.Event()

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
    self._stop.set()
    for task in self.tasks:
      task.cancel()
    await asyncio.gather(*self.tasks, return_exceptions=True)
    self.tasks.clear()

  async def _run(self):
    redis_url = getConfig(at_redis_url)
    stream_key = getConfig(at_stream, at_key)
    stream_group = getConfig(at_stream, at_group)
    stream_consumer = getConfig(at_stream, at_consumer)
    batch_size = getConfig(at_batch_size)
    block_ms = getConfig(at_block_ms)
    pg_dsn = getConfig(at_pg_dsn)

    r = Redis.from_url(redis_url, decode_responses=True)
    await ensure_group(r, stream_key, stream_group)

    pool = await asyncpg.create_pool(pg_dsn, min_size=1, max_size=10)
    await init_db(pool)

    async with httpx.AsyncClient() as http:
      logger.info(
        f"worker loop started: stream={stream_key}, "
        f"group={stream_group}, consumer={stream_consumer}"
      )

      while not self._stop.is_set():
        batch = await read_batch(
          r,
          stream_key=stream_key,
          group=stream_group,
          consumer=stream_consumer,
          batch_size=batch_size,
          block_ms=block_ms,
        )

        if not batch:
          continue

        processed_ids = []
        for stream_id, payload in batch:
          try:
            llm_result = await self.llm.classify(http, payload.get("text") or "")
            saved = False

            if llm_result.get('score') and llm_result['score'] > 0.0:
              saved = True
              await insert_result(pool, payload=payload, stream_id=stream_id, llm=llm_result)

            text = payload.get("text") or ""
            chat_title = payload.get("chat_title") or "undefined"
            chat_username = payload.get("chat_username") or "undefined"
            score = llm_result.get('score')
            reason = llm_result.get('reason')

            if saved:
              logger.info(f"save message score={score}: \"{text[:100]}\" from chat \"{chat_title}\", user: {chat_username}, reason: {reason}")
            else:
              logger.debug(f"skip message score={score}: \"{text[:100]}\" from chat \"{chat_title}\", user: {chat_username}, reason: {reason}")

            processed_ids.append(stream_id)
          except Exception as e:
            logger.error(f"error processing {stream_id}: {e}")

        if processed_ids:
          await ack(r, stream_key=stream_key, group=stream_group, stream_ids=processed_ids)

    await pool.close()
    await r.aclose()
