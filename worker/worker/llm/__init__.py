from __future__ import annotations

import json
import re
from typing import Any, Dict

import httpx

from worker.settings import getConfig
from worker.logger import logger
from worker.strings import *


_JSON_RE = re.compile(r"\{.*\}", re.S)


class Llm:
  def __init__(self):
    self._http = None

  async def init(self):
    self._http = httpx.AsyncClient()

  async def close(self):
    if self._http:
      await self._http.aclose()

  async def handle(self, payload: dict) -> Dict[str, Any]:
    text = payload.get("text") or ""
    result = await self.classify(self._http, text)
    return result

  async def classify(self, client: httpx.AsyncClient, text: str) -> Dict[str, Any]:
    raise NotImplementedError

  def build_prompt(self, text: str) -> str:
    prompt = self.load_prompt()
    return f"{prompt}\n\nMessage:\n{text}"

  def load_prompt(self) -> str:
    with open(getConfig(at_llm, at_prompt), 'r', encoding='utf-8') as file:
      return file.read()

  def extract_json(self, s: str) -> Dict[str, Any]:
    s = (s or "").strip()
    m = _JSON_RE.search(s)
    if not m:
      return {"match": False, "score": None, "reason": "no_json", "raw": s}
    try:
      obj = json.loads(m.group(0))
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