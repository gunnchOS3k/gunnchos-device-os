#!/usr/bin/env python3
"""Run WP-007 digital red-team harness and write artifacts/wp007/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.security_red_team.harness import run_red_team  # noqa: E402


def main() -> int:
    report = run_red_team(write=True)
    summary = {
        "INTERNAL_RED_TEAM_READY": report["INTERNAL_RED_TEAM_READY"],
        "SECURITY_S0": report["SECURITY_S0"],
        "SECURITY_S1": report["SECURITY_S1"],
        "cases_passed": report["cases_passed"],
        "cases_total": report["cases_total"],
        "external_pentest": report["external_pentest"],
        "open_s0": report["open_s0"],
        "open_s1": report["open_s1"],
        "open_s2": report["open_s2"],
    }
    print(json.dumps(summary, indent=2))
    if report["SECURITY_S0"] or report["SECURITY_S1"]:
        return 1
    if not report["INTERNAL_RED_TEAM_READY"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
