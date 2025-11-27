from __future__ import annotations

import itertools
from typing import Iterable

from .base import BaseGenerator


class LettersGenerator(BaseGenerator):
    def __init__(self, length_range=(2, 3), uppercase: bool = False, **options):
        super().__init__(length_range=length_range, uppercase=uppercase, **options)
        self.length_range = length_range
        self.uppercase = uppercase

    def generate(self) -> Iterable[str]:
        letters = "abcdefghijklmnopqrstuvwxyz"
        if self.uppercase:
            letters += letters.upper()
        min_len, max_len = self.length_range
        for length in range(min_len, max_len + 1):
            for combo in itertools.product(letters, repeat=length):
                yield "".join(combo)
