#!/usr/bin/env python3
"""Verify launcherContract.json matches export_launcher_contract.py output."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apps" / "launcher_mock" / "src" / "generated" / "launcherContract.json"
EXPORT = ROOT / "scripts" / "export_launcher_contract.py"


def _semantic_contract(raw: str) -> dict:
    data = json.loads(raw)
    data.pop("generated_at", None)
    return data


def main() -> int:
    if not CONTRACT.exists():
        print(f"Missing {CONTRACT}. Run: python3 scripts/export_launcher_contract.py")
        return 1

    before = _semantic_contract(CONTRACT.read_text(encoding="utf-8"))
    rc = subprocess.call([sys.executable, str(EXPORT)], cwd=ROOT)
    if rc != 0:
        return rc
    after = _semantic_contract(CONTRACT.read_text(encoding="utf-8"))
    if before != after:
        print("launcherContract.json is out of date. Commit regenerated file.")
        return 1

    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    for key in ("version", "apps", "modes", "media_apps", "campus_native_apps"):
        if key not in data:
            print(f"Contract missing required key: {key}")
            return 1
    for app_id in ("files", "notes"):
        if app_id not in data["apps"]:
            print(f"Contract missing app: {app_id}")
            return 1
    print("launcherContract.json is up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
