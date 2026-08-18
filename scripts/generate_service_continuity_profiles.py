#!/usr/bin/env python3
"""Generate RQ1 service-continuity profiles from existing Device OS code."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.service_continuity import write_bundle  # noqa: E402


def main() -> int:
    bundle = write_bundle(ROOT / "artifacts" / "supervisor_ready")
    print(f"wrote={bundle.get('_written')}")
    print(f"digest={bundle['content_digest_sha256']}")
    print(f"classes={bundle['research_classes']}")
    print(json.dumps({k: v["continuity_levels_observed"] for k, v in bundle["profiles"].items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
