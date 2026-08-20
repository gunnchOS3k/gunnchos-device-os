"""NET-ORCH-030 — application-level multipath (not kernel MPTCP)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.service_continuity_execution.models import MultipathKind


@dataclass
class MultipathPlan:
    primary: str
    secondary: str | None
    kind: MultipathKind = MultipathKind.APPLICATION_LEVEL_MULTIPATH
    bytes_primary: int = 0
    bytes_secondary: int = 0
    REAL_MPTCP: bool = False
    KERNEL_MPTCP_VALIDATED: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "primary": self.primary,
            "secondary": self.secondary,
            "MULTIPATH_KIND": self.kind.value,
            "bytes_primary": self.bytes_primary,
            "bytes_secondary": self.bytes_secondary,
            "REAL_MPTCP": False,
            "KERNEL_MPTCP_VALIDATED": False,
        }


def build_multipath_plan(available: list[str], *, prefer: str | None = None) -> MultipathPlan:
    paths = [p for p in available if p]
    if not paths:
        return MultipathPlan(primary="offline", secondary=None)
    if prefer and prefer in paths:
        primary = prefer
        secondary = next((p for p in paths if p != primary), None)
    else:
        primary = paths[0]
        secondary = paths[1] if len(paths) > 1 else None
    return MultipathPlan(primary=primary, secondary=secondary)


def stripe_application_payload(plan: MultipathPlan, payload: bytes) -> MultipathPlan:
    """Split payload across primary/secondary at application layer."""
    if plan.secondary is None:
        plan.bytes_primary = len(payload)
        plan.bytes_secondary = 0
        return plan
    mid = len(payload) // 2
    plan.bytes_primary = mid
    plan.bytes_secondary = len(payload) - mid
    return plan


def prove_application_multipath() -> dict[str, Any]:
    plan = build_multipath_plan(["wifi", "cellular", "ntn_simulated"], prefer="wifi")
    plan = stripe_application_payload(plan, b"x" * 100)
    single = build_multipath_plan(["wifi"])
    single = stripe_application_payload(single, b"y" * 40)
    ok = (
        plan.kind == MultipathKind.APPLICATION_LEVEL_MULTIPATH
        and plan.secondary == "cellular"
        and plan.bytes_primary == 50
        and plan.bytes_secondary == 50
        and plan.REAL_MPTCP is False
        and single.secondary is None
        and single.bytes_primary == 40
        and plan.to_dict()["MULTIPATH_KIND"] == "APPLICATION_LEVEL_MULTIPATH"
    )
    return {
        "schema": "gunnchos.engineering_wave006.application_multipath.v1",
        "ok": ok,
        "dual_path": plan.to_dict(),
        "single_path": single.to_dict(),
        "MULTIPATH_KIND": MultipathKind.APPLICATION_LEVEL_MULTIPATH.value,
        "REAL_MPTCP": False,
        "KERNEL_MPTCP_VALIDATED": False,
    }
