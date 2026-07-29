# Telegram LLM Monitor

A service that monitors Telegram channels/chats, filters messages by keywords, and classifies them using an LLM (local Ollama or cloud OpenAI-compatible API).

## Architecture

- **watcher** — connects to Telegram, filters messages by keywords, and pushes them to Redis Stream
- **worker** — reads messages from Redis Stream, classifies them using LLM, and saves results to PostgreSQL

## Running Ollama on the local host
This step is not required but it may be usefull for any debugging.

Execute the next command in the shell:
```bash
# check that nvidia works well
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

Check availability from the Docker:
```bash
docker compose run --rm worker-ollama python -c "import httpx; print(httpx.get('http://ollama:11434/api/tags').status_code)"
```

If it does not return 200:
- make sure Ollama listens on 127.0.0.1:11434 (or 0.0.0.0:11434);
- sometimes it is easier to explicitly tell Ollama to listen on 0.0.0.0 (depends on installation/service).


## Running the full service
Build docker images first:
```bash
cd /project/home/folder/tg-llm-monitor
docker compose build
```

Luanch the next command to perform telegram authorization:
```bash
# first telegram login
docker compose run --rm watcher
# enter phone number/code/2FA here and exit from the container
docker compose down
```

To launch the watcher service modify the [watcher.config.yml](watcher.config.yml) file (or use it or the [watcher/watcher/settings/config.yml](watcher/watcher/settings/config.yml) file as examples) and laucnh the docker:
```bash
# modify the watcher.config.yml
docker compose up -d redis postgres watcher
```

Launch worker with either a local ollama:
```bash
docker compose --profile llm up -d worker-ollama
# check ollama on host
curl http://127.0.0.1:11434/api/tags
```

or a cloud LLM:
```bash
docker compose --profile cloud up -d worker-cloud
```

Stop:
```bash
docker compose --profile llm stop worker-ollama
```

If you made changes and need to rebuild and restart without service stopping then execute the next commands.

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
\dt
# see the command output...
select message_id, text from tg_message_classifications;
# see the command output...
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
