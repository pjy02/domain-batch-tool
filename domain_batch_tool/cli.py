from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import Iterable

from .config import load_config
from .pipeline import Pipeline, apply_filters, build_filters, build_generators
from .utils import apply_max_count, cartesian_concat, ensure_directory


def parse_args():
    parser = argparse.ArgumentParser(description="Batch domain generator and checker")
    parser.add_argument("--config", default=None, help="Path to YAML config file")
    subparsers = parser.add_subparsers(dest="command", required=False)

    gen_parser = subparsers.add_parser("generate", help="Generate domain labels only")
    gen_parser.add_argument("--output", default=None, help="Output file path (default stdout)")
    gen_parser.add_argument("--max-count", type=int, default=None, help="Maximum number of labels to generate")

    check_parser = subparsers.add_parser("check", help="Check domains from file")
    check_parser.add_argument("input", help="File containing domains, one per line")
    check_parser.add_argument("--output", default=None, help="Output file path (default stdout)")

    pipeline_parser = subparsers.add_parser("pipeline", help="Generate + check domains")
    pipeline_parser.add_argument("--output", default=None, help="Output file path (default from config)")

    return parser.parse_args()


def handle_generate(settings, output: str | None, max_count: int | None):
    parts = build_generators(settings)
    filters = build_filters(settings)
    labels: Iterable[str] = cartesian_concat(parts)
    labels = (label for label in labels if apply_filters(label, filters))
    labels = apply_max_count(labels, max_count or settings.max_count)

    if output:
        ensure_directory(output)
        Path(output).write_text("\n".join(labels), encoding="utf-8")
    else:
        for label in labels:
            print(label)


def handle_check(settings, input_path: str, output: str | None):
    pipeline = Pipeline(settings)
    domains = Path(input_path).read_text(encoding="utf-8").splitlines()
    pipeline.parts = [domains]
    pipeline.settings.tlds = [""]  # domains already include tld
    asyncio.run(pipeline.run_and_write())


def handle_pipeline(settings, output: str | None):
    if output:
        settings.output.file = output
    pipeline = Pipeline(settings)
    asyncio.run(pipeline.run_and_write())


def main():
    args = parse_args()
    settings = load_config(args.config)
    command = args.command or settings.mode

    if command == "generate":
        handle_generate(settings, args.output, args.max_count)
    elif command == "check":
        handle_check(settings, args.input, args.output)
    else:
        handle_pipeline(settings, getattr(args, "output", None))


if __name__ == "__main__":
    main()
