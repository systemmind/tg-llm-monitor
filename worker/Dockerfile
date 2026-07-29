from python:3.12-slim

workdir /app

copy . .

run pip install -e . \
  && mkdir -p /var/log/worker \
  && mkdir -p /etc/tg-monitor

entrypoint ["run", "--settings", "worker/settings/settings.json"]
