from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable
import re


def _norm(s: str) -> str:
  return re.sub(r"\s+", " ", s or "").strip().lower()


@dataclass(frozen=True)
class KeywordFilter:
  name: str
  enabled: bool
  include_any: tuple[str, ...]
  exclude_any: tuple[str, ...]
  min_length: int = 1

  def match(self, text: str) -> bool:
    if not self.enabled:
      return False
    t = _norm(text)
    if len(t) < self.min_length:
      return False
    if self.exclude_any and any(x in t for x in self.exclude_any):
      return False
    if self.include_any:
      return any(x in t for x in self.include_any)
    return True


def build_filters(cfg: dict) -> list[KeywordFilter]:
  res: list[KeywordFilter] = []
  for f in cfg.get("filters", []):
    res.append(
      KeywordFilter(
        name=f.get("name", "unnamed"),
        enabled=bool(f.get("enabled", True)),
        include_any=tuple(map(_norm, f.get("include_any", []) or [])),
        exclude_any=tuple(map(_norm, f.get("exclude_any", []) or [])),
        min_length=int(f.get("min_length", 1)),
      )
    )
  return res


def any_match(filters: Iterable[KeywordFilter], text: str) -> tuple[bool, list[str]]:
  matched = []
  for f in filters:
    if f.match(text):
      matched.append(f.name)

  return (len(matched) > 0, matched)