from __future__ import annotations

import asyncio
import signal

import asyncpg
import httpx
from redis.asyncio import Redis

from .settings import (
  REDIS_URL,
  STREAM_KEY,
  STREAM_GROUP,
  STREAM_CONSUMER,
  PG_DSN,
  OLLAMA_URL,
  OLLAMA_MODEL,
  BATCH_SIZE,
  BLOCK_MS,
)

from .redis_in import ensure_group, read_batch, ack
from .llm_ollama import classify_with_ollama
from .pg import init_db, insert_result


class GracefulExit:
  def __init__(self) -> None:
    self._stop = asyncio.Event()

  def install(self) -> None:
    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
      try:
        loop.add_signal_handler(sig, self._stop.set)
      except NotImplementedError:
        # на некоторых платформах может не работать
        signal.signal(sig, lambda *_: self._stop.set())

  @property
  def stop_event(self) -> asyncio.Event:
    return self._stop


async def process_one(
  *,
  pool: asyncpg.Pool,
  http: httpx.AsyncClient,
  stream_id: str,
  payload: dict,
) -> dict:
  text = payload.get("text") or ""
  llm = await classify_with_ollama(
    http,
    ollama_url=OLLAMA_URL,
    model=OLLAMA_MODEL,
    text=text,
  )

  saved = False
  if llm['score'] > 0.0:
    saved = True
    await insert_result(pool, payload=payload, stream_id=stream_id, llm=llm)

  return llm, saved


async def main():
  exit_ctl = GracefulExit()
  exit_ctl.install()

  r = Redis.from_url(REDIS_URL, decode_responses=True)
  await ensure_group(r, STREAM_KEY, STREAM_GROUP)

  pool = await asyncpg.create_pool(PG_DSN, min_size=1, max_size=10)
  await init_db(pool)

  async with httpx.AsyncClient() as http:
    print(
      "Worker started:",
      f"stream={STREAM_KEY}",
      f"group={STREAM_GROUP}",
      f"consumer={STREAM_CONSUMER}",
      f"ollama={OLLAMA_URL}",
      f"model={OLLAMA_MODEL}",
      flush=True,
    )

    while not exit_ctl.stop_event.is_set():
      batch = await read_batch(
        r,
        stream_key=STREAM_KEY,
        group=STREAM_GROUP,
        consumer=STREAM_CONSUMER,
        batch_size=BATCH_SIZE,
        block_ms=BLOCK_MS,
      )

      if not batch:
        continue

      # последовательно (проще и безопаснее по RAM/CPU).
      # если нужно — можно добавить concurrency semaphore.
      processed_ids = []
      for stream_id, payload in batch:
        try:
          llm, saved = await process_one(pool=pool, http=http, stream_id=stream_id, payload=payload)

          text = payload.get("text") or ""
          chat_title = payload.get("chat_title") or 'undefined'
          chat_username = payload.get("chat_username") or 'undefined'
          if saved:
            print(f"\033[31mSave message with score: {llm['score']}:\033[0m \"{text[0:100]}{'...' if len(text) > 100 else ''}\" из чата \"{chat_title}\", chat_username: {chat_username}, reason: {llm['reason']}")
          else:
            print(f"\033[90mSkip message with score: {llm['score']}:\033[0m \"{text[0:100]}{'...' if len(text) > 100 else ''}\" из чата \"{chat_title}\", chat_username: {chat_username}, reason: {llm['reason']}")

          processed_ids.append(stream_id)
        except Exception as e:
          # не ack, чтобы можно было повторить позже
          print(f"Error processing {stream_id}: {e}", flush=True)

      if processed_ids:
        await ack(r, stream_key=STREAM_KEY, group=STREAM_GROUP, stream_ids=processed_ids)

  await pool.close()
  await r.aclose()


if __name__ == "__main__":
  asyncio.run(main())
