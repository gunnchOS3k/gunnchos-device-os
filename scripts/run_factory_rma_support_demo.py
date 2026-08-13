#!/usr/bin/env python3
"""Run the factory/RMA/support digital STREAM evaluation (DEV/TEST)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.ops.stream_eval import evaluate  # noqa: E402


def main() -> int:
    report = evaluate(ROOT)
    print(json.dumps({k: report[k] for k in ("ok", "status", "PRODUCTION_RELEASE_CLAIMED", "commercial_warranty", "artifact")}, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
