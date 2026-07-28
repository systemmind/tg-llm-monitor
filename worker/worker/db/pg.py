from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

import asyncpg
from importlib import resources

from worker.logger import logger


async def init_db(pool: asyncpg.Pool) -> None:
  with resources.as_file(resources.files('worker') / 'db' / 'schema.sql') as schema_file:
    schema = schema_file.read_text(encoding='utf-8')

  async with pool.acquire() as conn:
    await conn.execute(schema)
  logger.info("database schema initialized")


def _parse_dt(s: Optional[str]) -> Optional[datetime]:
  if not s:
    return None
  try:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))
  except Exception:
    return None


async def insert_result(pool, *, payload, stream_id: str, llm: dict) -> None:
  async with pool.acquire() as conn:
    llm_raw_json = json.dumps(llm, ensure_ascii=False)

    await conn.execute(
      """
      INSERT INTO tg_message_classifications (
        chat_id, message_id, msg_date, sender_id, chat_title, chat_username,
        matched_by_keywords, matched_filters,
        text,
        llm_match, llm_score, llm_reason, llm_raw,
        stream_id
      )
      VALUES (
        $1,$2,$3,$4,$5,$6,
        $7,$8,
        $9,
        $10,$11,$12,$13::jsonb,
        $14
      )
      ON CONFLICT (chat_id, message_id)
      DO UPDATE SET
        llm_match = EXCLUDED.llm_match,
        llm_score = EXCLUDED.llm_score,
        llm_reason = EXCLUDED.llm_reason,
        llm_raw = EXCLUDED.llm_raw,
        stream_id = EXCLUDED.stream_id
      """,
      int(payload["chat_id"]),
      int(payload["message_id"]),
      _parse_dt(payload.get("date")),
      payload.get("sender_id"),
      payload.get("chat_title"),
      payload.get("chat_username"),
      bool(payload.get("matched", False)),
      payload.get("matched_filters") or [],
      payload.get("text") or "",
      bool(llm.get("match", False)),
      llm.get("score"),
      llm.get("reason"),
      llm_raw_json,
      stream_id,
    )
