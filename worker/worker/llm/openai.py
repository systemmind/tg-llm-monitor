from __future__ import annotations

from typing import Any, Dict

import httpx

from worker.llm import Llm
from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


class OpenAi(Llm):
  async def classify(self, client: httpx.AsyncClient, text: str) -> Dict[str, Any]:
    model = getConfig(at_llm, at_model)
    url = getConfig(at_llm, at_url)
    logger.debug(f"perform openai request, model: {model}")

    prompt = self.build_prompt(text)

    resp = await client.post(
      f"{url}/v1/chat/completions",
      json={
        at_model: model,
        "messages": [
          {at_role: "system", at_content: self.load_prompt()},
          {at_role: "user", at_content: text},
        ],
        at_temperature: 0,
      },
      timeout=60.0,
    )

    resp.raise_for_status()
    data = resp.json()

    content = data.get("choices", [{}])[0].get("message", {}).get(at_content, "")
    out = self.extract_json(content)
    out["_openai"] = {
      at_model: model,
      "usage": data.get("usage"),
    }
    return out
