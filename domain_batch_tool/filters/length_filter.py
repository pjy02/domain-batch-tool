from __future__ import annotations

from .base import BaseFilter


class LengthFilter(BaseFilter):
    def __init__(self, min_length: int = 1, max_length: int | None = None):
        self.min_length = min_length
        self.max_length = max_length

    def allow(self, label: str) -> bool:
        if len(label) < self.min_length:
            return False
        if self.max_length is not None and len(label) > self.max_length:
            return False
        return True
