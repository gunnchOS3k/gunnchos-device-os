"""gunnchAI3k tutor integration — EVT-1 alpha with digital safety gates."""
from __future__ import annotations


INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous",
    "system:",
    "<tool>",
    "exfiltrate",
    "disable safety",
)

BLOCKED_RESPONSE_PATTERNS = ("password", "api_key", "exploit", "private_key")


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
    flagged = any(p in response.lower() for p in BLOCKED_RESPONSE_PATTERNS)
    return {
        "safe_to_show": not flagged,
        "requires_educator_review": flagged,
        "mock": True,
    }


def tutor_prompt_guard(prompt: str) -> dict:
    """SEC-AI digital gate: reject obvious prompt/tool injection before tutoring."""
    lowered = (prompt or "").lower()
    hit = next((m for m in INJECTION_MARKERS if m in lowered), None)
    if hit:
        return {
            "ok": False,
            "denied": True,
            "reason": "prompt_injection_suspected",
            "marker": hit,
            "mock": True,
        }
    return {"ok": True, "denied": False, "reason": None, "mock": True}
