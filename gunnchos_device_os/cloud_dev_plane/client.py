"""Mode-aware HTTP client with outage survival queue and resync."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from gunnchos_device_os.cloud_dev_plane.claim import CLAIM_BOUNDARY, REALM
from gunnchos_device_os.cloud_edge.services import ServiceMode, _MODE_CAPABILITIES
from gunnchos_device_os.identity import utc_now_iso


@dataclass
class QueuedOp:
    op_id: str
    capability: str
    method: str
    path: str
    body: dict[str, Any]
    enqueued_at: str
    status: str = "pending"


@dataclass
class DevPlaneClient:
    """Client for the runnable DEV plane.

    When transport fails (outage), eligible ops are queued locally and flushed
    on ``resync()`` once connectivity returns.
    """

    base_url: str
    mode: ServiceMode = ServiceMode.LOCAL
    timeout_s: float = 2.0
    force_outage: bool = False
    outbox: list[QueuedOp] = field(default_factory=list)
    last_error: str | None = None
    delivered_on_resync: list[dict[str, Any]] = field(default_factory=list)

    def set_mode(self, mode: ServiceMode | str) -> dict[str, Any]:
        self.mode = mode if isinstance(mode, ServiceMode) else ServiceMode(mode)
        return {
            "mode": self.mode.value,
            "capabilities": sorted(_MODE_CAPABILITIES[self.mode]),
            "realm": REALM,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
        }

    def simulate_outage(self, enabled: bool = True) -> None:
        self.force_outage = enabled

    def _allow(self, capability: str) -> None:
        if capability not in _MODE_CAPABILITIES[self.mode]:
            raise PermissionError(
                f"capability {capability!r} unavailable in mode {self.mode.value}"
            )

    def _headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Gunnchos-Mode": self.mode.value,
            "X-Gunnchos-Realm": REALM,
        }

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        *,
        capability: str,
        queue_on_failure: bool = True,
    ) -> dict[str, Any]:
        self._allow(capability)
        payload = dict(body or {})
        payload.setdefault("mode", self.mode.value)
        if self.force_outage:
            return self._enqueue(capability, method, path, payload, reason="simulated_outage")

        data = None if method == "GET" else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url.rstrip("/") + path,
            data=data,
            headers=self._headers(),
            method=method,
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                raw = resp.read().decode("utf-8")
                result = json.loads(raw) if raw else {}
                result.setdefault("mock", False)
                self.last_error = None
                return result
        except urllib.error.HTTPError as exc:
            raw = exc.read().decode("utf-8") if exc.fp else ""
            try:
                result = json.loads(raw) if raw else {"error": str(exc)}
            except json.JSONDecodeError:
                result = {"error": raw or str(exc)}
            result.setdefault("http_status", exc.code)
            result.setdefault("mock", False)
            self.last_error = str(exc)
            if exc.code >= 500 and queue_on_failure and method != "GET":
                return self._enqueue(capability, method, path, payload, reason=str(exc))
            return result
        except PermissionError:
            raise
        except Exception as exc:  # noqa: BLE001
            self.last_error = str(exc)
            if queue_on_failure and method != "GET":
                return self._enqueue(capability, method, path, payload, reason=str(exc))
            raise ConnectionError(f"dev plane unreachable: {exc}") from exc

    def _enqueue(
        self,
        capability: str,
        method: str,
        path: str,
        body: dict[str, Any],
        *,
        reason: str,
    ) -> dict[str, Any]:
        op = QueuedOp(
            op_id=uuid4().hex[:12],
            capability=capability,
            method=method,
            path=path,
            body=body,
            enqueued_at=utc_now_iso(),
            status="held_local",
        )
        self.outbox.append(op)
        return {
            "status": "held_local",
            "op_id": op.op_id,
            "reason": reason,
            "outbox_depth": len(self.outbox),
            "mode": self.mode.value,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    # --- surface helpers ---
    def identity_register(self, subject_id: str, attributes: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/identity/register",
            {"subject_id": subject_id, "attributes": attributes or {}},
            capability="identity",
        )

    def identity_resolve(self, subject_id: str) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/v1/identity/{subject_id}",
            capability="identity",
            queue_on_failure=False,
        )

    def enrollment_submit(
        self,
        device_id: str,
        org_id: str,
        enrollment_token: str = "DEV_ENROLLMENT_TOKEN",
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/enrollment/submit",
            {
                "device_id": device_id,
                "org_id": org_id,
                "enrollment_token": enrollment_token,
            },
            capability="enrollment",
        )

    def sync_enqueue(self, collection: str, item_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/sync/enqueue",
            {"collection": collection, "item_id": item_id, "payload": payload},
            capability="sync",
        )

    def sync_drain(self, limit: int = 50) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/sync/drain",
            {"limit": limit},
            capability="sync",
            queue_on_failure=False,
        )

    def save_put(self, save_id: str, meta: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/saves/put",
            {"save_id": save_id, "meta": meta},
            capability="saves",
        )

    def matchmaking_publish(self, lobby_id: str, metadata: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/matchmaking/publish",
            {"lobby_id": lobby_id, "metadata": metadata},
            capability="matchmaking",
        )

    def telemetry_emit(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/telemetry/emit",
            {"event_type": event_type, "payload": payload},
            capability="telemetry",
        )

    def update_metadata_set(
        self, channel: str, version: str, extra: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/v1/ota/metadata",
            {"channel": channel, "version": version, "extra": extra or {}},
            capability="update_metadata",
        )

    def fleet_heartbeat(self, device_id: str, ring: str = "dev") -> dict[str, Any]:
        # Use sync capability gate via online modes — fleet blocked in DISCONNECTED by server
        # and by treating as enrollment-class online op.
        if self.mode == ServiceMode.DISCONNECTED:
            raise PermissionError("capability 'fleet' unavailable in mode disconnected")
        return self._request(
            "POST",
            "/v1/fleet/heartbeat",
            {"device_id": device_id, "ring": ring},
            capability="enrollment",  # online-only proxy; DISCONNECTED already blocked
        )

    def diagnostics_report(self, device_id: str, checks: dict[str, Any] | None = None) -> dict[str, Any]:
        # Diagnostics allowed even when disconnected (local).
        payload = {"device_id": device_id, "checks": checks or {"ok": True}, "mode": self.mode.value}
        if self.force_outage:
            # Still record locally in outbox for later upload.
            return self._enqueue("saves", "POST", "/v1/diagnostics/report", payload, reason="simulated_outage")
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/v1/diagnostics/report",
            data=data,
            headers=self._headers(),
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            return self._enqueue(
                "saves", "POST", "/v1/diagnostics/report", payload, reason=str(exc)
            )

    def resync(self) -> dict[str, Any]:
        """Flush outbox after outage; returns delivery report."""
        if self.force_outage:
            return {
                "status": "still_disconnected",
                "outbox_depth": len(self.outbox),
                "delivered": 0,
                "mock": False,
            }
        delivered: list[dict[str, Any]] = []
        failed: list[dict[str, Any]] = []
        remaining: list[QueuedOp] = []
        for op in self.outbox:
            if op.capability not in _MODE_CAPABILITIES[self.mode]:
                op.status = "blocked_in_mode"
                remaining.append(op)
                failed.append({"op_id": op.op_id, "reason": f"blocked_in_mode_{self.mode.value}"})
                continue
            try:
                # Bypass queue-on-failure to surface hard errors.
                data = json.dumps(op.body).encode("utf-8")
                req = urllib.request.Request(
                    self.base_url.rstrip("/") + op.path,
                    data=data,
                    headers=self._headers(),
                    method=op.method,
                )
                with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                delivered.append({"op_id": op.op_id, "path": op.path, "result": result})
            except Exception as exc:  # noqa: BLE001
                op.status = "retry"
                remaining.append(op)
                failed.append({"op_id": op.op_id, "reason": str(exc)})
        self.outbox = remaining
        self.delivered_on_resync.extend(delivered)
        return {
            "status": "resync_complete" if not remaining else "resync_partial",
            "delivered": len(delivered),
            "failed": len(failed),
            "outbox_depth": len(self.outbox),
            "items": delivered,
            "errors": failed,
            "mode": self.mode.value,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def inventory(self) -> dict[str, Any]:
        req = urllib.request.Request(
            self.base_url.rstrip("/") + "/v1/inventory",
            headers=self._headers(),
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
            return json.loads(resp.read().decode("utf-8"))
