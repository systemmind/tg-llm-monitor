from setuptools import setup, find_packages

setup(
  name='tg-llm-watcher',
  version='1.0.0',
  description='Telegram LLM monitor watcher',
  author='Illia Rohozhkin',
  author_email='systemmind@ukr.net',
  url='https://github.com/systemmind/tg-llm-monitor',
  install_requires=[
    'telethon==1.40.0',
    'PyYAML==6.0.2',
    'redis==5.0.8',
  ],
  packages=find_packages(),
  package_data={'watcher': ['cfg/logging.conf', 'settings/settings.json', 'settings/config.yml']},
  scripts=['watcher/run']
)
