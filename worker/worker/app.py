from __future__ import annotations

import asyncio

from worker.llm.ollama import Ollama
from worker.llm.openai import OpenAi
from worker.db import Database
from worker.message_broker import MessageBroker
from worker.settings import getConfig
from worker.utils import cancel_tasks
from worker.logger import logger
from worker.strings import *


class Application:
  def __init__(self):
    self.llm = Ollama() if getConfig(at_llm, at_local) else OpenAi()
    self.tasks = set()
    self.exitCode = 0
    self._stop = asyncio.Event()
    self.db = None
    self.broker = None

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
    await cancel_tasks(self.tasks)

    if self.broker:
      await self.broker.close()

    if self.db:
      await self.db.close()

    await self.llm.close()

  async def handleMessage(self, payload: dict, stream_id: str = '') -> dict:
    llm_result = await self.llm.handle(payload)
    saved = False

    if llm_result.get('score') and llm_result['score'] > 0.0:
      saved = True
      await self.db.insert_result(payload=payload, stream_id=stream_id, llm=llm_result)

    llm_result['_saved'] = saved
    return llm_result

  async def _run(self):
    pg_dsn = getConfig(at_pg_dsn)
    self.db = await Database.create(pg_dsn)

    await self.llm.init()

    self.broker = MessageBroker(self)
    await self.broker.run(self._stop)
