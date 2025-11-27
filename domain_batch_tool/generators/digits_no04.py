from __future__ import annotations

import itertools
from typing import Iterable

from .base import BaseGenerator


class DigitsNo04Generator(BaseGenerator):
    def __init__(self, length_range=(1, 4), mode: str = "substring", **options):
        super().__init__(length_range=length_range, mode=mode, **options)
        self.length_range = length_range
        self.mode = mode

    def _is_valid(self, value: str) -> bool:
        if self.mode == "exclude-chars":
            return "0" not in value and "4" not in value
        # default substring mode: reject substring "04"
        return "04" not in value

    def generate(self) -> Iterable[str]:
        digits = "0123456789"
        min_len, max_len = self.length_range
        for length in range(min_len, max_len + 1):
            for combo in itertools.product(digits, repeat=length):
                value = "".join(combo)
                if self._is_valid(value):
                    yield value
