#!/usr/bin/env python3
"""Generate Wave 004 engineering evidence artifacts."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.platform.coordinator import Wave004PlatformCoordinator  # noqa: E402


def _git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    out_dir = ROOT / "artifacts/engineering_wave004"
    out_dir.mkdir(parents=True, exist_ok=True)
    coord = Wave004PlatformCoordinator(out_dir)
    validation = coord.run_full_validation()
    classification = validation["requirement_classification"]
    summary = {
        "validated": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTED_AND_VALIDATED"),
        "implemented_validation_open": sum(
            1 for v in classification.values() if v["classification"] == "IMPLEMENTED_VALIDATION_OPEN"
        ),
        "implementation_open": sum(1 for v in classification.values() if v["classification"] == "IMPLEMENTATION_OPEN"),
        "blocked_environment": sum(1 for v in classification.values() if v["classification"] == "BLOCKED_ENVIRONMENT"),
        "blocked_external": sum(1 for v in classification.values() if v["classification"] == "BLOCKED_EXTERNAL"),
        "total": len(classification),
    }
    head = _git_head()
    result = {
        "schema": "gunnchos.engineering_wave004.v1",
        "wave": "004",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "primary_repo": "gunnchos-device-os",
        "branch": "eng/wave004-platform-security",
        "head_sha": head,
        "target_requirements": 12,
        "summary": summary,
        "requirement_classification": classification,
        "e2e_scenarios": validation["e2e"],
        "security_injection": validation["security_injection"],
        "claim_flags": validation["claim_flags"],
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
        "wave004_ok": validation["ok"],
    }
    files = {
        "WAVE004_RESULT.json": result,
        "REQUIREMENT_RESULTS.json": {"requirements": classification, "summary": summary},
        "E2E_SCENARIOS_RESULT.json": validation["e2e"],
        "SECURITY_INJECTION_RESULT.json": validation["security_injection"],
        "CLAIM_BOUNDARIES.json": {"claim_flags": validation["claim_flags"]},
        "RUNTIME_STATUS.json": coord.status(),
    }
    for name, payload in files.items():
        (out_dir / name).write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": validation["ok"], "path": str(out_dir / "WAVE004_RESULT.json"), "summary": summary}, indent=2))
    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
