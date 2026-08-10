#!/usr/bin/env python3
"""Run Phase XII RJ acceptance set and write artifacts."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.phase_xii.journeys.rj_acceptance import run_rj_set  # noqa: E402


def main() -> int:
    summary = run_rj_set(ROOT)
    print(json.dumps({
        "pass_count": summary.get("pass_count"),
        "fail_count": summary.get("fail_count"),
        "failed": summary.get("failed"),
        "REAL_APP_X0_OPEN": summary.get("REAL_APP_X0_OPEN"),
        "REAL_APP_X1_OPEN": summary.get("REAL_APP_X1_OPEN"),
        "REAL_APP_X2_OPEN": summary.get("REAL_APP_X2_OPEN"),
        "tokens": summary.get("tokens"),
    }, indent=2))
    # Non-zero if X0 open. Wave 0 CI sets REQUIRE_REAL_APP_X1_ZERO=1 so X1 also fails closed.
    import os
    require_x1_zero = os.environ.get("REQUIRE_REAL_APP_X1_ZERO", "").strip() in {"1", "true", "TRUE", "yes"}
    if summary.get("REAL_APP_X0_OPEN", 0):
        return 1
    if require_x1_zero and summary.get("REAL_APP_X1_OPEN", 0):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
