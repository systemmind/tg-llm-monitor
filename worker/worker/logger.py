import logging
import logging.config
from importlib import resources


with resources.as_file(resources.files('worker') / 'cfg' / 'logging.conf') as cfgFile:
  if cfgFile.is_file():
    logging.config.fileConfig(str(cfgFile))


logger = logging.getLogger('worker')
