from __future__ import annotations

import time

from telethon import TelegramClient, events
from telethon.sessions import SQLiteSession
from redis.asyncio import Redis

from watcher.filters import build_filters, any_match
from watcher.redis_out import push_message
from watcher.logger import logger
from watcher.strings import *


class TgClient:
  def __init__(self, session_path: str, api_id: int, api_hash: str, redis: Redis, stream_key: str, filters, matched_only: bool):
    self.client = TelegramClient(SQLiteSession(session_path), api_id, api_hash)
    self.redis = redis
    self.stream_key = stream_key
    self.filters = filters
    self.matched_only = matched_only

    self.client.add_event_handler(self.handler, events.NewMessage)

  async def handler(self, event: events.NewMessage.Event):
    msg = event.message
    text = msg.message or ""
    chat_title = None
    chat_username = None

    try:
      ok, matched_filters = any_match(self.filters, text)

      if self.matched_only and not ok:
        return

      try:
        chat = await event.get_chat()
        chat_title = getattr(chat, "title", None)
        chat_username = getattr(chat, "username", None)
      except Exception as error:
        logger.error(f"failed to get chat info: {error}")

      payload = {
        at_ts: int(time.time()),
        at_chat_id: event.chat_id,
        at_message_id: msg.id,
        at_date: msg.date.isoformat() if msg.date else None,
        at_sender_id: msg.sender_id,
        at_text: text,
        at_matched: ok,
        at_matched_filters: matched_filters,
        at_chat_title: chat_title,
        at_chat_username: chat_username,
      }

      await push_message(self.redis, self.stream_key, payload)
    finally:
      logger.info(f"message: \"{text[:100]}\" from chat \"{chat_title}\", user: {chat_username}")

  async def start(self):
    await self.client.start()

  async def disconnect(self):
    await self.client.disconnect()

  async def run_until_disconnected(self):
    await self.client.run_until_disconnected()
