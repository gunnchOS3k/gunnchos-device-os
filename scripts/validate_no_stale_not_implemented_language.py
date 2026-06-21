#!/usr/bin/env python3
"""Fail on stale requirements-only / not-implemented language without implementation links."""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STALE_PATTERNS = [
    r"requirements defined only",
    r"no firmware implementation claimed",
]

ALLOWLIST_DIRS = {
    "implementation_backlog",
    "results",
    "demo",
}

IMPLEMENTATION_MARKERS = [
    "firmware_compat/",
    "hardware_component_runtime/",
    "implemented in",
    "simulation harness",
    "validate_",
    "implementation_backlog/",
]

SKIP_FILES = {"NOT_IMPLEMENTED_LANGUAGE_AUDIT.md", "CLAIM_BOUNDARY.md"}


def main() -> int:
    violations = []
    for path in ROOT.rglob("*.md"):
        if any(part.startswith(".") for part in path.parts):
            continue
        if path.name in SKIP_FILES:
            continue
        if any(d in path.parts for d in ALLOWLIST_DIRS):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pat in STALE_PATTERNS:
            if re.search(pat, text, re.I):
                if any(m.lower() in text.lower() for m in IMPLEMENTATION_MARKERS):
                    continue
                violations.append(str(path.relative_to(ROOT)))
    if violations:
        print("FAIL stale language:", violations[:15])
        return 1
    print("PASS no stale not-implemented language")
    return 0


if __name__ == "__main__":
    sys.exit(main())
