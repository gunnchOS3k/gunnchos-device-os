#!/usr/bin/env python3
"""Live repo-linked lab for SEVEN_GC_APPRENTICESHIP — 7GC AI-RAN Research Apprenticeship.

Not a renamed template: solver is `lab_seven_gc_apprenticeship` in
gunnchos_device_os/waike_curriculum/labs.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.waike_curriculum.labs import run_lab  # noqa: E402

COURSE_ID = "SEVEN_GC_APPRENTICESHIP"


def main() -> int:
    out = run_lab(COURSE_ID)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
