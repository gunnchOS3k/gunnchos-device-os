"""Mock rollback to known-good version."""
from __future__ import annotations

KNOWN_GOOD = ["0.0.9-evt0", "0.1.0-evt1-alpha"]


def rollback_to(version: str) -> dict:
    if version not in KNOWN_GOOD:
        return {"success": False, "reason": "version_not_in_known_good_list"}
    return {"success": True, "restored_version": version, "mock": True}
