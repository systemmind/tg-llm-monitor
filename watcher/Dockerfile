from python:3.12-slim

workdir /app

copy . .

run pip install -e . \
  && mkdir -p /var/log/watcher
  && mkdir -p /etc/tg-monitor

entrypoint ["run", "--settings", "watcher/settings/settings.json"]
