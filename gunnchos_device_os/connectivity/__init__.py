"""Connectivity bearers + modem software paths (DEV / digital)."""
from __future__ import annotations

from gunnchos_device_os.connectivity.bearers import (
    BearerCapability,
    BearerMetricsView,
    EthernetBearer,
    FutureNTNBearer,
    SimulatedNTNBearer,
    TerrestrialBearer,
    WiFiBearer,
    build_default_bearers,
    select_bearer,
)
from gunnchos_device_os.connectivity.modem_rm520n import (
    RM520N_GL_SKUS,
    SimulatedRM520NGL,
    ModemManagerFacade,
)

__all__ = [
    "BearerCapability",
    "BearerMetricsView",
    "EthernetBearer",
    "FutureNTNBearer",
    "SimulatedNTNBearer",
    "TerrestrialBearer",
    "WiFiBearer",
    "build_default_bearers",
    "select_bearer",
    "RM520N_GL_SKUS",
    "SimulatedRM520NGL",
    "ModemManagerFacade",
]
