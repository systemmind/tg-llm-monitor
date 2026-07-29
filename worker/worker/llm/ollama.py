from __future__ import annotations

from typing import Any, Dict

from ollama import chat

from worker.llm import Llm, JobPosting
from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


class Ollama(Llm):
  async def classify(self, text: str) -> Dict[str, Any]:
    model = getConfig(at_llm, at_model)
    url = getConfig(at_llm, at_url)
    logger.debug(f"perform ollama request, model: {model}")

    response = chat(
      model=model,
      messages=[
        {
          at_role: at_system,
          at_content: self.load_prompt()
        },
        {
          at_role: at_user,
          at_content: text
        }
      ],
      format=JobPosting.model_json_schema(),
      options={'temperature': 0},
    )

    result = JobPosting.model_validate_json(response.message.content)
    return result.model_dump()


  async def close(self):
    pass
