from __future__ import annotations

import json
import re
from typing import Any, Dict

import httpx


from .settings import PROMPT_PATH

_JSON_RE = re.compile(r"\{.*\}", re.S)


def load_prompt(path: str) -> dict:
  with open(path, "r", encoding="utf-8") as f:
    return f.read()


def build_prompt(text: str) -> str:
  prompt = load_prompt(PROMPT_PATH)

  return f"""
{prompt}

Message:
{text}
""".strip()


def _extract_json(s: str) -> Dict[str, Any]:
  s = (s or "").strip()
  # Иногда модель оборачивает JSON текстом — пробуем вытащить объект.
  m = _JSON_RE.search(s)
  if not m:
    return {"match": False, "score": None, "reason": "no_json", "raw": s}
  try:
    obj = json.loads(m.group(0))
    # нормализация
    if "match" not in obj:
      obj["match"] = False
    if "score" in obj and obj["score"] is not None:
      try:
        obj["score"] = float(obj["score"])
      except Exception:
        obj["score"] = None
    if "reason" not in obj:
      obj["reason"] = ""
    return obj
  except Exception:
    return {"match": False, "score": None, "reason": "bad_json", "raw": s}


async def classify_with_ollama(
  client: httpx.AsyncClient,
  *,
  ollama_url: str,
  model: str,
  text: str,
) -> Dict[str, Any]:
  prompt = build_prompt(text)

  # /api/generate проще и стабилен
  resp = await client.post(
    f"{ollama_url}/api/generate",
    json={
      "model": model,
      "prompt": prompt,
      "stream": False,
      "options": {
        "temperature": 0,
      },
    },
    timeout=60.0,
  )

  resp.raise_for_status()

  data = resp.json()
  # print(f"Ollama response: {resp.text}")

  out = _extract_json(data.get("response", ""))
  out["_ollama"] = {
    "model": model,
    "prompt_tokens": data.get("prompt_eval_count"),
    "eval_tokens": data.get("eval_count"),
    "total_duration": data.get("total_duration"),
  }
  return out