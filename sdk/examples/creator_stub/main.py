#!/usr/bin/env python3
"""gunnchSDK example app: Creator Studio stub.

Real (if minimal) behavior: creates a project file inside the sandboxed
data directory the installer/runner assign this app, then reports its
contents. This is the smallest honest stand-in for the real Creator/Coder
first-party app validating the package/install/run pipeline end to end.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    project_name = sys.argv[1] if len(sys.argv) > 1 else "untitled_project"
    project = {
        "project_name": project_name,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "app_id": os.environ.get("GUNNCHOS_APP_ID"),
        "app_version": os.environ.get("GUNNCHOS_APP_VERSION"),
    }
    out_path = data_dir / f"{project_name}.project.json"
    out_path.write_text(json.dumps(project, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "wrote": str(out_path), "project": project}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
