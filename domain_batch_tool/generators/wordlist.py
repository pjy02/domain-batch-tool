from __future__ import annotations

from typing import Iterable

from .base import BaseGenerator
from ..utils import load_wordlist


class WordlistGenerator(BaseGenerator):
    def __init__(self, file: str, **options):
        super().__init__(file=file, **options)
        self.file = file

    def generate(self) -> Iterable[str]:
        yield from load_wordlist(self.file)
