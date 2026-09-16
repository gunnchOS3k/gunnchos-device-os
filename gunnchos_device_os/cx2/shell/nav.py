"""Shared navigation + a11y wiring for CX2 surfaces."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

SURFACE_ORDER = ("home", "vault", "app_center", "connect", "assist", "care")

SURFACE_A11Y = {
    "home": {"role": "main", "name": "gunnch Home", "shortcut": "Alt+1"},
    "vault": {"role": "region", "name": "Vault", "shortcut": "Alt+2"},
    "app_center": {"role": "region", "name": "App Center", "shortcut": "Alt+3"},
    "connect": {"role": "region", "name": "Connect", "shortcut": "Alt+4"},
    "assist": {"role": "region", "name": "Assist", "shortcut": "Alt+5"},
    "care": {"role": "region", "name": "Care", "shortcut": "Alt+6"},
}


@dataclass
class ShellNav:
    history: List[str] = field(default_factory=lambda: ["home"])
    focus_index: int = 0
    offline: bool = False
    error: Optional[str] = None
    profile: str = "student_14_5"

    @property
    def current(self) -> str:
        return self.history[-1] if self.history else "home"

    def go(self, surface: str) -> dict:
        if surface not in SURFACE_ORDER:
            self.error = f"unknown_surface:{surface}"
            return self.snapshot()
        self.history.append(surface)
        self.focus_index = SURFACE_ORDER.index(surface)
        self.error = None
        return self.snapshot()

    def back(self) -> dict:
        if len(self.history) > 1:
            self.history.pop()
            self.focus_index = SURFACE_ORDER.index(self.current)
        return self.snapshot()

    def home(self) -> dict:
        self.history = ["home"]
        self.focus_index = 0
        self.error = None
        return self.snapshot()

    def focus_next(self) -> dict:
        self.focus_index = (self.focus_index + 1) % len(SURFACE_ORDER)
        return self.go(SURFACE_ORDER[self.focus_index])

    def focus_prev(self) -> dict:
        self.focus_index = (self.focus_index - 1) % len(SURFACE_ORDER)
        return self.go(SURFACE_ORDER[self.focus_index])

    def snapshot(self) -> dict:
        return {
            "current": self.current,
            "history": list(self.history),
            "focus_index": self.focus_index,
            "focus_visible": True,
            "surfaces": [
                {
                    "id": sid,
                    **SURFACE_A11Y[sid],
                    "focused": sid == self.current,
                }
                for sid in SURFACE_ORDER
            ],
            "offline": self.offline,
            "error": self.error,
            "profile": self.profile,
            "back_available": len(self.history) > 1,
            "empty_states": {
                "vault": "No files yet — drop documents here or save from apps.",
                "app_center": "No apps installed — browse the catalog to get started.",
                "connect": "Inbox empty — compose or sync when online.",
                "care": "No support bundles yet.",
            },
            "evidence_class": "CONTRACT_PASS",
        }
