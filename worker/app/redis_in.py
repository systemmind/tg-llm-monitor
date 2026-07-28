from __future__ import annotations

import json
from typing import Any, Iterable, List, Tuple

from redis.asyncio import Redis
from redis.exceptions import ResponseError


async def ensure_group(r: Redis, stream_key: str, group: str) -> None:
  try:
    # mkstream=True создаст stream, если его ещё нет
    await r.xgroup_create(stream_key, group, id="0-0", mkstream=True)
  except ResponseError as e:
    if "BUSYGROUP" in str(e):
      return
    raise


def _decode_messages(
  items: list[tuple[str, dict[str, str]]],
) -> list[tuple[str, dict[str, Any]]]:
  out = []
  for stream_id, kv in items:
    payload_raw = kv.get("payload") or "{}"
    try:
      payload = json.loads(payload_raw)
    except Exception:
      payload = {"text": "", "_bad_payload": payload_raw}
    out.append((stream_id, payload))
  return out


async def read_batch(
  r: Redis,
  *,
  stream_key: str,
  group: str,
  consumer: str,
  batch_size: int,
  block_ms: int,
) -> list[tuple[str, dict[str, Any]]]:
  resp = await r.xreadgroup(
    groupname=group,
    consumername=consumer,
    streams={stream_key: ">"},
    count=batch_size,
    block=block_ms,
  )
  if not resp:
    return []
  # resp: [(stream_key, [(id, {k:v}), ...])]
  _, items = resp[0]
  return _decode_messages(items)


async def ack(
  r: Redis,
  *,
  stream_key: str,
  group: str,
  stream_ids: Iterable[str],
) -> int:
  ids = list(stream_ids)
  if not ids:
    return 0
  return await r.xack(stream_key, group, *ids)