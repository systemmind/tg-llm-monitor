# Telegram LLM Monitor

A service that monitors Telegram channels/chats, filters messages by keywords, and classifies them using an LLM (local Ollama or cloud OpenAI-compatible API).

## Architecture

- **watcher** — connects to Telegram, filters messages by keywords, and pushes them to Redis Stream
- **worker** — reads messages from Redis Stream, classifies them using LLM, and saves results to PostgreSQL

## Running Ollama on host
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

Check availability from Docker:
```bash
docker compose run --rm worker-ollama python -c "import httpx; print(httpx.get('http://ollama:11434/api/tags').status_code)"
```

If it does not return 200:
- make sure Ollama listens on 127.0.0.1:11434 (or 0.0.0.0:11434);
- sometimes it is easier to explicitly tell Ollama to listen on 0.0.0.0 (depends on installation/service).


## Running the full service
```bash
# first telegram login
docker compose run --rm watcher

# enter phone number/code/2FA here
docker compose down

# basic services
docker compose up -d redis postgres watcher

# check ollama on host
curl http://127.0.0.1:11434/api/tags

# launch worker with local ollama
docker compose --profile llm up -d worker-ollama

# or launch worker with cloud LLM
docker compose --profile cloud up -d worker-cloud
```

Stop:
```bash
docker compose --profile llm stop worker-ollama
```

If you made changes and need to rebuild and restart without stopping:

For worker:
```bash
sudo docker compose --profile llm build worker-ollama
sudo docker compose --profile llm up -d --force-recreate worker-ollama
```

For watcher:
```bash
sudo docker compose build watcher
sudo docker compose up -d --force-recreate watcher
```

## Check database
```bash
docker exec -it tg-llm-monitor-postgres-1 psql -U tg -d tgmon
```

## Troubleshooting
If nvidia drivers are installed but these commands do not work:
```bash
nvidia-smi
nvidia-settings
```
the following command may fix the issue:
```bash
sudo prime-select on-demand
```
