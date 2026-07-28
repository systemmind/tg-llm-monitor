from __future__ import annotations

import asyncio
import time

import yaml
from telethon import TelegramClient, events
from telethon.sessions import SQLiteSession
from redis.asyncio import Redis

from watcher.filters import build_filters, any_match
from watcher.redis_out import push_message
from watcher.settings import getConfig
from watcher.logger import logger
from watcher.strings import *


def load_config(path: str) -> dict:
  with open(path, "r", encoding="utf-8") as f:
    return yaml.safe_load(f) or {}


class Application:
  def __init__(self):
    self.tasks = set()
    self.exitCode = 0
    self.client = None

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
    if self.client:
      await self.client.disconnect()
    for task in self.tasks:
      task.cancel()
    await asyncio.gather(*self.tasks, return_exceptions=True)
    self.tasks.clear()

  async def _run(self):
    config_path = getConfig(at_config_path)
    cfg = load_config(config_path)
    filters = build_filters(cfg)
    matched_only = bool((cfg.get(at_routing) or {}).get(at_matched_only, True))

    session_dir = getConfig(at_session_dir)
    session_path = f"{session_dir}/telegram"
    api_id = getConfig(at_telegram_api_id)
    api_hash = getConfig(at_telegram_api_hash)
    stream_key = getConfig(at_stream_key)

    self.client = TelegramClient(SQLiteSession(session_path), api_id, api_hash)
    r = Redis.from_url(getConfig(at_redis_url), decode_responses=True)

    @self.client.on(events.NewMessage)
    async def handler(event: events.NewMessage.Event):
      msg = event.message
      text = msg.message or ""
      chat_title = None
      chat_username = None

      try:
        ok, matched_filters = any_match(filters, text)

        if matched_only and not ok:
          return

        try:
          chat = await event.get_chat()
          chat_title = getattr(chat, "title", None)
          chat_username = getattr(chat, "username", None)
        except Exception as error:
          logger.error(f"failed to get chat info: {error}")

        payload = {
          "ts": int(time.time()),
          "chat_id": event.chat_id,
          "message_id": msg.id,
          "date": msg.date.isoformat() if msg.date else None,
          "sender_id": msg.sender_id,
          "text": text,
          "matched": ok,
          "matched_filters": matched_filters,
          "chat_title": chat_title,
          "chat_username": chat_username,
        }

        await push_message(r, stream_key, payload)
      finally:
        logger.info(f"message: \"{text[:100]}\" from chat \"{chat_title}\", user: {chat_username}")

    await self.client.start()
    logger.info(f"watcher started. stream={stream_key}, config={config_path}")
    await self.client.run_until_disconnected()
