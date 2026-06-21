"""Generate hardware compatibility report."""
from __future__ import annotations

from typing import Any

from .hardware_compatibility_engine import evaluate_compatibility
from .hardware_manifest_loader import list_device_ids, load_device_profile


def generate_report() -> dict[str, Any]:
    devices = list_device_ids()
    profiles = {d: load_device_profile(d) for d in devices}
    return {
        "report_type": "hardware_compatibility_summary",
        "device_count": len(devices),
        "devices": devices,
        "simulated_only": True,
        "claim_boundary": "Profile-based compatibility report — not physical hardware validation",
        "profiles_summary": {
            d: {
                "display_name": p.display_name,
                "modes": p.supported_modes,
                "presets": p.supported_journey_presets,
                "gaps": p.known_gaps,
            }
            for d, p in profiles.items()
        },
    }


def scenario_report(device_id: str, **kwargs: Any) -> dict[str, Any]:
    result = evaluate_compatibility(device_id, **kwargs)
    return {
        "device_id": device_id,
        "compatible": result.compatible,
        "status": result.status,
        "user_message": result.user_message,
        "technical_log": result.technical_log,
        "fallback": result.recommended_fallbacks,
        "evidence_required": result.evidence_required,
        "warnings": result.warnings,
        "blockers": result.blockers,
        **kwargs,
    }
