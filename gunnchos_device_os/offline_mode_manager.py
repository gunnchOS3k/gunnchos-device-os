"""Offline mode manager — low-bandwidth and disconnected workflows."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.offline_sync import ConflictPolicy, OfflineSyncEngine

OFFLINE_CAPABILITIES: dict[str, dict[str, Any]] = {
    "offline_lessons": {"apps": ["waike_offline", "gunnchai3k"], "sync": "when_online"},
    "offline_writing": {"apps": ["notes"], "sync": "when_online"},
    "offline_sketching": {"apps": ["sketch"], "sync": "when_online"},
    "offline_coding": {"apps": ["vscode", "waike_offline"], "sync": "when_online"},
    "offline_music": {"apps": ["music_notes"], "sync": "when_online"},
    "offline_games": {"apps": ["scaly_wings_edu"], "sync": "license_dependent"},
}


def get_offline_plan(
    profile_offline_first: bool = True,
    *,
    policy: ConflictPolicy | str = ConflictPolicy.VECTOR_CLOCK,
) -> dict[str, Any]:
    policy_value = policy.value if isinstance(policy, ConflictPolicy) else policy
    return {
        "offline_first": profile_offline_first,
        "capabilities": OFFLINE_CAPABILITIES,
        "sync_when_online": True,
        "conflict_handling": policy_value,
        "conflict_policies_available": [p.value for p in ConflictPolicy],
        "mock": False,
    }


def enable_offline_mode(
    preset_id: str = "offline",
    *,
    replica_id: str | None = None,
    policy: ConflictPolicy | str = ConflictPolicy.VECTOR_CLOCK,
) -> dict[str, Any]:
    pol = policy if isinstance(policy, ConflictPolicy) else ConflictPolicy(policy)
    engine = OfflineSyncEngine(
        replica_id=replica_id or f"offline-{preset_id}",
        policy=pol,
    )
    return {
        "preset": preset_id,
        "plan": get_offline_plan(True, policy=pol),
        "sync_engine": engine.snapshot(),
        "message": "Offline mode enabled — vector-clock/LWW sync when connected",
        "mock": False,
    }


def create_sync_engine(
    *,
    replica_id: str = "local",
    policy: ConflictPolicy | str = ConflictPolicy.VECTOR_CLOCK,
) -> OfflineSyncEngine:
    pol = policy if isinstance(policy, ConflictPolicy) else ConflictPolicy(policy)
    return OfflineSyncEngine(replica_id=replica_id, policy=pol)
