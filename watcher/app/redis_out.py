from __future__ import annotations

import json
from redis.asyncio import Redis


async def push_message(r: Redis, stream_key: str, payload: dict) -> str:
  # Redis Streams values must be strings/bytes
  data = {"payload": json.dumps(payload, ensure_ascii=False)}
  msg_id = await r.xadd(stream_key, data, maxlen=200_000, approximate=True)
  return msg_id
