from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError as exc:  # pragma: no cover - dependency hint
    raise ImportError("PyYAML is required to load configuration. Please install with `pip install -r requirements.txt`.") from exc


@dataclass
class OutputConfig:
    format: str
    file: Optional[str]


@dataclass
class FilterConfig:
    enabled: bool
    options: Dict[str, Any]


@dataclass
class GeneratorConfig:
    type: str
    enabled: bool
    options: Dict[str, Any]


@dataclass
class CheckerConfig:
    enabled: bool
    options: Dict[str, Any]


@dataclass
class Settings:
    mode: str
    output: OutputConfig
    max_count: Optional[int]
    tlds: List[str]
    filters: Dict[str, FilterConfig]
    generators: List[GeneratorConfig]
    checkers: Dict[str, CheckerConfig]
    concurrency: int


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "default.yaml"


def load_config(path: str | None = None) -> Settings:
    config_path = Path(path) if path else DEFAULT_CONFIG_PATH
    with config_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    output_cfg = OutputConfig(format=data.get("output", {}).get("format", "text"), file=data.get("output", {}).get("file"))

    filters: Dict[str, FilterConfig] = {}
    for key, raw in data.get("filters", {}).items():
        filters[key] = FilterConfig(enabled=raw.get("enabled", False), options={k: v for k, v in raw.items() if k != "enabled"})

    generators: List[GeneratorConfig] = []
    for gen in data.get("generators", []):
        generators.append(
            GeneratorConfig(
                type=gen.get("type"),
                enabled=gen.get("enabled", True),
                options={k: v for k, v in gen.items() if k not in {"type", "enabled"}},
            )
        )

    checkers: Dict[str, CheckerConfig] = {}
    for key, raw in data.get("checkers", {}).items():
        checkers[key] = CheckerConfig(enabled=raw.get("enabled", False), options={k: v for k, v in raw.items() if k != "enabled"})

    return Settings(
        mode=data.get("mode", "pipeline"),
        output=output_cfg,
        max_count=data.get("max_count"),
        tlds=data.get("tlds", []),
        filters=filters,
        generators=generators,
        checkers=checkers,
        concurrency=data.get("concurrency", 10),
    )
