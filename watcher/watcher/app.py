from __future__ import annotations

import asyncio

from watcher.tg_client import TgClient
from watcher.message_broker import MessageBroker
from watcher.settings import getSettings
from watcher.utils import cancel_tasks
from watcher.logger import logger
from watcher.strings import *


class Application:
  def __init__(self):
    self.tasks = set()
    self.exitCode = 0
    self.tg_client = None
    self.broker = MessageBroker()

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

    await self.broker.close()
    await cancel_tasks(self.tasks)

  async def handleMessage(self, payload: dict):
    await self.broker.handleMessage(payload)

  async def _run(self):
    self.tg_client = TgClient(self)

    await self.tg_client.start()
    stream_key = getSettings(at_stream_key)
    config_path = getSettings(at_config_path)
    logger.info(f"watcher started. stream={stream_key}, config={config_path}")
    await self.tg_client.run_until_disconnected()
