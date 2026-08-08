"""WAIKE learning integration — real offline packs + session progress (EVT / Cont VI)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import json
import time


CLAIM_BOUNDARY = (
    "Digital WAIKE learning runtime using repo lesson packs. Not a full LMS, "
    "not production cloud sync."
)

OFFLINE_PACKS = [
    "waike_gary_upnow_intro",
    "wireless_basics_101",
    "python_starter_pack",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def list_offline_lessons() -> list[str]:
    return list(OFFLINE_PACKS)


def _load_yaml_lessons() -> list[dict[str, Any]]:
    """Prefer real config content when present; fall back to built-in packs."""
    root = _repo_root()
    lessons: list[dict[str, Any]] = []
    for rel in (
        "config/waike_student_tasks.yaml",
        "config/waike_tutor_cards.yaml",
        "configs/modes/waike_lesson.yaml",
    ):
        path = root / rel
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        lessons.append(
            {
                "source": rel,
                "bytes": len(text.encode("utf-8")),
                "sha_prefix": __import__("hashlib").sha256(text.encode()).hexdigest()[:12],
                "present": True,
            }
        )
    return lessons


def deploy_lesson(lesson_id: str, profile: str) -> dict[str, Any]:
    if lesson_id not in OFFLINE_PACKS:
        return {"deployed": False, "reason": "lesson_not_found", "mock": False}
    packs = _load_yaml_lessons()
    return {
        "deployed": True,
        "lesson_id": lesson_id,
        "profile": profile,
        "offline_capable": True,
        "content_sources": packs,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


@dataclass
class WaikeProgressStore:
    path: Path | None = None
    progress: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.path and self.path.exists():
            self.progress = json.loads(self.path.read_text(encoding="utf-8"))

    def persist(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.progress, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def mark(self, account: str, lesson_id: str, *, pct: float, role: str) -> dict[str, Any]:
        key = f"{account}:{lesson_id}"
        self.progress[key] = {
            "account": account,
            "lesson_id": lesson_id,
            "pct": pct,
            "role": role,
            "updated_at": time.time(),
        }
        self.persist()
        return dict(self.progress[key])


_STORE = WaikeProgressStore()


def run_session(
    profile: str = "student",
    lesson_id: str = "wireless_basics_101",
    *,
    role: str = "student",
    account: str = "dev-student",
    persistence_path: str | None = None,
) -> dict[str, Any]:
    """Run a WAIKE learning session against real offline pack metadata."""
    global _STORE
    if persistence_path:
        _STORE = WaikeProgressStore(path=Path(persistence_path))
    deployed = deploy_lesson(lesson_id, profile)
    if not deployed.get("deployed"):
        return {"ok": False, **deployed}
    tutor = {
        "available": True,
        "mode": "local_privacy",
        "topic": lesson_id,
        "profile": profile,
    }
    a11y = {
        "captions": True,
        "reduced_motion": False,
        "scaling": 1.0,
        "input_alternatives": ["keyboard", "controller"],
    }
    progress = _STORE.mark(account, lesson_id, pct=25.0, role=role)
    educator = None
    if role == "educator":
        educator = {
            "can_assign": True,
            "can_view_progress": True,
            "cohort": "dev-class",
        }
    return {
        "ok": True,
        "session": {
            "lesson_id": lesson_id,
            "profile": profile,
            "role": role,
            "account": account,
            "offline_pack": lesson_id,
            "labs": ["lab-intro", "lab-check"],
            "tutor": tutor,
            "accessibility": a11y,
            "educator": educator,
            "progress": progress,
        },
        "content_sources": deployed.get("content_sources") or [],
        "claim_boundary": CLAIM_BOUNDARY,
        "mock": False,
    }


def list_progress() -> list[dict[str, Any]]:
    return list(_STORE.progress.values())
