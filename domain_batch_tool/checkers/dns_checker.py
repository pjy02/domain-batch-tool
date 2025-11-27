from __future__ import annotations

import asyncio
import socket
from typing import Any, Dict

from .base import BaseChecker


class DNSChecker(BaseChecker):
    async def _resolve(self, domain: str) -> bool:
        try:
            await asyncio.wait_for(asyncio.to_thread(socket.getaddrinfo, domain, None), timeout=self.options.get("timeout", 3))
            return True
        except Exception:
            return False

    async def check(self, domain: str) -> Dict[str, Any]:
        resolved = await self._resolve(domain)
        return {
            "domain": domain,
            "status": "registered" if resolved else "available",
            "backend": "dns",
            "message": "record found" if resolved else "no dns record",
        }
