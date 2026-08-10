#!/usr/bin/env python3
"""Validate Golden Journey scorecards / fixtures / competitor matrix structure."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.golden_journeys.scorecard import validate_scorecards  # noqa: E402


def main() -> int:
    report = validate_scorecards(root=ROOT)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
