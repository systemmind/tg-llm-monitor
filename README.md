# Запуск ollama на хосте
```bash
nvidia-smi

# setup
curl -fsSL https://ollama.com/install.sh | sh

# download model
ollama pull llama3.2:3b

# run service
ollama serve

# check
curl http://127.0.0.1:11434/api/tags
```

Проверить доступность из докера:
```bash
docker compose run --rm worker python -c "import httpx; print(httpx.get('http://ollama:11434/api/tags').status_code)"
```

Если вернуло не 200:
- убедитесь, что Ollama слушает 127.0.0.1:11434 (или 0.0.0.0:11434);
- иногда проще явно сказать Ollama слушать на 0.0.0.0 (зависит от установки/сервиса).


# Запуск всего сервиса
```bash
# first telegram login
docker compose run --rm watcher
# enter phone number/code/2FA here
docker compose down

# basic services
docker compose up -d redis postgres watcher

# check ollama on host
curl http://127.0.0.1:11434/api/tags

# launch worker
docker compose --profile llm up -d worker
```

Остановить:
```bash
docker compose --profile llm stop worker
```

Если сделал изменения и надо пересобрать и перезапустить без остановки, то
для воркера:
```bash
sudo docker compose --profile llm build worker
sudo docker compose --profile llm up -d --force-recreate worker
```

либо для watcher-а
```bash
sudo docker compose build watcher
sudo docker compose up -d --force-recreate watcher
```

# Check database
```bash
docker exec -it tg-llm-monitor-postgres-1 psql -U tg -d tgmon
```

# Troubleshooting
Если драйвера nvidia установлены, но эти команды не работают:
```bash
nvidia-smi
nvidia-settings
```
то следующая команда может вылечить проблему:
```bash
sudo prime-select on-demand
```
