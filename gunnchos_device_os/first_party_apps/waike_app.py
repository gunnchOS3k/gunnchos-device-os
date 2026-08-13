"""WAIKE Learning application — 18-course seeds + offline packs + progress.

Companion contract (do not regress): ``run_waike_app(lesson_id=..., role=...)`` remains
the entry used by ``/api/waike/start`` on PLATFORM-001. Extra kwargs (``course_id``)
are optional. Invalid course tokens fail closed.

Claim boundary: digitally executable course *seeds*, not full curriculum, not HUMAN_E6.
"""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.first_party_apps import runtime
from gunnchos_device_os.gunnchai_integration import (
    tutor_prompt_guard,
    tutor_safety_check,
    tutor_session_start,
)
from gunnchos_device_os.waike_curriculum.catalog import COURSE_IDS, course_by_id, resolve_course_id
from gunnchos_device_os.waike_curriculum.content import seed_for
from gunnchos_device_os.waike_curriculum.labs import run_lab
from gunnchos_device_os.waike_integration import (
    deploy_lesson,
    list_offline_lessons,
    list_progress,
    run_session,
)

CLAIM_BOUNDARY = (
    "Digital WAIKE Learning app with 18 distinct course seeds (lesson/lab/packets) "
    "plus gunnchSDK sandbox progress. Not a full LMS, not complete 8-week authorship, "
    "not production cloud sync, not student-validated pedagogy."
)

REQUIRED_PERMISSIONS = ["storage_read", "storage_write", "ai_interface"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _progress_path(data_dir: Path) -> Path:
    return data_dir / "waike_progress.json"


def _portfolio_path(data_dir: Path) -> Path:
    return data_dir / "waike_portfolio.json"


def _state_path(data_dir: Path) -> Path:
    return data_dir / "waike_app_state.json"


def _load_lesson_markdown(course_id: str) -> str | None:
    path = _repo_root() / "content/waike/courses" / course_id / "lesson.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return seed_for(course_id)["lesson"]


def _tutor_for_course(course_id: str, role: str) -> dict[str, Any]:
    seed = seed_for(course_id)
    session = tutor_session_start("student" if role == "learner" else "educator", course_id)
    guard = tutor_prompt_guard(seed["tutor_prompt"])
    if not guard.get("ok"):
        return {"ok": False, "session": session, "guard": guard, "reply": None}
    reply = seed["tutor_reply"]
    safety = tutor_safety_check(reply)
    return {
        "ok": bool(safety.get("safe_to_show")),
        "session": session,
        "guard": guard,
        "safety": safety,
        "reply": reply if safety.get("safe_to_show") else None,
        "prompt": seed["tutor_prompt"],
        "course_id": course_id,
        "offline": True,
        "claim_boundary": "Local tutor wording only — not curriculum completeness or model quality.",
    }


def run_waike_app(
    *,
    role: str = "learner",
    lesson_id: str = "wireless_basics_101",
    course_id: str | None = None,
    account: str = "dev-student",
    advance_pct: float | None = None,
    crash_probe: bool = False,
    run_course_lab: bool = True,
) -> dict[str, Any]:
    runtime.intentional_crash_probe(enabled=crash_probe)
    perms = runtime.assert_permissions(REQUIRED_PERMISSIONS)
    if not perms["ok"]:
        return {
            "ok": False,
            "app_id": "waike",
            "error": "permission_denied",
            "permissions": perms,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    token = course_id or lesson_id
    try:
        resolved = resolve_course_id(token)
    except KeyError:
        return {
            "ok": False,
            "app_id": "waike",
            "error": "unknown_course",
            "lesson_id": lesson_id,
            "course_id": course_id,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    data_dir = runtime.sandbox_data_dir()
    ui = _repo_root() / "apps/waike_learning/index.html"
    progress_file = _progress_path(data_dir)
    app_state = runtime.load_json(
        _state_path(data_dir),
        {"schema": "gunnchos.waike_app.state.v1", "sessions_completed": 0, "last_lesson": None},
    )

    prior = runtime.load_json(progress_file, {})
    prior_key = f"{account}:{lesson_id}"
    prior_pct = float((prior.get(prior_key) or {}).get("pct") or 0.0)
    if advance_pct is None:
        target_pct = min(100.0, prior_pct + 25.0 if prior_pct else 25.0)
    else:
        target_pct = float(advance_pct)

    if prior:
        runtime.write_json(progress_file, prior)

    session_lesson = lesson_id if lesson_id in list_offline_lessons() else resolved
    session = run_session(
        profile="student" if role == "learner" else "educator",
        lesson_id=session_lesson,
        role="student" if role == "learner" else "educator",
        account=account,
        persistence_path=str(progress_file),
    )
    if session.get("ok"):
        from gunnchos_device_os import waike_integration as wi

        marked = wi._STORE.mark(account, lesson_id, pct=target_pct, role=role)
        session["session"]["progress"] = marked

    deploy = deploy_lesson(
        session_lesson,
        "student" if role == "learner" else "educator",
    )

    spec = course_by_id(resolved)
    lesson_body = _load_lesson_markdown(resolved)
    tutor = _tutor_for_course(resolved, role)
    lab = run_lab(resolved) if run_course_lab else None

    app_state["sessions_completed"] = int(app_state.get("sessions_completed") or 0) + 1
    app_state["last_lesson"] = lesson_id
    app_state["last_course_id"] = resolved
    app_state["last_role"] = role
    app_state["updated_at"] = time.time()
    state_path = runtime.write_json(_state_path(data_dir), app_state)

    portfolio = {
        "schema": "waike.portfolio.v1",
        "lesson_id": lesson_id,
        "course_id": resolved,
        "role": role,
        "account": account,
        "exported_at": time.time(),
        "session_ok": bool(session.get("ok")),
        "progress_pct": target_pct,
        "tutor_ok": bool(tutor.get("ok")),
        "lab_ok": bool(lab and lab.get("ok")),
        "artifact": spec.title,
        "lessons_available": list_offline_lessons(),
        "course_ids": list(COURSE_IDS),
        "full_curriculum_complete": False,
    }
    portfolio_path = runtime.write_json(_portfolio_path(data_dir), portfolio)
    log_path = runtime.append_app_log(
        "waike_learning_run",
        {
            "lesson_id": lesson_id,
            "course_id": resolved,
            "role": role,
            "progress_pct": target_pct,
            "sessions_completed": app_state["sessions_completed"],
            "tutor_ok": tutor.get("ok"),
            "lab_ok": bool(lab and lab.get("ok")),
        },
    )

    result = {
        "ok": bool(session.get("ok")) and ui.exists() and perms["ok"] and bool(tutor.get("ok")),
        "app_id": "waike",
        "sdk_app_id": runtime.app_id(),
        "sdk_version": runtime.app_version(),
        "entry": "apps/waike_learning/index.html",
        "lessons": list_offline_lessons(),
        "course_id": resolved,
        "course_title": spec.title,
        "lesson_body": lesson_body,
        "assignment": seed_for(resolved)["assignment"],
        "lab": lab,
        "session": session,
        "deploy": deploy,
        "portfolio": portfolio,
        "portfolio_path": portfolio_path,
        "progress_listing": list_progress(),
        "gunnchai_tutor": tutor,
        "accessibility": {
            "high_contrast_supported": True,
            "roles": ["learner", "educator"],
            "captions": True,
        },
        "permissions": perms,
        "persisted_state_path": state_path,
        "persisted_progress_path": str(progress_file),
        "persisted_sessions_completed": app_state["sessions_completed"],
        "persisted_progress_pct": target_pct,
        "app_log_path": log_path,
        "ui_present": ui.exists(),
        "mock": False,
        "stub_content": False,
        "depth_claim": "D5_runtime_candidate",
        "full_curriculum_complete": False,
        "HUMAN_E6": False,
        "STUDENT_VALIDATED": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "owner_functions": [
            "eighteen_course_register",
            "lesson_body",
            "offline_pack_deploy",
            "executable_course_lab",
            "lab_session",
            "progress_persist",
            "portfolio_export",
            "learner_educator_roles",
            "accessibility_flags",
            "gunnchai_lesson_tutor",
        ],
        "not_claimed": [
            "full_waike_curriculum",
            "production_lms",
            "cloud_sync",
            "student_validated_pedagogy",
            "HUMAN_E6",
        ],
    }
    runtime.write_json(data_dir / "waike_learning_run.json", result)
    return result
