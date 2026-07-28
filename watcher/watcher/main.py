import signal
import asyncio
import argparse
from watcher.logger import logger, logging
from watcher.settings import updateSettings, updateConfig, setSettings
from watcher.app import Application
from watcher.strings import *


async def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-s", "--settings", help="Path to settings file")
  parser.add_argument("-c", "--config", help="Path to config yml file")
  parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true", default=False)

  args = parser.parse_args()

  if args.settings:
    updateSettings(args.settings)

  if args.config:
    setSettings(args.config, at_config_path)

  if args.verbose:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  updateConfig()

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
