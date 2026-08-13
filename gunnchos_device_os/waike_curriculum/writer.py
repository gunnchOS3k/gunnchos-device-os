"""Materialize per-course artifact directories (unique files, not a pack-ID list)."""

from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.waike_curriculum.catalog import CONTENT_ROOT_REL, COURSE_IDS, course_by_id
from gunnchos_device_os.waike_curriculum.content import assert_all_seeds, seed_for
from gunnchos_device_os.waike_curriculum.labs import FIXTURES, SOLVERS


LAB_PY_TEMPLATE = '''#!/usr/bin/env python3
"""Live repo-linked lab for {course_id} — {title}.

Not a renamed template: solver is `{solver}` in
gunnchos_device_os/waike_curriculum/labs.py.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.waike_curriculum.labs import run_lab  # noqa: E402

COURSE_ID = "{course_id}"


def main() -> int:
    out = run_lab(COURSE_ID)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
'''


def write_course(root: Path, course_id: str) -> Path:
    spec = course_by_id(course_id)
    seed = seed_for(course_id)
    cdir = root / CONTENT_ROOT_REL / course_id
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / "lesson.md").write_text(f"# {spec.title}\n\n{seed['lesson']}\n", encoding="utf-8")
    (cdir / "assignment.md").write_text(f"# Assignment — {spec.title}\n\n{seed['assignment']}\n", encoding="utf-8")
    (cdir / "group_project.md").write_text(
        f"# Group project — {spec.title}\n\n{seed['group_project']}\n", encoding="utf-8"
    )
    (cdir / "student_packet.md").write_text(
        f"# Student packet — {spec.title}\n\n{seed['student_packet']}\n", encoding="utf-8"
    )
    (cdir / "instructor_packet.md").write_text(
        f"# Instructor packet — {spec.title}\n\n{seed['instructor_packet']}\n", encoding="utf-8"
    )
    (cdir / "slides_outline.md").write_text(
        f"# Slides outline — {spec.title}\n\n{seed['slides']}\n\n"
        "VISUAL: no pixel deck in this packet.\n",
        encoding="utf-8",
    )
    (cdir / "portfolio.md").write_text(
        f"# Portfolio outputs — {spec.title}\n\n{seed['portfolio']}\n", encoding="utf-8"
    )
    (cdir / "assessment.json").write_text(
        json.dumps(
            {
                "schema": "waike.assessment.seed.v1",
                "course_id": course_id,
                "mastery_claimed": False,
                "items": seed["assessment"],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (cdir / "tutor_hook.json").write_text(
        json.dumps(
            {
                "schema": "waike.tutor_hook.v1",
                "course_id": course_id,
                "prompt": seed["tutor_prompt"],
                "local_reply": seed["tutor_reply"],
                "model_quality_claimed": False,
                "offline": True,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (cdir / "offline_pack.json").write_text(
        json.dumps(
            {
                "schema": "waike.offline_pack.v1",
                "course_id": course_id,
                "pack_id": f"{course_id}.seed.v1",
                "requires_network": False,
                "kinesthetic_hook": spec.kinesthetic_hook,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (cdir / "lab_manifest.json").write_text(
        json.dumps(
            {
                "schema": "waike.live_lab.v1",
                "course_id": course_id,
                "entrypoint": "lab.py",
                "solver": SOLVERS[course_id].__name__,
                "live_repo_path": f"gunnchos_device_os/waike_curriculum/labs.py::{SOLVERS[course_id].__name__}",
                "fixture": FIXTURES[course_id],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    # Unique first line per lab.py (solver name) so file hashes diverge.
    (cdir / "lab.py").write_text(
        LAB_PY_TEMPLATE.format(course_id=course_id, title=spec.title, solver=SOLVERS[course_id].__name__),
        encoding="utf-8",
    )
    return cdir


def write_all(root: Path) -> list[str]:
    assert_all_seeds()
    written = []
    for cid in COURSE_IDS:
        write_course(root, cid)
        written.append(cid)
    catalog = {
        "schema": "waike.course_catalog.ui.v1",
        "full_curriculum_complete": False,
        "courses": [
            {
                "course_id": cid,
                "title": course_by_id(cid).title,
                "kinesthetic_hook": course_by_id(cid).kinesthetic_hook,
                "lesson_excerpt": seed_for(cid)["lesson"].split("\n\n")[0],
                "worked_example": seed_for(cid)["tutor_reply"],
                "assignment": seed_for(cid)["assignment"],
                "lab_hint": course_by_id(cid).kinesthetic_hook,
            }
            for cid in COURSE_IDS
        ],
    }
    ui_path = root / "apps/waike_learning/courses.json"
    ui_path.write_text(json.dumps(catalog, indent=2) + "\n", encoding="utf-8")
    return written
