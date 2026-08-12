#!/usr/bin/env python3
"""Real Creator Studio first-party package entry (not sdk/examples stub)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GUNNCHOS_REPO_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.first_party_apps.creator_studio import run_creator_studio  # noqa: E402


def main() -> int:
    # Installer/runner does not inject permissions env; declare grant for dogfood.
    os.environ.setdefault(
        "GUNNCHOS_APP_PERMISSIONS",
        "storage_read,storage_write,ai_interface",
    )
    layout = "dsxl" if "--dsxl" in sys.argv else "single"
    crash = "--crash-probe" in sys.argv
    result = run_creator_studio(layout=layout, crash_probe=crash)
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    out = data_dir / "creator_studio_run.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": bool(result.get("ok")),
                "app_id": "gunnchos.creator_studio",
                "stub_content": False,
                "persisted_run_count": result.get("persisted_run_count"),
                "wrote": str(out),
            }
        )
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
