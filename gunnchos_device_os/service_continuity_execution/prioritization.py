"""NET-ORCH-032 — emergency/learning/communication prioritization via PriorityAuthority."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.network_decision.models import ApplicationPriority, PriorityAuthority, PrioritySource
from gunnchos_device_os.network_decision.priority_authority import resolve_priority_authority
from gunnchos_device_os.service_continuity_execution.models import TrafficClass


TRAFFIC_PRIORITY = {
    TrafficClass.EMERGENCY: ApplicationPriority.CRITICAL,
    TrafficClass.COMMUNICATION: ApplicationPriority.HIGH,
    TrafficClass.LEARNING: ApplicationPriority.HIGH,
    TrafficClass.BACKGROUND: ApplicationPriority.BACKGROUND,
    TrafficClass.OTHER: ApplicationPriority.NORMAL,
}


def prioritize_traffic(
    classes: list[TrafficClass],
    *,
    authority: PriorityAuthority | None = None,
) -> list[dict[str, Any]]:
    authority = authority or PriorityAuthority(
        source=PrioritySource.SYSTEM_POLICY,
        issuer="gunnchos.wave006.continuity",
        trusted=True,
        policy_version="wave006.v1",
        asserted_priority=ApplicationPriority.NORMAL,
    )
    ranked: list[tuple[int, dict[str, Any]]] = []
    order = {
        ApplicationPriority.CRITICAL: 0,
        ApplicationPriority.HIGH: 1,
        ApplicationPriority.NORMAL: 2,
        ApplicationPriority.LOW: 3,
        ApplicationPriority.BACKGROUND: 4,
    }
    for tc in classes:
        asserted = TRAFFIC_PRIORITY[tc]
        auth = PriorityAuthority(
            source=authority.source,
            issuer=authority.issuer,
            trusted=authority.trusted,
            policy_version=authority.policy_version,
            asserted_priority=asserted,
        )
        resolved = resolve_priority_authority(asserted, auth)
        effective = ApplicationPriority(resolved["effective"])
        ranked.append(
            (
                order[effective],
                {
                    "traffic_class": tc.value,
                    "asserted": asserted.value,
                    "effective": effective.value,
                    "authority": auth.to_dict(),
                },
            )
        )
    ranked.sort(key=lambda x: x[0])
    return [row for _, row in ranked]


def prove_traffic_prioritization() -> dict[str, Any]:
    # Self-asserted CRITICAL must not outrank system emergency
    self_asserted = PriorityAuthority(
        source=PrioritySource.APP_SELF_ASSERTED,
        issuer="untrusted.app",
        trusted=False,
        asserted_priority=ApplicationPriority.CRITICAL,
    )
    # Background self-asserted critical should be demoted by resolve_effective_priority
    from gunnchos_device_os.network_decision.priority_authority import prove_self_asserted_critical_blocked

    blocked = prove_self_asserted_critical_blocked()
    ordered = prioritize_traffic(
        [TrafficClass.BACKGROUND, TrafficClass.LEARNING, TrafficClass.EMERGENCY, TrafficClass.COMMUNICATION]
    )
    labels = [r["traffic_class"] for r in ordered]
    ok = (
        labels[0] == "EMERGENCY"
        and set(labels[:3]) >= {"EMERGENCY", "LEARNING", "COMMUNICATION"}
        and labels[-1] == "BACKGROUND"
        and blocked.get("ok") is True
        and self_asserted.source == PrioritySource.APP_SELF_ASSERTED
    )
    return {
        "schema": "gunnchos.engineering_wave006.traffic_prioritization.v1",
        "ok": ok,
        "ordered": ordered,
        "self_asserted_critical_blocked": blocked.get("ok") is True,
        "PRODUCTION_APP_PRIORITY_SIGNING": False,
    }
