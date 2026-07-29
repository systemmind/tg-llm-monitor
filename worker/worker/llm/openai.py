from __future__ import annotations

from typing import Any, Dict

from openai import OpenAI

from worker.llm import Llm, MessageMatch
from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


class OpenAi(Llm):
  def __init__(self):
    self.client = OpenAI()

  async def classify(self, text: str) -> Dict[str, Any]:
    resp = self.client.beta.chat.completions.parse(
      model=getConfig(at_llm, at_model),
      messages=[
        {at_role: at_system, at_content: self.load_prompt()},
        {at_role: at_user, at_content: text}
      ],
      response_format=MessageMatch
    )

    result = resp.choices[0].message.parsed
    return result.model_dump()


  async def close(self):
    self.client.close()
