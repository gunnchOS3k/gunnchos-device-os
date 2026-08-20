"""NET-ORCH-027 — local infrastructure status evaluation."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.models import (
    LocalInfraStatus,
    LocalInfrastructureObservation,
)


def evaluate_local_infrastructure(
    *,
    gateway_reachable: bool,
    dns_resolvable: bool,
    captive_portal_suspected: bool = False,
    latency_ms: float | None = None,
) -> LocalInfrastructureObservation:
    if not gateway_reachable:
        status = LocalInfraStatus.UNAVAILABLE
    elif captive_portal_suspected or not dns_resolvable:
        status = LocalInfraStatus.DEGRADED
    elif latency_ms is not None and latency_ms > 250.0:
        status = LocalInfraStatus.DEGRADED
    else:
        status = LocalInfraStatus.AVAILABLE
    return LocalInfrastructureObservation(
        status=status,
        gateway_reachable=gateway_reachable,
        dns_resolvable=dns_resolvable,
        captive_portal_suspected=captive_portal_suspected,
        latency_ms=latency_ms,
    )


def prove_local_infrastructure() -> dict[str, Any]:
    up = evaluate_local_infrastructure(gateway_reachable=True, dns_resolvable=True, latency_ms=12.0)
    deg = evaluate_local_infrastructure(
        gateway_reachable=True, dns_resolvable=False, captive_portal_suspected=True, latency_ms=80.0
    )
    down = evaluate_local_infrastructure(gateway_reachable=False, dns_resolvable=False)
    ok = (
        up.status == LocalInfraStatus.AVAILABLE
        and deg.status == LocalInfraStatus.DEGRADED
        and down.status == LocalInfraStatus.UNAVAILABLE
    )
    return {
        "schema": "gunnchos.engineering_wave006.local_infrastructure.v1",
        "ok": ok,
        "available": up.to_dict(),
        "degraded": deg.to_dict(),
        "unavailable": down.to_dict(),
    }
