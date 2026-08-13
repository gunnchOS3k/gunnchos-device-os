"""Detect templated/shallow WAIKE course seeds (pairwise 5-gram Jaccard + facet presence)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from gunnchos_device_os.waike_curriculum.catalog import (
    CONTENT_ROOT_REL,
    COURSE_IDS,
    FACETS,
    course_by_id,
)
from gunnchos_device_os.waike_curriculum.content import FORBIDDEN_PHRASES, seed_for
from gunnchos_device_os.waike_curriculum.labs import SOLVERS, run_lab

REQUIRED_ARTIFACTS = (
    "lesson.md",
    "assignment.md",
    "lab.py",
    "lab_manifest.json",
    "group_project.md",
    "student_packet.md",
    "instructor_packet.md",
    "slides_outline.md",
    "assessment.json",
    "portfolio.md",
    "tutor_hook.json",
    "offline_pack.json",
)

# S1 shallowness: indistinguishable courses. 0.35 is generous; seeds should sit far below.
SIMILARITY_S1 = 0.35
MIN_LESSON_CHARS = 280


def _ngrams(text: str, n: int = 5) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    if len(tokens) < n:
        return {" ".join(tokens)} if tokens else set()
    return {" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)}


def jaccard(a: str, b: str) -> float:
    sa, sb = _ngrams(a), _ngrams(b)
    if not sa and not sb:
        return 1.0
    inter = len(sa & sb)
    union = len(sa | sb)
    return inter / union if union else 0.0


def _course_blob(course_id: str) -> str:
    seed = seed_for(course_id)
    return "\n".join(
        [
            seed["lesson"],
            seed["assignment"],
            seed["student_packet"],
            seed["instructor_packet"],
            seed["slides"],
            seed["group_project"],
            SOLVERS[course_id].__name__,
        ]
    )


def pairwise_similarity() -> dict[str, Any]:
    blobs = {cid: _course_blob(cid) for cid in COURSE_IDS}
    worst = 0.0
    worst_pair = None
    pairs = []
    ids = list(COURSE_IDS)
    for i, a in enumerate(ids):
        for b in ids[i + 1 :]:
            sim = jaccard(blobs[a], blobs[b])
            pairs.append({"a": a, "b": b, "jaccard_5gram": round(sim, 4)})
            if sim > worst:
                worst = sim
                worst_pair = (a, b)
    pairs.sort(key=lambda r: r["jaccard_5gram"], reverse=True)
    return {
        "worst_jaccard": round(worst, 4),
        "worst_pair": list(worst_pair) if worst_pair else None,
        "s1_threshold": SIMILARITY_S1,
        "templated_cluster_detected": worst >= SIMILARITY_S1,
        "top_pairs": pairs[:8],
    }


def facet_status(course_id: str, root: Path) -> dict[str, str]:
    cdir = root / CONTENT_ROOT_REL / course_id
    present = {name: (cdir / name).exists() for name in REQUIRED_ARTIFACTS}
    seed = seed_for(course_id)
    lesson_ok = present["lesson.md"] and len(seed["lesson"]) >= MIN_LESSON_CHARS
    lab_ok = course_id in SOLVERS
    return {
        "lessons": "SEED" if lesson_ok else "MISSING",
        "assignments": "SEED" if present["assignment.md"] else "MISSING",
        "labs": "SEED_EXECUTABLE" if lab_ok else "MISSING",
        "live_repo_linked_labs": "LINKED" if lab_ok else "MISSING",
        "group_projects": "SEED" if present["group_project.md"] else "MISSING",
        "student_packets": "SEED" if present["student_packet.md"] else "MISSING",
        "instructor_packets": "SEED" if present["instructor_packet.md"] else "MISSING",
        "slide_instruction_media": "OUTLINE_ONLY" if present["slides_outline.md"] else "MISSING",
        "assessment_mastery": "SEED_QUIZ" if present["assessment.json"] else "MISSING",
        "portfolio_outputs": "SEED_SPEC" if present["portfolio.md"] else "MISSING",
        "live_gunnchai_tutoring": "HOOK_LOCAL_NOT_MODEL" if present["tutor_hook.json"] else "MISSING",
        "offline_use": "PACK_PRESENT" if present["offline_pack.json"] else "MISSING",
        "device_lab_use": "NOT_IN_THIS_PACKET",
    }


def audit_course(course_id: str, root: Path) -> dict[str, Any]:
    spec = course_by_id(course_id)
    seed = seed_for(course_id)
    lab = run_lab(course_id)
    facets = facet_status(course_id, root)
    blob = _course_blob(course_id).lower()
    forbidden_hits = [p for p in FORBIDDEN_PHRASES if p in blob]
    missing_facets = [f for f in FACETS if facets.get(f) in {"MISSING", None}]
    s0 = []
    s1 = []
    s2 = []
    if not lab.get("ok"):
        s0.append("LAB_NOT_EXECUTABLE")
    if forbidden_hits:
        s1.append({"code": "OWNER_TEMPLATE_PHRASE", "hits": forbidden_hits})
    if len(seed["lesson"]) < MIN_LESSON_CHARS:
        s1.append("LESSON_TOO_SHORT")
    if facets["slide_instruction_media"] == "OUTLINE_ONLY":
        s2.append("SLIDE_PIXELS_UNAVAILABLE")
    if facets["live_gunnchai_tutoring"] == "HOOK_LOCAL_NOT_MODEL":
        s2.append("TUTOR_NOT_FRONTIER_MODEL")
    s2.append("FULL_8_WEEK_AUTHORSHIP_OPEN")
    s2.append("STUDENT_PILOT_NOT_RUN")
    return {
        "course_id": course_id,
        "title": spec.title,
        "owner_program_file": spec.owner_program_file,
        "owner_content_class": spec.owner_content_class,
        "product_content_class": "REAL_SEED_EXECUTABLE",
        "course_complete": False,
        "engagement_readiness": "DIGITAL_SEED_NOT_COHORT_READY",
        "facets": facets,
        "missing_facets": missing_facets,
        "lab_executable": bool(lab.get("ok")),
        "lab_live_repo_path": lab.get("live_repo_path"),
        "lab_result_ok": bool(lab.get("ok")),
        "HUMAN_E6": False,
        "STUDENT_VALIDATED": False,
        "S0": len(s0),
        "S1": len(s1),
        "S2": len(s2),
        "open_s0": s0,
        "open_s1": s1,
        "open_s2": s2,
    }


def audit_all(root: Path) -> dict[str, Any]:
    sim = pairwise_similarity()
    courses = [audit_course(cid, root) for cid in COURSE_IDS]
    if sim["templated_cluster_detected"]:
        for row in courses:
            row["S1"] += 1
            row["open_s1"] = list(row["open_s1"]) + ["PAIRWISE_TEMPLATE_CLUSTER"]
    real = sum(1 for c in courses if c["product_content_class"] == "REAL_SEED_EXECUTABLE" and c["S1"] == 0)
    templated_owner = sum(1 for c in courses if c["owner_content_class"].startswith("TEMPLATED") or c["owner_content_class"] == "NEAR_TEMPLATE")
    stub_owner = sum(1 for c in courses if c["owner_content_class"] == "STUB_POINTER")
    s0_open = [c["course_id"] for c in courses if c["S0"]]
    s1_open = [c["course_id"] for c in courses if c["S1"]]
    return {
        "similarity": sim,
        "courses": courses,
        "counts": {
            "catalog": len(courses),
            "product_real_seed": real,
            "product_templated": len(courses) - real,
            "owner_templated_or_near": templated_owner,
            "owner_stub": stub_owner,
            "course_complete": 0,
        },
        "S0_open_courses": s0_open,
        "S1_open_courses": s1_open,
    }
