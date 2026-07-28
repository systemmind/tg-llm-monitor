from setuptools import setup, find_packages

setup(
  name='tg-llm-worker',
  version='1.0.0',
  description='Telegram LLM monitor worker',
  author='Illia Rohozhkin',
  author_email='systemmind@ukr.net',
  url='https://github.com/systemmind/tg-llm-monitor',
  install_requires=[
    'redis==5.0.8',
    'asyncpg==0.29.0',
    'httpx==0.27.2',
  ],
  packages=find_packages(),
  package_data={'worker': ['cfg/logging.conf', 'db/schema.sql', 'settings/settings.json']},
  scripts=['worker/run']
)
