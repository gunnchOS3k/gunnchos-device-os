#!/usr/bin/env python3
"""CI firewall: reject false *_ready=true claims without evidence."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.cont_viii.release_readiness import (  # noqa: E402
    evaluate_release_readiness,
    scan_false_ready_claims,
)


def main() -> int:
    fw = scan_false_ready_claims(ROOT)
    score = evaluate_release_readiness(write=True)
    out = {
        "firewall_ok": fw["ok"],
        "violations": fw["violations"],
        "scorecard_ok": score["ok"],
        "earned_tokens": score.get("earned_tokens"),
        "missing_lanes": score.get("missing_lanes"),
        "physical_execution_freeze": True,
    }
    print(json.dumps(out, indent=2))
    if not fw["ok"] or not score["ok"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
