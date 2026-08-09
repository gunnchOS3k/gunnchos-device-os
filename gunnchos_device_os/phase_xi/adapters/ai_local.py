from __future__ import annotations

import os
from typing import Any


def tutor_ask(prompt: str, private_clipboard: str | None = None, permission: bool = False) -> dict[str, Any]:
    """Phase XI entrypoint.

    When REAL_APP_EXECUTION_MODE=ACTIVE, use Phase XII gunnchAI/llama.cpp path.
    Otherwise preserve behavioral privacy-gate stub (historical harness).
    """
    if os.environ.get("REAL_APP_EXECUTION_MODE", "").upper() in {"ACTIVE", "1", "TRUE"}:
        from gunnchos_device_os.phase_xii.apps.ai import tutor_ask as real_ask

        return real_ask(prompt, private_clipboard=private_clipboard, permission=permission)

    if private_clipboard and not permission:
        return {
            "ok": True,
            "answered": False,
            "blocked_private_clipboard": True,
            "message": "Refusing to send private clipboard without permission",
            "VALID_AS_BEHAVIORAL_HARNESS": True,
            "NOT_YET_REAL_APP_PROVEN": True,
        }
    return {
        "ok": True,
        "answered": True,
        "blocked_private_clipboard": False,
        "reply": f"Tutoring hint for: {prompt[:120]}",
        "citations": ["local_waike://fixture"],
        "VALID_AS_BEHAVIORAL_HARNESS": True,
        "NOT_YET_REAL_APP_PROVEN": True,
        "stub": True,
    }
