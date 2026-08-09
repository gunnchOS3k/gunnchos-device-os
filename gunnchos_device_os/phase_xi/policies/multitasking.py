from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MultitaskingPolicy:
    """Process priority + memory-pressure behavior. Never silently kill user work."""

    schema: str = "gunnchos.multitasking_policy.v1"
    foreground_nice: int = -5
    background_nice: int = 5
    media_nice: int = -2
    memory_warn_pct: float = 85.0
    memory_critical_pct: float = 95.0
    silent_kill_forbidden: bool = True
    protected_workloads: tuple[str, ...] = (
        "document_editor",
        "spreadsheet",
        "presentation",
        "ide",
        "terminal",
        "browser_tabs_active",
        "game_session",
        "ai_session",
        "sync_inflight",
    )
    stacks: dict[str, list[str]] = field(default_factory=lambda: {
        "document_music": ["document_editor", "music_player"],
        "pdf_music": ["pdf_viewer", "music_player"],
        "browser_ai": ["browser", "ai_tutor"],
        "document_messaging": ["document_editor", "messaging"],
        "video_document": ["video_player", "document_editor"],
        "videocall_document_browser": ["webrtc", "document_editor", "browser"],
        "ide_docs_ai": ["ide", "docs", "ai_tutor"],
        "game_voice": ["game", "voice"],
        "game_music_opt_in": ["game", "music_player"],
        "archive_local_ai": ["archive", "ai_tutor"],
    })

    def admit(self, stack_name: str, memory_pct: float) -> dict[str, Any]:
        apps = self.stacks.get(stack_name, [])
        if memory_pct >= self.memory_critical_pct:
            return {
                "ok": True,
                "action": "warn_and_shed_caches_only",
                "kill_user_work": False,
                "apps": apps,
                "message": "Memory critical: shedding caches; user work preserved",
            }
        if memory_pct >= self.memory_warn_pct:
            return {
                "ok": True,
                "action": "warn_user",
                "kill_user_work": False,
                "apps": apps,
            }
        return {"ok": True, "action": "admit", "kill_user_work": False, "apps": apps}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "foreground_nice": self.foreground_nice,
            "background_nice": self.background_nice,
            "media_nice": self.media_nice,
            "memory_warn_pct": self.memory_warn_pct,
            "memory_critical_pct": self.memory_critical_pct,
            "silent_kill_forbidden": self.silent_kill_forbidden,
            "protected_workloads": list(self.protected_workloads),
            "stacks": self.stacks,
        }
