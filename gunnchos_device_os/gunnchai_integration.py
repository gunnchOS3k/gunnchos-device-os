"""gunnchAI3k tutor integration — EVT-1 alpha with digital safety gates.

Additive 17G.6 path: when the sibling product-service is reachable, prefer live
assist + provenance (Capability Broker equivalent on accepted-main product-service)
over local templates. Templates remain the offline fallback.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
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
    "Digital tutor safety gates + local reply templates + optional live "
    "gunnchAI product-service assist. Not production LLM deployment, not "
    "frontier model quality."
)

DEFAULT_PRODUCT_SERVICE_URL = "http://127.0.0.1:8791"


def product_service_base_url() -> str:
    return (
        os.environ.get("GUNNCHAI_PRODUCT_SERVICE_URL")
        or os.environ.get("GUNNCHAI_DEVICE_LAB_PRODUCT_SERVICE_URL")
        or DEFAULT_PRODUCT_SERVICE_URL
    ).rstrip("/")


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


def _http_json(
    method: str,
    url: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 45.0,
) -> tuple[int, dict[str, Any] | None, str | None]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            try:
                parsed = json.loads(body) if body else {}
            except json.JSONDecodeError:
                return int(resp.status), None, "invalid_json"
            return int(resp.status), parsed if isinstance(parsed, dict) else {"value": parsed}, None
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            parsed = {"raw": raw}
        return int(exc.code), parsed if isinstance(parsed, dict) else {"value": parsed}, f"http_{exc.code}"
    except Exception as exc:  # noqa: BLE001 — surface transport failures honestly
        return 0, None, f"{type(exc).__name__}:{exc}"


def product_service_health(base_url: str | None = None) -> dict[str, Any]:
    base = (base_url or product_service_base_url()).rstrip("/")
    status, body, err = _http_json("GET", f"{base}/health", timeout=5.0)
    return {
        "ok": status == 200 and isinstance(body, dict) and bool(body.get("ok", True)),
        "status": status,
        "body": body,
        "error": err,
        "base_url": base,
    }


def tutor_product_service_assist(
    *,
    prompt: str,
    topic: str,
    profile: str = "student",
    waike_lesson: str | None = None,
    capability: str = "tutoring",
    permissions: list[str] | None = None,
    base_url: str | None = None,
    purpose: str | None = None,
) -> dict[str, Any]:
    """Call accepted-main gunnchAI product-service assist with provenance.

    Provenance.modelId/backend/mechanism records provider choice for Device Lab
    Capability Broker checklist item without consuming CX #48 as release truth.
    """
    base = (base_url or product_service_base_url()).rstrip("/")
    query = prompt
    if waike_lesson:
        query = f"{prompt}\n\n[WAIKE lesson context: {waike_lesson}; read-only tutoring]"
    if topic:
        query = f"[topic={topic}; profile={profile}] {query}"
    payload: dict[str, Any] = {
        "capability": capability,
        "query": query,
        "purpose": purpose or "device_lab_gunnchai_tutor",
    }
    if permissions is not None:
        payload["permissions"] = permissions
    status, body, err = _http_json(
        "POST",
        f"{base}/v1/assist/{capability}",
        payload,
        timeout=60.0,
    )
    if err or not isinstance(body, dict):
        return {
            "ok": False,
            "source": "product_service",
            "error": err or "empty_body",
            "http_status": status,
            "base_url": base,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    provenance = body.get("provenance") if isinstance(body.get("provenance"), dict) else {}
    text = str(body.get("text") or "")
    return {
        "ok": bool(body.get("ok")) and bool(text),
        "text": text,
        "source": "product_service",
        "prompt_echo": prompt,
        "request_id": body.get("requestId") or provenance.get("requestId"),
        "provenance": provenance,
        "capability_broker_record": {
            "provider_choice_recorded": bool(
                provenance.get("backend") or provenance.get("modelId") or provenance.get("mechanism")
            ),
            "backend": provenance.get("backend"),
            "modelId": provenance.get("modelId"),
            "modelVersion": provenance.get("modelVersion"),
            "mechanism": provenance.get("mechanism"),
            "realInference": provenance.get("realInference"),
            "fallbackUsed": provenance.get("fallbackUsed"),
            "fallbackReason": provenance.get("fallbackReason"),
            "offline": provenance.get("offline"),
            "processingMode": provenance.get("processingMode"),
        },
        "governance": body.get("governance"),
        "structured": body.get("structured"),
        "http_status": status,
        "base_url": base,
        "raw_ok": body.get("ok"),
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }


def tutor_assist_prefer_live(
    *,
    topic: str,
    prompt: str,
    profile: str = "student",
    waike_lesson: str | None = None,
    require_live: bool = False,
) -> dict[str, Any]:
    """Prefer live product-service; fall back to local template unless require_live."""
    health = product_service_health()
    if health.get("ok"):
        live = tutor_product_service_assist(
            prompt=prompt,
            topic=topic,
            profile=profile,
            waike_lesson=waike_lesson,
        )
        if live.get("ok"):
            return {**live, "provider_path": "LIVE_PRODUCT_SERVICE", "health": health}
        if require_live:
            return {
                **live,
                "provider_path": "LIVE_PRODUCT_SERVICE_FAILED",
                "health": health,
            }
        fallback = tutor_local_reply(topic=topic, prompt=prompt, waike_lesson=waike_lesson)
        return {
            **fallback,
            "ok": True,
            "provider_path": "TEMPLATE_AFTER_LIVE_FAIL",
            "live_error": live,
            "health": health,
            "fallbackUsed": True,
            "fallbackReason": live.get("error") or "product_service_assist_failed",
        }
    if require_live:
        return {
            "ok": False,
            "source": "product_service",
            "error": "product_service_unreachable",
            "provider_path": "LIVE_REQUIRED_UNAVAILABLE",
            "health": health,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
    template = tutor_local_reply(topic=topic, prompt=prompt, waike_lesson=waike_lesson)
    return {
        **template,
        "provider_path": "LOCAL_TEMPLATE_OFFLINE",
        "health": health,
        "offline": True,
    }
