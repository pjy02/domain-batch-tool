from __future__ import annotations

from typing import Iterable


class BaseGenerator:
    """Base class for generators.

    Each generator yields the domain label (without TLD).
    """

    def __init__(self, **options):
        self.options = options

    def generate(self) -> Iterable[str]:
        raise NotImplementedError
