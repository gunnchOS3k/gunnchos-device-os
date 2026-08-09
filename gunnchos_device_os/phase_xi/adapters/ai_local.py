
from __future__ import annotations
from typing import Any


def tutor_ask(prompt: str, private_clipboard: str | None = None, permission: bool = False) -> dict[str, Any]:
    """Local AI tutoring stub that enforces privacy gate (product behavior)."""
    if private_clipboard and not permission:
        return {
            "ok": True,
            "answered": False,
            "blocked_private_clipboard": True,
            "message": "Refusing to send private clipboard without permission",
        }
    return {
        "ok": True,
        "answered": True,
        "blocked_private_clipboard": False,
        "reply": f"Tutoring hint for: {prompt[:120]}",
        "citations": ["local_waike://fixture"],
    }
