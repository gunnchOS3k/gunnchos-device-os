#!/usr/bin/env python3
"""Run one or all WAIKE course labs (digitally executable)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.waike_curriculum.catalog import COURSE_IDS  # noqa: E402
from gunnchos_device_os.waike_curriculum.labs import run_all_labs, run_lab  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--course", choices=list(COURSE_IDS), default=None)
    args = parser.parse_args()
    payload = run_lab(args.course) if args.course else run_all_labs()
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
