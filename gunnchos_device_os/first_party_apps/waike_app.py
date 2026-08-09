"""WAIKE Learning application — uses real offline packs + progress."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import time

from gunnchos_device_os.waike_integration import run_session, list_offline_lessons, deploy_lesson

CLAIM_BOUNDARY = (
    "Digital WAIKE Learning app using repo lesson packs and progress store. "
    "Not a full LMS or production cloud sync."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_waike_app(*, role: str = "learner", lesson_id: str = "wireless_basics_101") -> dict[str, Any]:
    profile = "student" if role == "learner" else "educator"
    session = run_session(profile=profile, lesson_id=lesson_id)
    deploy = deploy_lesson(lesson_id, profile)
    ui = _repo_root() / "apps/waike_learning/index.html"
    portfolio = {
        "schema": "waike.portfolio.v1",
        "lesson_id": lesson_id,
        "role": role,
        "exported_at": time.time(),
        "session_ok": bool(session.get("ok")),
    }
    return {
        "ok": bool(session.get("ok")) and ui.exists(),
        "app_id": "waike",
        "entry": "apps/waike_learning/index.html",
        "lessons": list_offline_lessons(),
        "session": session,
        "deploy": deploy,
        "portfolio": portfolio,
        "accessibility": {"high_contrast_supported": True, "roles": ["learner", "educator"]},
        "ui_present": ui.exists(),
        "mock": False,
        "stub_content": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
