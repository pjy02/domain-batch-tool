from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Iterable, List

from .checkers.dns_checker import DNSChecker
from .checkers.whois_checker import WhoisChecker
from .config import Settings
from .filters.blacklist_filter import BlacklistFilter
from .filters.charset_filter import CharsetFilter
from .filters.length_filter import LengthFilter
from .generators.digits import DigitsGenerator
from .generators.digits_no04 import DigitsNo04Generator
from .generators.letters import LettersGenerator
from .generators.wordlist import WordlistGenerator
from .utils import apply_max_count, cartesian_concat, ensure_directory, format_result, unique_everseen


GENERATOR_REGISTRY = {
    "letters": LettersGenerator,
    "digits": DigitsGenerator,
    "digits_no04": DigitsNo04Generator,
    "wordlist": WordlistGenerator,
}

CHECKER_REGISTRY = {
    "dns": DNSChecker,
    "whois": WhoisChecker,
}


def build_generators(settings: Settings):
    parts: List[Iterable[str]] = []
    for gen_cfg in settings.generators:
        if not gen_cfg.enabled:
            continue
        cls = GENERATOR_REGISTRY.get(gen_cfg.type)
        if not cls:
            continue
        generator = cls(**gen_cfg.options)
        parts.append(generator.generate())
    return parts


def build_filters(settings: Settings):
    filters = []
    if settings.filters.get("length", {}).enabled:
        opts = settings.filters["length"].options
        filters.append(LengthFilter(min_length=opts.get("min_length", 1), max_length=opts.get("max_length")))
    if settings.filters.get("charset", {}).enabled:
        opts = settings.filters["charset"].options
        filters.append(CharsetFilter(allowed=opts.get("allowed", "abcdefghijklmnopqrstuvwxyz0123456789")))
    if settings.filters.get("blacklist", {}).enabled:
        opts = settings.filters["blacklist"].options
        filters.append(BlacklistFilter(entries=opts.get("entries", [])))
    return filters


def apply_filters(label: str, filters: List) -> bool:
    return all(f.allow(label) for f in filters)


def build_checkers(settings: Settings):
    checkers = []
    for key, cfg in settings.checkers.items():
        if not cfg.enabled:
            continue
        cls = CHECKER_REGISTRY.get(key)
        if not cls:
            continue
        checkers.append(cls(**cfg.options))
    return checkers


class Pipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.filters = build_filters(settings)
        self.checkers = build_checkers(settings)
        self.parts = build_generators(settings)

    def _generate_labels(self) -> Iterable[str]:
        combined = cartesian_concat(self.parts)
        filtered = (label for label in combined if apply_filters(label, self.filters))
        unique = unique_everseen(filtered)
        return apply_max_count(unique, self.settings.max_count)

    def _expand_tlds(self, labels: Iterable[str]) -> Iterable[str]:
        for label in labels:
            for tld in self.settings.tlds:
                yield f"{label}{tld}"

    async def _check_domain(self, domain: str):
        # Run checkers in order; first non-unknown result wins.
        for checker in self.checkers:
            result = await checker.check(domain)
            if result.get("status") != "unknown":
                return result
        if self.checkers:
            # fall back to last checker result
            return result
        return {"domain": domain, "status": "unknown", "backend": "none", "message": "no checkers configured"}

    async def _check_worker(self, domain: str, sem: asyncio.Semaphore, results: List[dict]):
        async with sem:
            result = await self._check_domain(domain)
            results.append(result)

    async def run(self) -> List[dict]:
        labels = list(self._generate_labels())
        domains = list(self._expand_tlds(labels))
        if not self.checkers:
            # no checking; return as available
            return [{"domain": domain, "status": "generated", "backend": "none"} for domain in domains]

        sem = asyncio.Semaphore(self.settings.concurrency)
        tasks = []
        results: List[dict] = []
        for domain in domains:
            tasks.append(asyncio.create_task(self._check_worker(domain, sem, results)))
        await asyncio.gather(*tasks)
        return results

    async def run_and_write(self):
        results = await self.run()
        output_path = self.settings.output.file
        fmt = self.settings.output.format
        lines = [format_result(res, fmt=fmt) for res in results]
        if output_path:
            ensure_directory(output_path)
            Path(output_path).write_text("\n".join(lines), encoding="utf-8")
        else:
            for line in lines:
                print(line)
