from python:3.12-slim

workdir /app

copy . .

run pip install -e . \
  && mkdir -p /var/log/watcher

entrypoint ["run", "--settings", "watcher/settings/settings.json"]
