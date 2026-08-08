"""Integrated OS/runtime service architecture for gunnchOS (digital).

Supervises in-process service adapters over existing platform modules,
with optional Unix-socket / local-HTTP IPC for cross-process calls.
Not a shipping kernel init, not systemd, not a production OS runtime.
"""
from __future__ import annotations

from gunnchos_device_os.runtime.catalog import SERVICE_CATALOG, service_matrix
from gunnchos_device_os.runtime.ipc import (
    CLAIM_BOUNDARY as IPC_CLAIM_BOUNDARY,
    IpcRuntimePlane,
    TOKEN_IPC_PASS,
)
from gunnchos_device_os.runtime.service_base import (
    CLAIM_BOUNDARY,
    FaultRecord,
    ServiceConfig,
    ServiceState,
    ServiceStatus,
)
from gunnchos_device_os.runtime.supervisor import RuntimeSupervisor

__all__ = [
    "CLAIM_BOUNDARY",
    "FaultRecord",
    "IPC_CLAIM_BOUNDARY",
    "IpcRuntimePlane",
    "RuntimeSupervisor",
    "SERVICE_CATALOG",
    "ServiceConfig",
    "ServiceState",
    "ServiceStatus",
    "TOKEN_IPC_PASS",
    "service_matrix",
]
