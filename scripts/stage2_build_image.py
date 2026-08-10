#!/usr/bin/env python3
"""Build Stage 2 reproducible system + recovery images."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main() -> int:
    from gunnchos_device_os.stage2.image_build import build_image

    result = build_image(repo_root=ROOT)
    print(json.dumps(result, indent=2))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
