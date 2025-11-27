from __future__ import annotations

from typing import Any, Dict


class BaseChecker:
    def __init__(self, **options):
        self.options = options

    async def check(self, domain: str) -> Dict[str, Any]:
        raise NotImplementedError
