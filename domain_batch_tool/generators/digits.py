from __future__ import annotations

import itertools
from typing import Iterable

from .base import BaseGenerator


class DigitsGenerator(BaseGenerator):
    def __init__(self, length_range=(1, 4), **options):
        super().__init__(length_range=length_range, **options)
        self.length_range = length_range

    def generate(self) -> Iterable[str]:
        digits = "0123456789"
        min_len, max_len = self.length_range
        for length in range(min_len, max_len + 1):
            for combo in itertools.product(digits, repeat=length):
                yield "".join(combo)
