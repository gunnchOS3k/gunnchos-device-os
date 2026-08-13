"""gunnchAI3k tutor integration — EVT-1 alpha with digital safety gates."""
from __future__ import annotations

from typing import Any


INJECTION_MARKERS = (
    "ignore previous instructions",
    "ignore all previous",
    "system:",
    "<tool>",
    "exfiltrate",
    "disable safety",
)

BLOCKED_RESPONSE_PATTERNS = ("password", "api_key", "exploit", "private_key")

CLAIM_BOUNDARY = (
    "Digital tutor safety gates + local reply templates. "
    "Not production LLM deployment, not frontier model quality."
)


def tutor_session_start(profile: str, topic: str) -> dict:
    return {
        "started": True,
        "profile": profile,
        "topic": topic,
        "safety": "ai_suggests_human_verifies",
        "pii_collection": False,
        "runtime": "local_template",
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def tutor_safety_check(response: str) -> dict:
    flagged = any(p in response.lower() for p in BLOCKED_RESPONSE_PATTERNS)
    return {
        "safe_to_show": not flagged,
        "requires_educator_review": flagged,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
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
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    return {
        "ok": True,
        "denied": False,
        "reason": None,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def tutor_local_reply(
    *,
    topic: str,
    prompt: str,
    waike_lesson: str | None = None,
) -> dict[str, Any]:
    """Deterministic local tutoring reply (template) — not an LLM quality claim."""
    lesson_bit = f" Bound to WAIKE lesson `{waike_lesson}`." if waike_lesson else ""
    topic_l = (topic or "").lower()
    if "ofdm" in topic_l or "ofdm" in (prompt or "").lower():
        text = (
            "OFDM splits a wide channel into many narrow, orthogonal subcarriers so "
            "each carries a lower-rate stream that is more robust to multipath. "
            "A cyclic prefix helps absorb delay spread. Verify with a lab spectrum "
            f"plot and an educator checklist.{lesson_bit}"
        )
    elif "python" in topic_l or "code" in (prompt or "").lower():
        text = (
            "Start with a minimal function, add a type hint, write one pytest, then "
            "package the artifact under dist/ for gunnchSDK install dogfood. "
            f"AI suggests; you verify.{lesson_bit}"
        )
    else:
        text = (
            f"Topic `{topic}`: read the offline pack summary, attempt the lab check, "
            "then ask a clarifying question. gunnchAI provides a local hint only; "
            f"a human verifies correctness.{lesson_bit}"
        )
    return {
        "ok": True,
        "text": text,
        "source": "local_template",
        "prompt_echo": prompt,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
