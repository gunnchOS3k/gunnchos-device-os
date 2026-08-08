"""Fleet enrollment facade — delegates to FleetOpsSimulator.

Not production MDM: no remote server. Prefer gunnchos_device_os.fleet_ops.
"""
from __future__ import annotations

from gunnchos_device_os.fleet_ops import FleetOpsSimulator, EnrollmentState

_DEFAULT = FleetOpsSimulator(org_id="local-sim")


def enrolled(device_id: str | None = None) -> bool:
    if device_id is None:
        return any(
            d.enrollment == EnrollmentState.ENROLLED for d in _DEFAULT.devices.values()
        )
    dev = _DEFAULT.devices.get(device_id)
    return bool(dev and dev.enrollment == EnrollmentState.ENROLLED)


def enroll_device(device_id: str, **kwargs) -> dict:
    return _DEFAULT.enroll(device_id, **kwargs)


def simulator() -> FleetOpsSimulator:
    return _DEFAULT
