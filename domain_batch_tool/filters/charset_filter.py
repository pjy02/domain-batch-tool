from __future__ import annotations

from .base import BaseFilter


class CharsetFilter(BaseFilter):
    def __init__(self, allowed: str):
        self.allowed = set(allowed)

    def allow(self, label: str) -> bool:
        return all(ch in self.allowed for ch in label)
