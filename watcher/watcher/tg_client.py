from __future__ import annotations

import time
import weakref
from typing import TYPE_CHECKING

from telethon import TelegramClient, events
from telethon.sessions import SQLiteSession

from watcher.filters import build_filters, any_match
from watcher.settings import getSettings, getConfig
from watcher.logger import logger
from watcher.strings import *

if TYPE_CHECKING:
  from watcher.app import Application


class TgClient:
  def __init__(self, app: Application):
    self._app_ref = weakref.ref(app)

    session_dir = getSettings(at_session_dir)
    session_path = f"{session_dir}/telegram"
    api_id = getSettings(at_telegram, at_id)
    api_hash = getSettings(at_telegram, at_hash)

    cfg = getConfig()
    self.filters = build_filters(cfg)
    self.matched_only = bool((cfg.get(at_routing) or {}).get(at_matched_only, True))

    self.client = TelegramClient(SQLiteSession(session_path), api_id, api_hash)
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

      app = self._app_ref()
      if app:
        await app.handleMessage(payload)

    finally:
      logger.info(f"message: \"{text[:100]}\" from user: {chat_username} in the chat \"{chat_title}\"")

  async def start(self):
    await self.client.start()

  async def disconnect(self):
    await self.client.disconnect()

  async def run_until_disconnected(self):
    await self.client.run_until_disconnected()
