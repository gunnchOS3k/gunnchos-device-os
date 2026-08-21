"""NET-ORCH-027 — local infrastructure capability graph."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.service_continuity_execution.models import (
    LocalCapability,
    LocalInfrastructureSnapshot,
    LocalInfraStatus,
)


def evaluate_local_infrastructure(
    *,
    link_or_ap_available: bool = True,
    gateway_reachable: bool = True,
    backhaul_reachable: bool = True,
    dns_resolvable: bool = True,
    edge_service_reachable: bool = False,
    local_cache_available: bool = False,
    peer_path_available: bool = False,
    captive_portal_suspected: bool = False,
    latency_ms: float | None = 20.0,
    observed_at: float = 1_700_000_000.0,
    max_age_s: float = 30.0,
    provenance: str = "DIGITAL_SYNTHETIC_EVIDENCE",
    now: float | None = None,
) -> LocalInfrastructureSnapshot:
    return LocalInfrastructureSnapshot(
        link_or_ap_available=link_or_ap_available,
        gateway_reachable=gateway_reachable,
        backhaul_reachable=backhaul_reachable,
        dns_resolvable=dns_resolvable,
        edge_service_reachable=edge_service_reachable,
        local_cache_available=local_cache_available,
        peer_path_available=peer_path_available,
        captive_portal_suspected=captive_portal_suspected,
        latency_ms=latency_ms,
        observed_at=observed_at,
        max_age_s=max_age_s,
        provenance=provenance,
    )


def prove_local_infrastructure() -> dict[str, Any]:
    now = 1_700_000_050.0
    scenarios: dict[str, LocalInfrastructureSnapshot] = {
        "ap_up_gateway_down": evaluate_local_infrastructure(
            link_or_ap_available=True, gateway_reachable=False, backhaul_reachable=False, observed_at=now
        ),
        "gateway_up_backhaul_down": evaluate_local_infrastructure(
            gateway_reachable=True, backhaul_reachable=False, observed_at=now
        ),
        "internet_down_edge_up": evaluate_local_infrastructure(
            backhaul_reachable=False,
            dns_resolvable=False,
            edge_service_reachable=True,
            observed_at=now,
        ),
        "internet_down_cache_up": evaluate_local_infrastructure(
            backhaul_reachable=False,
            dns_resolvable=False,
            local_cache_available=True,
            observed_at=now,
        ),
        "internet_down_peer_up": evaluate_local_infrastructure(
            backhaul_reachable=False,
            dns_resolvable=False,
            peer_path_available=True,
            observed_at=now,
        ),
        "dns_down_direct_local": evaluate_local_infrastructure(
            dns_resolvable=False,
            backhaul_reachable=False,
            edge_service_reachable=True,
            observed_at=now,
        ),
        "stale": evaluate_local_infrastructure(observed_at=now - 120.0, max_age_s=30.0),
        "unknown": evaluate_local_infrastructure(provenance="UNKNOWN", observed_at=now),
        "full_internet": evaluate_local_infrastructure(observed_at=now),
    }

    checks = {
        "ap_up_gateway_down_no_internet": scenarios["ap_up_gateway_down"].capabilities(now)[
            LocalCapability.INTERNET_SERVICE.value
        ]
        is False,
        "backhaul_down_no_internet": scenarios["gateway_up_backhaul_down"].capabilities(now)[
            LocalCapability.INTERNET_SERVICE.value
        ]
        is False,
        "edge_retained": scenarios["internet_down_edge_up"].capabilities(now)[
            LocalCapability.LOCAL_EDGE_SERVICE.value
        ]
        is True
        and scenarios["internet_down_edge_up"].capabilities(now)[LocalCapability.INTERNET_SERVICE.value] is False,
        "cache_retained": scenarios["internet_down_cache_up"].capabilities(now)[
            LocalCapability.LOCAL_CACHE_SERVICE.value
        ]
        is True,
        "peer_retained": scenarios["internet_down_peer_up"].capabilities(now)[
            LocalCapability.LOCAL_PEER_SERVICE.value
        ]
        is True,
        "dns_down_local_ok": scenarios["dns_down_direct_local"].capabilities(now)[
            LocalCapability.LOCAL_EDGE_SERVICE.value
        ]
        is True,
        "stale_unknown": scenarios["stale"].status(now) == LocalInfraStatus.UNKNOWN,
        "unknown_unknown": scenarios["unknown"].status(now) == LocalInfraStatus.UNKNOWN,
        "full_internet_available": scenarios["full_internet"].status(now) == LocalInfraStatus.AVAILABLE,
        "not_collapsed_to_one_bit": len(
            {
                frozenset(scenarios[k].capabilities(now).items())
                for k in (
                    "internet_down_edge_up",
                    "internet_down_cache_up",
                    "internet_down_peer_up",
                    "full_internet",
                )
            }
        )
        >= 3,
    }
    ok = all(checks.values())
    return {
        "schema": "gunnchos.engineering_wave006.local_infra.v1",
        "ok": ok,
        "checks": checks,
        "scenarios": {k: v.to_dict(now) for k, v in scenarios.items()},
        "LOCAL_INFRA_CAPABILITY_GRAPH": True,
    }
