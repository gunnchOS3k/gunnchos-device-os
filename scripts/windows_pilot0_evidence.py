#!/usr/bin/env python3
"""Windows Pilot 0 classification/evidence for gunnchos-device-os.

Host OS product path is NOT Windows Pilot 0 applicable.
Optional Windows-facing docs/tooling is classified separately and does not
convert Device OS host into WINDOWS_NATIVE_DESKTOP PASS.
"""
from __future__ import annotations

import json
import os
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports" / "windows_pilot0"


def head_sha() -> str:
    env_sha = (os.environ.get("GITHUB_SHA") or "").strip()
    if env_sha:
        return env_sha
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    sha = head_sha()
    strategy = ROOT / "docs" / "WINDOWS_FIRST_STRATEGY.md"
    evidence = {
        "schema": "gunnchos.windows_pilot0.evidence.v1",
        "product": "gunnchos-device-os",
        "classification": "WINDOWS_NOT_APPLICABLE",
        "tooling_classification": "WINDOWS_DEV_TOOLING_ONLY",
        "generated_at_utc": datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "head_sha": sha,
        "head_sha12": sha[:12],
        "claim": "WINDOWS_PILOT0_NOT_APPLICABLE",
        "skipped_required_checks": 0,
        "checks": {
            "host_os_windows_pilot": {
                "status": "NOT_APPLICABLE",
                "detail": "Device OS host/guest target is not a Windows consumer desktop Pilot 0 product",
            },
            "windows_first_strategy_doc": {
                "status": "PRESENT" if strategy.is_file() else "ABSENT",
                "path": str(strategy),
            },
            "windows_tooling_runtime": {
                "status": "NOT_RUN",
                "detail": "No separate Windows host tooling package claimed for Pilot 0 PASS",
            },
        },
        "runner": {
            "note": "Classification evidence may be produced off Windows; host claim is NOT_APPLICABLE",
            "platform_system": platform.system(),
            "image_os": os.environ.get("ImageOS"),
            "image_version": os.environ.get("ImageVersion"),
        },
        "WINDOWS_PILOT0_ACCEPTED_MAIN_PASS": False,
        "non_claims": [
            "Does not claim Device Lab current-pin revalidation",
            "Does not claim physical Device Quartet",
            "Does not treat Windows strategy docs as Windows product PASS",
        ],
    }
    (REPORTS / "WINDOWS_PILOT0_EVIDENCE.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (REPORTS / "WINDOWS_PILOT0_EVIDENCE.md").write_text(
        "# Windows Pilot 0 — gunnchos-device-os\n\n"
        "- claim: `WINDOWS_PILOT0_NOT_APPLICABLE` (host)\n"
        "- tooling: `WINDOWS_DEV_TOOLING_ONLY` (no Pilot 0 PASS inferred)\n"
    )
    print(json.dumps({"claim": evidence["claim"], "sha12": sha[:12]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
