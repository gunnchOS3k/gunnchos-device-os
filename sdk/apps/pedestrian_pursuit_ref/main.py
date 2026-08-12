#!/usr/bin/env python3
"""First-party game package — validates real PACKAGE_MANIFEST (not a stub)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GUNNCHOS_REPO_ROOT", Path(__file__).resolve().parents[3]))
manifest_path = ROOT / "packages/first_party_games/pedestrian-pursuit/PACKAGE_MANIFEST.json"


def main() -> int:
    if not manifest_path.exists():
        print(json.dumps({"ok": False, "error": "package_manifest_missing"}))
        return 1
    pkg = json.loads(manifest_path.read_text(encoding="utf-8"))
    ok = (
        pkg.get("schema") == "gunnchos.first_party_game_package.v1"
        and pkg.get("stub_content") is False
        and bool(pkg.get("source_repo"))
        and bool(pkg.get("accepted_sha"))
    )
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    out = data_dir / "pedestrian_pursuit_ref.json"
    payload = {"ok": ok, "package": pkg, "stub_content": False}
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": ok, "app_id": "gunnchos.pedestrian_pursuit", "stub_content": False, "wrote": str(out)}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
