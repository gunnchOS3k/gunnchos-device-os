#!/usr/bin/env python3
"""Generate Wave 002 engineering evidence artifact."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.shell.coordinator import Wave002ShellCoordinator  # noqa: E402


def main() -> int:
    out_dir = ROOT / "artifacts/engineering_wave002"
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "runtime_work"
    coord = Wave002ShellCoordinator(work)
    slices = {}
    for ff in ("handheld", "student_14_5", "ds_xl", "docked"):
        slices[ff] = coord.run_vertical_slice(ff)
    classification = coord.classify_requirements()
    pass_count = sum(1 for v in classification.values() if v["status"] == "PASS")
    partial_count = sum(1 for v in classification.values() if v["status"] == "PARTIAL")
    result = {
        "schema": "gunnchos.engineering_wave002.v1",
        "wave": "002",
        "primary_repo": "gunnchos-device-os",
        "branch": "eng/wave002-shell-continuity",
        "requirement_classification": classification,
        "pass_count": pass_count,
        "partial_count": partial_count,
        "fail_count": sum(1 for v in classification.values() if v["status"] == "FAIL"),
        "target_requirements": 14,
        "vertical_slices": slices,
        "coordinator_status": coord.status(),
        "claim_flags": coord.status()["claim_flags"],
        "impl_open_baseline_post_field_kit_92": 123,
        "DO_NOT_UPDATE_BASELINE_COUNTS": True,
    }
    result_path = out_dir / "WAVE002_RESULT.json"
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "path": str(result_path), "pass": pass_count, "partial": partial_count}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
