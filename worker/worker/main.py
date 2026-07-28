import signal
import asyncio
import argparse
from worker.logger import logger, logging
from worker.settings import updateConfig, setConfig
from worker.app import Application
from worker.strings import *


async def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-o", "--ollama", help="Use ollama local model", action="store_true", default=False)
  parser.add_argument("-s", "--settings", help="Path to settings file")
  parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true", default=False)

  args = parser.parse_args()

  if args.settings:
    updateConfig(args.settings)

  if args.verbose:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  if args.ollama:
    setConfig(True, at_llm, at_local)

  app = Application()

  def sigHandle(signum):
    try:
      logger.info("signal " + str(signum))
      asyncio.create_task(app.cleanup())
    except Exception as error:
      logger.exception(error)

  loop = asyncio.get_event_loop()
  loop.add_signal_handler(signal.SIGINT, sigHandle, 'SIGINT')
  loop.add_signal_handler(signal.SIGTERM, sigHandle, 'SIGTERM')

  quit(await app())
