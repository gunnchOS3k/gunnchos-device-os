#!/usr/bin/env python3
"""Real WAIKE Learning first-party package entry (not sdk/examples stub)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GUNNCHOS_REPO_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.first_party_apps.waike_app import run_waike_app  # noqa: E402


def main() -> int:
    result = run_waike_app()
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    out = data_dir / "waike_learning_run.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": bool(result.get("ok")), "app_id": "gunnchos.waike_learning", "stub_content": False, "wrote": str(out)}))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
