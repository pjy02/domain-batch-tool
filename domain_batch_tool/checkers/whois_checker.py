from __future__ import annotations

import asyncio
from typing import Any, Dict

from .base import BaseChecker


class WhoisChecker(BaseChecker):
    async def check(self, domain: str) -> Dict[str, Any]:
        # Placeholder for WHOIS lookup. For now, mark as unknown to avoid false positives.
        await asyncio.sleep(0)
        return {
            "domain": domain,
            "status": "unknown",
            "backend": "whois",
            "message": "whois lookup not implemented",
        }
