"""Shared persistence for the runnable DEV plane services."""
from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from gunnchos_device_os.cloud_dev_plane.claim import CLAIM_BOUNDARY, REALM
from gunnchos_device_os.identity import utc_now_iso


class DevPlaneStore:
    """JSON-backed store shared by compose services (volume) or in-process tests."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._lock = threading.RLock()
        self.data: dict[str, Any] = {
            "identities": {},
            "enrollments": {},
            "sync_queue": [],
            "sync_delivered": [],
            "saves": {},
            "matchmaking": {},
            "telemetry": [],
            "update_metadata": {},
            "fleet": {},
            "diagnostics": [],
            "meta": {"realm": REALM, "claim_boundary": CLAIM_BOUNDARY},
        }
        if self.path and self.path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.data.update(raw)

    def persist(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        tmp.replace(self.path)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "identity_count": len(self.data["identities"]),
                "enrollment_count": len(self.data["enrollments"]),
                "sync_queue_depth": len(self.data["sync_queue"]),
                "sync_delivered_count": len(self.data["sync_delivered"]),
                "saves_count": len(self.data["saves"]),
                "matchmaking_count": len(self.data["matchmaking"]),
                "telemetry_buffered": len(self.data["telemetry"]),
                "update_channels": sorted(self.data["update_metadata"].keys()),
                "fleet_devices": sorted(self.data["fleet"].keys()),
                "diagnostics_count": len(self.data["diagnostics"]),
                "realm": REALM,
                "claim_boundary": CLAIM_BOUNDARY,
                "updated_at": utc_now_iso(),
                "mock": False,
            }
