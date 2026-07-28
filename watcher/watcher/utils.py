import asyncio

from watcher.logger import logger


async def cancel_tasks(tasks: set):
  for task in list(tasks):
    task.cancel()

  cancel_results = await asyncio.gather(*tasks, return_exceptions=True)

  for res in cancel_results:
    if not isinstance(res, asyncio.CancelledError):
      logger.error(f"{res!r}")

  tasks.clear()
