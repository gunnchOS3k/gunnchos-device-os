"""gunnchAI3k tutor integration — EVT-1 alpha."""
from __future__ import annotations


def tutor_session_start(profile: str, topic: str) -> dict:
    return {
        "started": True,
        "profile": profile,
        "topic": topic,
        "safety": "ai_suggests_human_verifies",
        "pii_collection": False,
        "mock": True,
    }


def tutor_safety_check(response: str) -> dict:
    blocked_patterns = ("password", "api_key", "exploit")
    flagged = any(p in response.lower() for p in blocked_patterns)
    return {"safe_to_show": not flagged, "requires_educator_review": flagged, "mock": True}
