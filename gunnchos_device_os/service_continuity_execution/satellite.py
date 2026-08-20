"""NET-ORCH-026 — satellite visibility (SIMULATED / DIGITAL_TWIN only)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.models import (
    SatelliteVisibility,
    SatelliteVisibilityProvenance,
)


def evaluate_satellite_visibility(
    *,
    elevation_deg: float | None,
    satellites_in_view: int,
    provenance: SatelliteVisibilityProvenance,
    confidence: float = 0.8,
) -> SatelliteVisibility:
    if provenance not in (
        SatelliteVisibilityProvenance.SIMULATED,
        SatelliteVisibilityProvenance.DIGITAL_TWIN,
        SatelliteVisibilityProvenance.UNKNOWN,
    ):
        provenance = SatelliteVisibilityProvenance.UNKNOWN
    if elevation_deg is None or satellites_in_view < 0:
        return SatelliteVisibility(
            visible=False,
            elevation_deg=elevation_deg,
            satellites_in_view=max(0, satellites_in_view),
            provenance=provenance,
            confidence=min(confidence, 0.4),
            note="missing/invalid visibility inputs → not visible (never best-case)",
        )
    visible = elevation_deg >= 10.0 and satellites_in_view >= 1
    return SatelliteVisibility(
        visible=visible,
        elevation_deg=elevation_deg,
        satellites_in_view=satellites_in_view,
        provenance=provenance,
        confidence=confidence if provenance != SatelliteVisibilityProvenance.UNKNOWN else min(confidence, 0.3),
    )


def prove_satellite_visibility() -> dict[str, Any]:
    sim = evaluate_satellite_visibility(
        elevation_deg=35.0,
        satellites_in_view=4,
        provenance=SatelliteVisibilityProvenance.SIMULATED,
    )
    twin = evaluate_satellite_visibility(
        elevation_deg=5.0,
        satellites_in_view=1,
        provenance=SatelliteVisibilityProvenance.DIGITAL_TWIN,
    )
    missing = evaluate_satellite_visibility(
        elevation_deg=None,
        satellites_in_view=0,
        provenance=SatelliteVisibilityProvenance.UNKNOWN,
    )
    ok = (
        sim.visible is True
        and twin.visible is False
        and missing.visible is False
        and sim.provenance == SatelliteVisibilityProvenance.SIMULATED
        and twin.provenance == SatelliteVisibilityProvenance.DIGITAL_TWIN
        and sim.to_dict()["REAL_NTN_MODEM_VALIDATED"] is False
    )
    return {
        "schema": "gunnchos.engineering_wave006.satellite_visibility.v1",
        "ok": ok,
        "simulated": sim.to_dict(),
        "digital_twin": twin.to_dict(),
        "missing_inputs": missing.to_dict(),
        "REAL_NTN_MODEM_VALIDATED": False,
        "allowed_provenance": ["SIMULATED", "DIGITAL_TWIN", "UNKNOWN"],
    }
