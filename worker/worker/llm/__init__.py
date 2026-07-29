from __future__ import annotations

import json
import re
from typing import Any, Dict
from pydantic import BaseModel, Field

from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


class JobPosting(BaseModel):
  # FIXME: implement this class
  pass


class Llm:
  def __init__(self):
    pass

  async def init(self):
    pass

  async def close(self):
    pass

  async def handle(self, payload: dict) -> Dict[str, Any]:
    text = payload.get("text") or ""
    result = await self.classify(text)
    return result

  async def classify(self, text: str) -> Dict[str, Any]:
    raise NotImplementedError

  def build_prompt(self, text: str) -> str:
    prompt = self.load_prompt()
    return f"{prompt}\n\nMessage:\n{text}"

  def load_prompt(self) -> str:
    with open(getConfig(at_llm, at_prompt), 'r', encoding='utf-8') as file:
      return file.read()
