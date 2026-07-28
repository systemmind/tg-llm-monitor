from __future__ import annotations

import asyncio
import json
import time
from telethon import TelegramClient, events
from telethon.sessions import SQLiteSession

import yaml
from redis.asyncio import Redis

from .settings import (
  TELEGRAM_API_ID,
  TELEGRAM_API_HASH,
  REDIS_URL,
  STREAM_KEY,
  SESSION_DIR,
  CONFIG_PATH,
)
from .filters import build_filters, any_match
from .redis_out import push_message


def load_config(path: str) -> dict:
  with open(path, "r", encoding="utf-8") as f:
    return yaml.safe_load(f) or {}


async def main():
  cfg = load_config(CONFIG_PATH)
  filters = build_filters(cfg)
  matched_only = bool((cfg.get("routing") or {}).get("matched_only", True))

  # Telethon session stored in /data/session/telegram.session (SQLite)
  session_path = f"{SESSION_DIR}/telegram"
  client = TelegramClient(SQLiteSession(session_path), TELEGRAM_API_ID, TELEGRAM_API_HASH)

  r = Redis.from_url(REDIS_URL, decode_responses=True)

  @client.on(events.NewMessage)
  async def handler(event: events.NewMessage.Event):
    msg = event.message
    text = msg.message or ""
    chat = None
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
        print(error)

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

      await push_message(r, STREAM_KEY, payload)
    finally:
      print(f"Message: \"{text[0:100]}{'...' if len(text) > 100 else ''}\" из чата \"{chat_title}\", chat_username: {chat_username}")


  await client.start()  # интерактивный логин если сессии нет
  print(f"Watcher started. Stream={STREAM_KEY}, config={CONFIG_PATH}")
  await client.run_until_disconnected()


if __name__ == "__main__":
  asyncio.run(main())
