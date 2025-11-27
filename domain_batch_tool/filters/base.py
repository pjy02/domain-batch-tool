from __future__ import annotations

from typing import Protocol


class BaseFilter(Protocol):
    def allow(self, label: str) -> bool:
        ...
