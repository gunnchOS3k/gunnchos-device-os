"""Security / accessibility / offline / networking digital baselines (Lane I)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_BASELINES_PASS


def evaluate_baselines() -> dict[str, Any]:
    checks: dict[str, Any] = {}

    # Security
    from gunnchos_device_os.privacy_security_model import (
        get_profile_defaults,
        get_telemetry_policy,
    )
    from gunnchos_device_os.security_event_log import log_event

    defaults = get_profile_defaults("student")
    tele = get_telemetry_policy("student", defaults.get("consent_state", "not_asked"))
    log_event("cont_viii_baseline", {"lane": "security"})
    checks["security"] = {
        "ok": isinstance(defaults, dict) and isinstance(tele, dict),
        "detail": {
            "profile_keys": sorted(defaults.keys())[:12],
            "telemetry_keys": sorted(tele.keys())[:12] if isinstance(tele, dict) else [],
        },
    }

    # Accessibility
    from gunnchos_device_os.accessibility import get_a11y_defaults
    from gunnchos_device_os.accessibility_manager import get_defaults, validate_coverage

    a11y_defaults = get_a11y_defaults()
    mgr_defaults = get_defaults()
    coverage = validate_coverage(mgr_defaults)
    # validate_coverage returns list of missing feature ids; empty => ok
    coverage_ok = coverage == [] if isinstance(coverage, list) else bool(coverage.get("ok", True))
    checks["accessibility"] = {
        "ok": bool(a11y_defaults.get("screen_reader_friendly", True)) and coverage_ok,
        "detail": {"defaults": a11y_defaults, "manager": mgr_defaults, "missing": coverage},
    }

    # Offline
    from gunnchos_device_os.offline_mode_manager import enable_offline_mode, get_offline_plan
    from gunnchos_device_os.offline_sync import OfflineSyncEngine

    plan = get_offline_plan()
    offline_state = enable_offline_mode("offline")
    eng = OfflineSyncEngine(replica_id="baseline")
    eng.put("k", "v")
    checks["offline"] = {
        "ok": bool(offline_state.get("preset", True)),
        "detail": {
            "plan_keys": sorted(plan.keys())[:12] if isinstance(plan, dict) else type(plan).__name__,
            "offline_state": {k: offline_state.get(k) for k in ("preset", "message", "mock")},
            "pending": len(eng.pending()),
        },
    }

    # Networking
    from gunnchos_device_os.connectivity.bearers import build_default_bearers

    bearers = build_default_bearers()
    bearer_ids = set(bearers.keys()) if isinstance(bearers, dict) else set(bearers)
    needed = {"ethernet", "wifi", "terrestrial"}
    checks["networking"] = {
        "ok": needed.issubset(bearer_ids),
        "detail": {"bearers": sorted(bearer_ids)},
    }

    ok = all(v["ok"] for v in checks.values())
    return {
        "schema": "gunnchos.sec_a11y_offline_net_baselines.v1",
        "ok": ok,
        "token": TOKEN_BASELINES_PASS if ok else None,
        "checks": checks,
        "digitally_testable": True,
        "physical_rf_claimed": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
