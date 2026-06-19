"""Mock signed update model — no real update server."""
from __future__ import annotations

MANIFEST = {
    "version": "0.1.0-evt1-alpha",
    "signed": "PLACEHOLDER_SIGNATURE_REQUIRES_ENGINEERING_REVIEW",
    "channel": "evt-alpha",
    "staged_rollout_percent": 10,
}


def check_for_update(current: str) -> dict:
    latest = MANIFEST["version"]
    return {
        "current": current,
        "latest": latest,
        "update_available": current != latest,
        "signed": MANIFEST["signed"],
        "channel": MANIFEST["channel"],
    }
