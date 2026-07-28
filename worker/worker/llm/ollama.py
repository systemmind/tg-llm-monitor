from __future__ import annotations

from typing import Any, Dict

import httpx

from worker.llm import Llm
from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


class Ollama(Llm):
  async def classify(self, client: httpx.AsyncClient, text: str) -> Dict[str, Any]:
    model = getConfig(at_llm, at_model)
    url = getConfig(at_llm, at_url)
    logger.debug(f"perform ollama request, model: {model}")

    prompt = self.build_prompt(text)

    resp = await client.post(
      f"{url}/api/generate",
      json={
        at_model: model,
        at_prompt: prompt,
        at_stream: False,
        at_options: {
          at_temperature: 0,
        },
      },
      timeout=60.0,
    )

    resp.raise_for_status()
    data = resp.json()

    out = self.extract_json(data.get("response", ""))
    out["_ollama"] = {
      at_model: model,
      "prompt_tokens": data.get("prompt_eval_count"),
      "eval_tokens": data.get("eval_count"),
      "total_duration": data.get("total_duration"),
    }
    return out
