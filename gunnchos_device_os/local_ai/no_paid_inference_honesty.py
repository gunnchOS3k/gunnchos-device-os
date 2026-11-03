"""Runtime gate loaded from artifacts/local_ai/NO_PAID_CLOUD_INFERENCE_HONESTY.json."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_STAMP = ROOT / "artifacts" / "local_ai" / "NO_PAID_CLOUD_INFERENCE_HONESTY.json"
SCHEMA = "gunnchos.device_os.no_paid_cloud_inference_honesty_v1"


def load_honesty_stamp(path: Path | None = None) -> dict[str, Any]:
    target = path or DEFAULT_STAMP
    doc = json.loads(target.read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA:
        raise ValueError(f"unexpected honesty schema: {doc.get('schema')}")
    return doc


def gates(doc: dict[str, Any] | None = None) -> dict[str, bool]:
    payload = doc if doc is not None else load_honesty_stamp()
    raw = payload.get("gates") or {}
    return {str(k): bool(v) for k, v in raw.items()}


def runtime_envelope(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    """Tokens every AI/tutor path must surface when the tip stamp is active."""
    payload = doc if doc is not None else load_honesty_stamp()
    sibling = payload.get("absent_sibling_gunnchai") or {}
    return {
        "NO_PAID_CLOUD_INFERENCE": bool((payload.get("gates") or {}).get("NO_PAID_CLOUD_INFERENCE")),
        "paid_cloud_inference_invoked": bool(payload.get("paid_cloud_inference_invoked")),
        "production_deploy_claimed": bool(payload.get("production_deploy_claimed")),
        "GUNNCHAI_APP_PRODUCT_COMPLETE": bool(payload.get("GUNNCHAI_APP_PRODUCT_COMPLETE")),
        "HUMAN": bool(payload.get("HUMAN")),
        "HUMAN_E6": bool(payload.get("HUMAN_E6")),
        "RC2": bool(payload.get("RC2")),
        "V1": bool(payload.get("V1")),
        "absent_sibling_compat_bridge_authorizes_paid_inference": bool(
            sibling.get("compat_bridge_authorizes_paid_inference")
        ),
        "absent_sibling_compat_bridge_claims_product_complete": bool(
            sibling.get("compat_bridge_claims_product_complete")
        ),
    }


def refuse_cloud_consent(*, cloud_consent: bool, doc: dict[str, Any] | None = None) -> dict[str, Any] | None:
    """Return a refusal payload when cloud consent is requested under the no-paid gate."""
    if not cloud_consent:
        return None
    payload = doc if doc is not None else load_honesty_stamp()
    if not gates(payload).get("NO_PAID_CLOUD_INFERENCE", False):
        return None
    return {
        "ok": False,
        "error": "paid_cloud_inference_refused",
        "detail": "cloudConsent refused — tip stamp NO_PAID_CLOUD_INFERENCE active",
        "cloud_consent_requested": True,
        **runtime_envelope(payload),
    }
