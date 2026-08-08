"""Cloud/edge fabric stubs — mode-aware digital adapters.

Provides identity, enrollment, sync, saves, matchmaking metadata, telemetry,
and update metadata surfaces. Behavior changes by ServiceMode; nothing here
is a production multi-tenant cloud.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from gunnchos_device_os.identity import sha256_json, utc_now_iso


CLAIM_BOUNDARY = (
    "Cloud/edge service stubs only. Modes LOCAL/DISCONNECTED/CAMPUS_EDGE/CLOUD "
    "are software adapters — not a deployed campus or public cloud control plane."
)


class ServiceMode(str, Enum):
    LOCAL = "local"
    DISCONNECTED = "disconnected"
    CAMPUS_EDGE = "campus_edge"
    CLOUD = "cloud"


# Which operations each mode may attempt (still stubs when allowed).
_MODE_CAPABILITIES: dict[ServiceMode, frozenset[str]] = {
    ServiceMode.LOCAL: frozenset(
        {"identity", "enrollment", "sync", "saves", "matchmaking", "telemetry", "update_metadata"}
    ),
    ServiceMode.DISCONNECTED: frozenset({"identity", "saves"}),  # local-only
    ServiceMode.CAMPUS_EDGE: frozenset(
        {"identity", "enrollment", "sync", "saves", "matchmaking", "telemetry", "update_metadata"}
    ),
    ServiceMode.CLOUD: frozenset(
        {"identity", "enrollment", "sync", "saves", "matchmaking", "telemetry", "update_metadata"}
    ),
}


@dataclass
class CloudEdgeFabric:
    mode: ServiceMode = ServiceMode.LOCAL
    identities: dict[str, dict[str, Any]] = field(default_factory=dict)
    enrollments: dict[str, dict[str, Any]] = field(default_factory=dict)
    sync_queue: list[dict[str, Any]] = field(default_factory=list)
    saves: dict[str, dict[str, Any]] = field(default_factory=dict)
    matchmaking: dict[str, dict[str, Any]] = field(default_factory=dict)
    telemetry_buffer: list[dict[str, Any]] = field(default_factory=list)
    update_metadata: dict[str, Any] = field(default_factory=dict)

    def claim_boundary(self) -> str:
        return CLAIM_BOUNDARY

    def set_mode(self, mode: ServiceMode | str) -> dict[str, Any]:
        self.mode = mode if isinstance(mode, ServiceMode) else ServiceMode(mode)
        return {
            "mode": self.mode.value,
            "capabilities": sorted(_MODE_CAPABILITIES[self.mode]),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def _allow(self, capability: str) -> None:
        if capability not in _MODE_CAPABILITIES[self.mode]:
            raise PermissionError(
                f"capability {capability!r} unavailable in mode {self.mode.value}"
            )

    def _backend_label(self) -> str:
        return {
            ServiceMode.LOCAL: "local_store",
            ServiceMode.DISCONNECTED: "offline_cache",
            ServiceMode.CAMPUS_EDGE: "campus_edge_stub",
            ServiceMode.CLOUD: "cloud_stub",
        }[self.mode]

    # --- identity ---
    def identity_register(self, subject_id: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
        self._allow("identity")
        record = {
            "subject_id": subject_id,
            "attributes": dict(attributes or {}),
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "created_at": utc_now_iso(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.identities[subject_id] = record
        return record

    def identity_resolve(self, subject_id: str) -> dict[str, Any]:
        self._allow("identity")
        if subject_id not in self.identities:
            return {"found": False, "subject_id": subject_id, "mode": self.mode.value, "mock": False}
        return {"found": True, **self.identities[subject_id]}

    # --- enrollment ---
    def enrollment_submit(self, device_id: str, org_id: str) -> dict[str, Any]:
        self._allow("enrollment")
        token = sha256_json({"device_id": device_id, "org_id": org_id, "nonce": uuid4().hex})[:32]
        record = {
            "device_id": device_id,
            "org_id": org_id,
            "enrollment_token": token,
            "status": "accepted_stub",
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "at": utc_now_iso(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.enrollments[device_id] = record
        return record

    # --- sync ---
    def sync_enqueue(self, collection: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._allow("sync")
        entry = {
            "collection": collection,
            "item_id": item_id,
            "payload": payload,
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "queued_at": utc_now_iso(),
            "status": "queued" if self.mode != ServiceMode.DISCONNECTED else "held_local",
            "mock": False,
        }
        self.sync_queue.append(entry)
        return entry

    def sync_drain(self, limit: int = 50) -> list[dict[str, Any]]:
        self._allow("sync")
        batch = self.sync_queue[:limit]
        self.sync_queue = self.sync_queue[limit:]
        for item in batch:
            item["status"] = "delivered_stub"
            item["delivered_at"] = utc_now_iso()
        return batch

    # --- saves ---
    def save_put(self, save_id: str, blob_meta: dict[str, Any]) -> dict[str, Any]:
        self._allow("saves")
        record = {
            "save_id": save_id,
            "meta": dict(blob_meta),
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "at": utc_now_iso(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.saves[save_id] = record
        return record

    def save_get(self, save_id: str) -> dict[str, Any]:
        self._allow("saves")
        if save_id not in self.saves:
            return {"found": False, "save_id": save_id, "mode": self.mode.value, "mock": False}
        return {"found": True, **self.saves[save_id]}

    # --- matchmaking metadata (not a game server) ---
    def matchmaking_publish(self, lobby_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        self._allow("matchmaking")
        record = {
            "lobby_id": lobby_id,
            "metadata": dict(metadata),
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "at": utc_now_iso(),
            "note": "Metadata only — not a live matchmaking service",
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.matchmaking[lobby_id] = record
        return record

    def matchmaking_list(self) -> dict[str, Any]:
        self._allow("matchmaking")
        return {
            "lobbies": list(self.matchmaking.values()),
            "mode": self.mode.value,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    # --- telemetry ---
    def telemetry_emit(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._allow("telemetry")
        entry = {
            "event_type": event_type,
            "payload": payload,
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "at": utc_now_iso(),
            "mock": False,
        }
        self.telemetry_buffer.append(entry)
        return entry

    # --- update metadata ---
    def update_metadata_set(self, channel: str, version: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
        self._allow("update_metadata")
        record = {
            "channel": channel,
            "version": version,
            "extra": dict(extra or {}),
            "backend": self._backend_label(),
            "mode": self.mode.value,
            "at": utc_now_iso(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.update_metadata[channel] = record
        return record

    def update_metadata_get(self, channel: str) -> dict[str, Any]:
        self._allow("update_metadata")
        if channel not in self.update_metadata:
            return {"found": False, "channel": channel, "mode": self.mode.value, "mock": False}
        return {"found": True, **self.update_metadata[channel]}

    def snapshot(self) -> dict[str, Any]:
        return {
            "mode": self.mode.value,
            "capabilities": sorted(_MODE_CAPABILITIES[self.mode]),
            "identity_count": len(self.identities),
            "enrollment_count": len(self.enrollments),
            "sync_queue_depth": len(self.sync_queue),
            "saves_count": len(self.saves),
            "matchmaking_count": len(self.matchmaking),
            "telemetry_buffered": len(self.telemetry_buffer),
            "update_channels": sorted(self.update_metadata.keys()),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
