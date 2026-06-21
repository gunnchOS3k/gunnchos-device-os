#!/usr/bin/env python3
"""Validate hardware component runtime package."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    "README.md",
    "configs/imported_component_stacks.yaml",
    "results/os_component_runtime_simulation.json",
]


def main() -> int:
    missing = [f for f in REQUIRED if not (ROOT / f).exists()]
    if missing:
        print("FAIL missing component runtime files:", missing)
        return 1
    print("PASS component runtime validation")
    return 0


if __name__ == "__main__":
    sys.exit(main())
