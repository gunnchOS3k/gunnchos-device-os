"""NET-ORCH-031 — low-bandwidth adaptation."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.models import AdaptationMode


def select_adaptation_mode(
    *,
    available_kbps: float | None,
    emergency: bool = False,
    offline: bool = False,
) -> AdaptationMode:
    if offline or available_kbps is None or available_kbps <= 0:
        return AdaptationMode.OFFLINE if offline or (available_kbps is not None and available_kbps <= 0) else AdaptationMode.OFFLINE
    if emergency and available_kbps < 64.0:
        return AdaptationMode.EMERGENCY_MINIMAL
    if available_kbps < 32.0:
        return AdaptationMode.LOW_BANDWIDTH
    if available_kbps < 256.0:
        return AdaptationMode.REDUCED
    return AdaptationMode.FULL


def adapt_payload(mode: AdaptationMode, payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    if mode == AdaptationMode.FULL:
        out["quality"] = "full"
        return out
    if mode == AdaptationMode.REDUCED:
        out["quality"] = "reduced"
        out.pop("attachments", None)
        return out
    if mode == AdaptationMode.LOW_BANDWIDTH:
        return {"quality": "low", "text": str(out.get("text", ""))[:120]}
    if mode == AdaptationMode.EMERGENCY_MINIMAL:
        return {"quality": "emergency", "text": str(out.get("text", ""))[:40], "priority": "EMERGENCY"}
    return {"quality": "offline", "cached_only": True}


def prove_low_bandwidth_adaptation() -> dict[str, Any]:
    full = select_adaptation_mode(available_kbps=1000.0)
    low = select_adaptation_mode(available_kbps=20.0)
    emerg = select_adaptation_mode(available_kbps=10.0, emergency=True)
    off = select_adaptation_mode(available_kbps=0.0, offline=True)
    payload = {"text": "A" * 200, "attachments": ["img.png"]}
    adapted_low = adapt_payload(low, payload)
    adapted_full = adapt_payload(full, payload)
    ok = (
        full == AdaptationMode.FULL
        and low == AdaptationMode.LOW_BANDWIDTH
        and emerg == AdaptationMode.EMERGENCY_MINIMAL
        and off == AdaptationMode.OFFLINE
        and "attachments" not in adapted_low
        and adapted_full.get("attachments") == ["img.png"]
        and len(adapted_low.get("text", "")) <= 120
    )
    return {
        "schema": "gunnchos.engineering_wave006.low_bandwidth_adaptation.v1",
        "ok": ok,
        "modes": {
            "full": full.value,
            "low": low.value,
            "emergency": emerg.value,
            "offline": off.value,
        },
        "adapted_low": adapted_low,
        "adapted_full_has_attachments": "attachments" in adapted_full,
    }
