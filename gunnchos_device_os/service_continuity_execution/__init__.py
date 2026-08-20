"""Service-Continuity Execution Plane (Wave006) — NET-ORCH-026..035.

Extends Wave005 network_decision + Wave004 continuity/sync/diagnostics/storage.
Digital/synthetic execution only: no live carrier handover, kernel MPTCP, or real NTN modem claims.
"""
from __future__ import annotations

from gunnchos_device_os.service_continuity_execution.models import (
    CLAIM_BOUNDARIES,
    ContinuityState,
    MultipathKind,
    SatelliteVisibilityProvenance,
)

__all__ = [
    "CLAIM_BOUNDARIES",
    "ContinuityState",
    "MultipathKind",
    "SatelliteVisibilityProvenance",
]


def get_continuity_controller(*args, **kwargs):
    from gunnchos_device_os.service_continuity_execution.controller import ContinuityController
    return ContinuityController(*args, **kwargs)
