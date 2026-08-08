#!/usr/bin/env python3
"""Build + validate the DEV reproducible system image bundle."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.system_image import build_and_validate  # noqa: E402


def main() -> int:
    out = ROOT / "os_build" / "reproducible_system_image" / "artifacts"
    result = build_and_validate(out)
    report_dir = ROOT / "results" / "full_product"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "system_image_validation.json"
    report_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    validation = result["validation"]
    print(f"content_digest={result['build']['content_digest_sha256']}")
    print(f"ok={validation['ok']} token={validation.get('token')}")
    print(f"report={report_path}")
    return 0 if validation["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
