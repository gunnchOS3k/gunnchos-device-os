"""User-facing network decision summary for shell surfaces (no screenshots)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.network_decision.engine import DecisionExplanation


def shell_connection_view(decision: DecisionExplanation | None) -> dict[str, Any]:
    if decision is None:
        return {
            "selected_connection": None,
            "connection_state": "unknown",
            "degraded_or_offline": True,
            "basic_reason": "no_decision",
            "metered_warning": False,
            "security_warning": False,
            "user_preference": None,
        }
    rejected_security = any(
        "security_below_required_trust" in r.get("reasons", []) for r in decision.rejected_candidates
    )
    metered_warning = False
    # Infer from objective weights / selected candidate cost class via explanation scores
    selected = decision.selected_candidate
    floor = decision.service_floor
    state = decision.orchestrator_state or (
        "offline" if floor in {"OFFLINE_CAPABLE", "UNAVAILABLE"} else
        "degraded" if floor in {"REDUCED", "MINIMUM_USEFUL"} else "connected"
    )
    reason = decision.tie_break_reason or (
        f"selected={selected};floor={floor}"
    )
    return {
        "selected_connection": selected,
        "connection_state": state,
        "degraded_or_offline": floor in {"OFFLINE_CAPABLE", "UNAVAILABLE", "REDUCED", "MINIMUM_USEFUL"},
        "basic_reason": reason,
        "metered_warning": metered_warning,
        "security_warning": rejected_security,
        "user_preference": decision.user_preference,
        "service_floor": floor,
        "screenshot": None,
        "fake_screenshot": False,
    }
