import itertools
import os
from pathlib import Path
from typing import Iterable, Iterator, List, Sequence


def ensure_directory(path: str) -> None:
    """Create parent directory for a file path if needed."""
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def load_wordlist(path: str) -> List[str]:
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def cartesian_concat(parts: Sequence[Iterable[str]]) -> Iterator[str]:
    """Concatenate strings from each iterable using cartesian product."""
    if not parts:
        return iter(())
    for combo in itertools.product(*parts):
        yield "".join(combo)


def unique_everseen(iterable: Iterable[str]) -> Iterator[str]:
    seen = set()
    for item in iterable:
        if item not in seen:
            seen.add(item)
            yield item


def apply_max_count(items: Iterable[str], max_count: int | None) -> Iterator[str]:
    if max_count is None:
        yield from items
    else:
        for idx, item in enumerate(items):
            if idx >= max_count:
                break
            yield item


def chunked(iterable: Iterable[str], size: int) -> Iterator[List[str]]:
    chunk: List[str] = []
    for item in iterable:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


def format_result(result: dict, fmt: str = "text") -> str:
    if fmt == "json":
        import json

        return json.dumps(result, ensure_ascii=False)
    if fmt == "csv":
        # Simple CSV with domain,status,backend
        fields = [result.get("domain", ""), result.get("status", ""), result.get("backend", ""), result.get("message", "")]
        return ",".join(fields)
    # default text
    status = result.get("status", "unknown")
    backend = result.get("backend", "")
    message = result.get("message", "")
    parts = [result.get("domain", ""), status]
    if backend:
        parts.append(f"via {backend}")
    if message:
        parts.append(message)
    return " ".join(parts)
