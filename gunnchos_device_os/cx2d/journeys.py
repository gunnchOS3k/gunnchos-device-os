"""CX2D journey upgrade — REAL_USER_JOURNEY_DIGITAL_PASS only with full conditions."""

from __future__ import annotations

from typing import Any, Dict, Optional

# Prior CX2C classes (from authentic journeys fail-closed GUI)
CX2C_PRIOR = {
    "J1": "REAL_PROVIDER_CLI_PASS",
    "J2": "REAL_PROVIDER_PARTIAL",
    "J3": "REAL_PROVIDER_CLI_PASS",  # pid without gui_window
    "J4": "REAL_PROVIDER_PARTIAL",  # typically
    "J5": "REAL_PROVIDER_CLI_PASS",
    "J6": "HUMAN_VALIDATION_PENDING",
    "J7": "REAL_PROVIDER_CLI_PASS",
}


def _blocked_upgrade(
    jid: str,
    *,
    prior: str,
    missing: str,
    real_ui: bool = False,
    real_provider: bool = False,
    persistence: bool = False,
) -> Dict[str, Any]:
    return {
        "id": jid,
        "prior_cx2_class": prior,
        "cx2d_class": "BLOCKED",
        "REAL_USER_JOURNEY_DIGITAL_PASS": False,
        "real_ui": real_ui,
        "real_provider": real_provider,
        "persistence": persistence,
        "missing_condition": missing,
        "blocker": missing,
    }


def upgrade_journeys(
    *,
    linux_gui_proven: bool = False,
    prior_override: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    prior = {**CX2C_PRIOR, **(prior_override or {})}
    missing = (
        "Linux production-shell rendered UI + real provider + real UI/input + "
        "authoritative read-back not proven in CX2D lab this run"
    )
    if linux_gui_proven:
        # Still require per-journey evidence objects; without them stay blocked.
        missing = "linux_gui_session_flag_true_but_per_journey_gui_evidence_missing"

    results = {
        "J1": _blocked_upgrade("J1", prior=prior["J1"], missing=missing + " (Writer/print GUI)"),
        "J2": _blocked_upgrade("J2", prior=prior["J2"], missing=missing + " (browser+mail GUI)"),
        "J3": _blocked_upgrade("J3", prior=prior["J3"], missing=missing + " (Flatpak App Center GUI)"),
        "J4": _blocked_upgrade(
            "J4",
            prior=prior.get("J4", "REAL_PROVIDER_PARTIAL"),
            missing=missing + " (CalDAV/CardDAV/chat GUI); chat may stay partial",
        ),
        "J5": _blocked_upgrade("J5", prior=prior["J5"], missing=missing + " (offline recovery GUI)"),
        "J6": _blocked_upgrade(
            "J6",
            prior=prior["J6"],
            missing="HUMAN_A11Y_PENDING — AT-SPI/Orca human validation required",
        ),
        "J7": _blocked_upgrade("J7", prior=prior["J7"], missing=missing + " (recovery GUI)"),
    }
    return {
        "schema": "gunnchos.cx2d.journey_upgrade.v1",
        "linux_gui_proven": linux_gui_proven,
        "journeys": results,
        "any_real_user_journey_digital_pass": False,
    }
