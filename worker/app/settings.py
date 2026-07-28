import os

REDIS_URL = os.environ["REDIS_URL"]
STREAM_KEY = os.environ.get("STREAM_KEY", "tg:messages")
STREAM_GROUP = os.environ.get("STREAM_GROUP", "tg-classifiers")
STREAM_CONSUMER = os.environ.get("STREAM_CONSUMER", "worker-1")

PG_DSN = os.environ["PG_DSN"]

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434").rstrip("/")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")

BATCH_SIZE = int(os.environ.get("BATCH_SIZE", "8"))
BLOCK_MS = int(os.environ.get("BLOCK_MS", "5000"))

# Если воркер упал, можно "забирать" зависшие сообщения у других consumer-ов
CLAIM_IDLE_MS = int(os.environ.get("CLAIM_IDLE_MS", "60000"))

PROMPT_PATH = os.environ.get("PROMPT_PATH", "/config/prompt.txt")
