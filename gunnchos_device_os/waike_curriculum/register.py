"""Build artifacts/waike/WAIKE_COURSE_REGISTER.json (18 rows)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.waike_curriculum.auditor import audit_all
from gunnchos_device_os.waike_curriculum.catalog import COURSE_IDS, OWNER_REPO
from gunnchos_device_os.waike_curriculum.writer import write_all


CLAIM_BOUNDARY = (
    "18-course WAIKE *seed* depth on device-os: distinct executable lesson/lab/"
    "packet artifacts per accepted course ID. Not a finished 8-week curriculum, "
    "not HUMAN_E6, not STUDENT_VALIDATED, not owner-repo authorship complete."
)


def build_register(root: Path) -> dict[str, Any]:
    write_all(root)
    audit = audit_all(root)
    rows = audit["courses"]
    residual = {
        "FULL_8_WEEK_AUTHORSHIP": "OPEN",
        "SLIDE_PIXEL_DECKS": "OPEN",
        "FRONTIER_GUNNCHAI_MODEL": "OPEN",
        "DEVICE_LAB_CLASSROOM_PIXELS": "OPEN",
        "STUDENT_PILOT": "OPEN",
        "OWNER_REPO_PROGRAMS_STILL_TEMPLATED_OR_STUB": "OPEN",
        "HUMAN_E6": "NOT_EARNED",
        "STUDENT_VALIDATED": False,
    }
    payload = {
        "schema": "waike.course_register.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "owner_truth": {
            "repo": OWNER_REPO,
            "index": "programs/00_program_index.md",
            "accepted_course_ids": list(COURSE_IDS),
            "accepted_course_count": len(COURSE_IDS),
            "note": (
                "IDs match waike-research-ops program files + charter WAIKE_COURSE_* "
                "children. Index lists 12 flagship shells; six more program files exist as stubs."
            ),
        },
        "HUMAN_E6": False,
        "STUDENT_VALIDATED": False,
        "full_curriculum_complete": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "counts": audit["counts"],
        "similarity": audit["similarity"],
        "S0_open": audit["S0_open_courses"],
        "S1_open": audit["S1_open_courses"],
        "residual_open": residual,
        "courses": rows,
    }
    out = root / "artifacts/waike/WAIKE_COURSE_REGISTER.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    return payload
