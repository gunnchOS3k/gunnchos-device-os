#!/usr/bin/env python3
"""Sync component stacks from hardware repo or use fixtures."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
OUT = ROOT / "results" / "component_stack_sync_report.json"
FIXTURE = ROOT / "configs" / "imported_component_stacks.yaml"
TARGET = ROOT / "configs" / "imported_component_stacks.yaml"


def load_yaml(path: Path) -> dict:
    try:
        import yaml
        return yaml.safe_load(path.read_text()) or {}
    except ImportError:
        return json.loads(path.read_text()) if path.suffix == ".json" else {}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hardware-repo", type=Path, default=None)
    ap.add_argument("--use-fixtures", action="store_true")
    args = ap.parse_args()

    report = {
        "sync_timestamp": datetime.now(timezone.utc).isoformat(),
        "fallback_used": False,
        "hardware_repo_present": False,
    }

    src = None
    if not args.use_fixtures and args.hardware_repo:
        hw = args.hardware_repo.resolve()
        candidate = hw / "component_selection/configs/device_stack_candidates.yaml"
        report["hardware_repo_path"] = str(args.hardware_repo)
        if candidate.exists():
            src = candidate
            report["hardware_repo_present"] = True

    if src:
        shutil.copy2(src, TARGET)
        report["source"] = str(src)
    else:
        report["fallback_used"] = True
        report["source"] = str(FIXTURE)
        if not TARGET.exists() and FIXTURE.exists():
            shutil.copy2(FIXTURE, TARGET)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
