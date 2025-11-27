from __future__ import annotations

from .base import BaseFilter


class BlacklistFilter(BaseFilter):
    def __init__(self, entries: list[str]):
        self.entries = entries

    def allow(self, label: str) -> bool:
        return not any(entry in label for entry in self.entries)
