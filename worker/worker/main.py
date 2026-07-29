import signal
import asyncio
import argparse
from worker.logger import logger, logging
from worker.settings import updateConfig, setConfig, getConfig
from worker.app import Application, TrivialApplication
from worker.strings import *


async def main():
  parser = argparse.ArgumentParser()
  parser.add_argument("-c", "--llm-cloud", help="Use cloud model", action="store_true", default=False)
  parser.add_argument("-l", "--llm-local", help="Use local model", action="store_true", default=False)
  parser.add_argument("-s", "--settings", help="Path to settings file")
  parser.add_argument("-v", "--verbose", help="Verbose output", action="store_true", default=False)

  args = parser.parse_args()

  if args.settings:
    updateConfig(args.settings)

  if args.verbose:
    logger.setLevel(logging.DEBUG)
  else:
    logger.setLevel(logging.INFO)

  if args.llm_local and args.llm_cloud:
    raise Exception('invalid arguments: both --llm-local and --llm-cloud must not be set')
  else:
    if args.llm_local:
      setConfig(True, at_llm, at_local)
    
    if args.llm_cloud:
      setConfig(True, at_llm, at_cloud)

  app = Application() if (getConfig(at_llm, at_local) or getConfig(at_llm, at_cloud)) else TrivialApplication()

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
