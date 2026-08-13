#!/usr/bin/env python3
"""Materialize 18-course seeds + WAIKE_COURSE_REGISTER.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.waike_curriculum.register import build_register  # noqa: E402


def main() -> int:
    payload = build_register(ROOT)
    counts = payload["counts"]
    print(
        json.dumps(
            {
                "ok": counts["course_complete"] == 0
                and counts["catalog"] == 18
                and not payload["S0_open"],
                "register": "artifacts/waike/WAIKE_COURSE_REGISTER.json",
                "product_real_seed": counts["product_real_seed"],
                "product_templated": counts["product_templated"],
                "owner_templated_or_near": counts["owner_templated_or_near"],
                "owner_stub": counts["owner_stub"],
                "S0_open": payload["S0_open"],
                "S1_open": payload["S1_open"],
                "full_curriculum_complete": payload["full_curriculum_complete"],
                "HUMAN_E6": payload["HUMAN_E6"],
                "STUDENT_VALIDATED": payload["STUDENT_VALIDATED"],
            },
            indent=2,
        )
    )
    return 0 if counts["catalog"] == 18 and not payload["S0_open"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
