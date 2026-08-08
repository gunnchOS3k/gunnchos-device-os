"""stdlib HTTP server exposing DEV plane service surfaces.

Can run as a single gateway (all routes) or as a single SERVICE_ROLE.
"""
from __future__ import annotations

import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from gunnchos_device_os.cloud_dev_plane.claim import CLAIM_BOUNDARY, REALM
from gunnchos_device_os.cloud_dev_plane.otel_export import OtelRoundTrip
from gunnchos_device_os.cloud_dev_plane.privacy_redaction import redact_payload
from gunnchos_device_os.cloud_dev_plane.store import DevPlaneStore
from gunnchos_device_os.cloud_edge.services import ServiceMode, _MODE_CAPABILITIES
from gunnchos_device_os.identity import sha256_json, utc_now_iso

SERVICE_ROLES = frozenset(
    {
        "gateway",
        "identity",
        "enrollment",
        "sync",
        "saves",
        "matchmaking",
        "ota_metadata",
        "telemetry",
        "fleet",
        "diagnostics",
    }
)

DEFAULT_PORTS = {
    "gateway": 8100,
    "identity": 8101,
    "enrollment": 8102,
    "sync": 8103,
    "saves": 8104,
    "matchmaking": 8105,
    "ota_metadata": 8106,
    "telemetry": 8107,
    "fleet": 8108,
    "diagnostics": 8109,
}


class DevPlaneApp:
    def __init__(
        self,
        store: DevPlaneStore | None = None,
        *,
        default_mode: ServiceMode = ServiceMode.LOCAL,
        otel: OtelRoundTrip | None = None,
        role: str = "gateway",
    ) -> None:
        if role not in SERVICE_ROLES:
            raise ValueError(f"unknown service role: {role}")
        self.store = store or DevPlaneStore()
        self.default_mode = default_mode
        self.otel = otel
        self.role = role
        self.started_at = utc_now_iso()

    def _mode(self, headers: dict[str, str], body: dict[str, Any] | None = None) -> ServiceMode:
        raw = (body or {}).get("mode") or headers.get("x-gunnchos-mode") or self.default_mode.value
        return raw if isinstance(raw, ServiceMode) else ServiceMode(str(raw).lower())

    def _allow(self, mode: ServiceMode, capability: str) -> None:
        if capability not in _MODE_CAPABILITIES[mode]:
            raise PermissionError(
                f"capability {capability!r} unavailable in mode {mode.value}"
            )

    def _maybe_trace(self, surface: str, mode: ServiceMode, attrs: dict[str, Any] | None = None) -> None:
        if self.otel is None:
            return
        self.otel.export_span(surface=surface, mode=mode.value, attributes=attrs)

    def inventory(self) -> dict[str, Any]:
        return {
            "realm": REALM,
            "role": self.role,
            "service_list": sorted(s for s in SERVICE_ROLES if s != "gateway"),
            "ports": dict(DEFAULT_PORTS),
            "modes": [m.value for m in ServiceMode],
            "claim_boundary": CLAIM_BOUNDARY,
            "started_at": self.started_at,
            "snapshot": self.store.snapshot(),
            "mock": False,
        }

    def handle(self, method: str, path: str, headers: dict[str, str], body: dict[str, Any]) -> tuple[int, dict[str, Any]]:
        parsed = urlparse(path)
        route = parsed.path.rstrip("/") or "/"
        qs = parse_qs(parsed.query)

        if method == "GET" and route in ("/health", "/v1/health"):
            return 200, {"ok": True, "role": self.role, "realm": REALM, "mock": False}
        if method == "GET" and route in ("/v1/inventory", "/inventory"):
            return 200, self.inventory()
        if method == "GET" and route == "/v1/snapshot":
            return 200, self.store.snapshot()

        try:
            mode = self._mode(headers, body)
        except ValueError as exc:
            return 400, {"error": str(exc), "mock": False}

        # Role isolation: gateway serves all; dedicated roles only their surface.
        def role_ok(surface: str) -> bool:
            return self.role in ("gateway", surface)

        try:
            if method == "POST" and route == "/v1/identity/register" and role_ok("identity"):
                self._allow(mode, "identity")
                subject_id = body["subject_id"]
                record = {
                    "subject_id": subject_id,
                    "attributes": redact_payload(dict(body.get("attributes") or {})),
                    "mode": mode.value,
                    "backend": f"dev_plane_{mode.value}",
                    "created_at": utc_now_iso(),
                    "realm": REALM,
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["identities"][subject_id] = record
                    self.store.persist()
                self._maybe_trace("identity", mode, {"gunnchos.event.type": "register"})
                return 200, record

            if method == "GET" and route.startswith("/v1/identity/") and role_ok("identity"):
                self._allow(mode, "identity")
                subject_id = route.split("/v1/identity/", 1)[1]
                with self.store._lock:
                    rec = self.store.data["identities"].get(subject_id)
                if not rec:
                    return 200, {"found": False, "subject_id": subject_id, "mode": mode.value, "mock": False}
                return 200, {"found": True, **rec}

            if method == "POST" and route == "/v1/enrollment/submit" and role_ok("enrollment"):
                self._allow(mode, "enrollment")
                device_id = body["device_id"]
                org_id = body["org_id"]
                token_raw = body.get("enrollment_token", "DEV_ENROLLMENT_TOKEN")
                if not str(token_raw).startswith("DEV_"):
                    return 403, {
                        "status": "rejected",
                        "reason": "non-DEV enrollment token rejected",
                        "mock": False,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                token = sha256_json({"device_id": device_id, "org_id": org_id, "nonce": uuid4().hex})[:32]
                record = {
                    "device_id": device_id,
                    "org_id": org_id,
                    "enrollment_token": "[REDACTED]",
                    "enrollment_token_fingerprint": token,
                    "status": "accepted_dev",
                    "mode": mode.value,
                    "backend": f"dev_plane_{mode.value}",
                    "at": utc_now_iso(),
                    "realm": REALM,
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["enrollments"][device_id] = record
                    self.store.persist()
                self._maybe_trace(
                    "enrollment",
                    mode,
                    {"gunnchos.device.id": device_id, "gunnchos.org.id": org_id},
                )
                return 200, record

            if method == "POST" and route == "/v1/sync/enqueue" and role_ok("sync"):
                self._allow(mode, "sync")
                entry = {
                    "collection": body["collection"],
                    "item_id": body["item_id"],
                    "payload": redact_payload(dict(body.get("payload") or {})),
                    "mode": mode.value,
                    "queued_at": utc_now_iso(),
                    "status": "queued",
                    "mock": False,
                }
                with self.store._lock:
                    self.store.data["sync_queue"].append(entry)
                    self.store.persist()
                self._maybe_trace("sync", mode)
                return 200, entry

            if method == "POST" and route == "/v1/sync/drain" and role_ok("sync"):
                self._allow(mode, "sync")
                limit = int(body.get("limit") or (qs.get("limit") or ["50"])[0])
                with self.store._lock:
                    batch = self.store.data["sync_queue"][:limit]
                    self.store.data["sync_queue"] = self.store.data["sync_queue"][limit:]
                    for item in batch:
                        item["status"] = "delivered_dev"
                        item["delivered_at"] = utc_now_iso()
                    self.store.data["sync_delivered"].extend(batch)
                    self.store.persist()
                return 200, {"delivered": batch, "count": len(batch), "mock": False}

            if method == "POST" and route == "/v1/saves/put" and role_ok("saves"):
                self._allow(mode, "saves")
                save_id = body["save_id"]
                record = {
                    "save_id": save_id,
                    "meta": redact_payload(dict(body.get("meta") or {})),
                    "mode": mode.value,
                    "at": utc_now_iso(),
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["saves"][save_id] = record
                    self.store.persist()
                self._maybe_trace("saves", mode)
                return 200, record

            if method == "GET" and route.startswith("/v1/saves/") and role_ok("saves"):
                self._allow(mode, "saves")
                save_id = route.split("/v1/saves/", 1)[1]
                with self.store._lock:
                    rec = self.store.data["saves"].get(save_id)
                if not rec:
                    return 200, {"found": False, "save_id": save_id, "mode": mode.value, "mock": False}
                return 200, {"found": True, **rec}

            if method == "POST" and route == "/v1/matchmaking/publish" and role_ok("matchmaking"):
                self._allow(mode, "matchmaking")
                lobby_id = body["lobby_id"]
                record = {
                    "lobby_id": lobby_id,
                    "metadata": redact_payload(dict(body.get("metadata") or {})),
                    "mode": mode.value,
                    "at": utc_now_iso(),
                    "note": "Metadata only — not a live matchmaking game server",
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["matchmaking"][lobby_id] = record
                    self.store.persist()
                self._maybe_trace("matchmaking", mode)
                return 200, record

            if method == "GET" and route == "/v1/matchmaking/list" and role_ok("matchmaking"):
                self._allow(mode, "matchmaking")
                with self.store._lock:
                    lobbies = list(self.store.data["matchmaking"].values())
                return 200, {"lobbies": lobbies, "mode": mode.value, "mock": False}

            if method == "POST" and route == "/v1/telemetry/emit" and role_ok("telemetry"):
                self._allow(mode, "telemetry")
                entry = {
                    "event_type": body.get("event_type", "event"),
                    "payload": redact_payload(dict(body.get("payload") or {})),
                    "mode": mode.value,
                    "at": utc_now_iso(),
                    "mock": False,
                }
                with self.store._lock:
                    self.store.data["telemetry"].append(entry)
                    self.store.persist()
                self._maybe_trace(
                    "telemetry",
                    mode,
                    {"gunnchos.event.type": entry["event_type"]},
                )
                return 200, entry

            if method == "POST" and route == "/v1/ota/metadata" and role_ok("ota_metadata"):
                self._allow(mode, "update_metadata")
                channel = body["channel"]
                record = {
                    "channel": channel,
                    "version": body["version"],
                    "extra": redact_payload(dict(body.get("extra") or {})),
                    "mode": mode.value,
                    "at": utc_now_iso(),
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["update_metadata"][channel] = record
                    self.store.persist()
                self._maybe_trace(
                    "update_metadata",
                    mode,
                    {"gunnchos.ota.channel": channel},
                )
                return 200, record

            if method == "GET" and route.startswith("/v1/ota/metadata/") and role_ok("ota_metadata"):
                self._allow(mode, "update_metadata")
                channel = route.split("/v1/ota/metadata/", 1)[1]
                with self.store._lock:
                    rec = self.store.data["update_metadata"].get(channel)
                if not rec:
                    return 200, {"found": False, "channel": channel, "mode": mode.value, "mock": False}
                return 200, {"found": True, **rec}

            if method == "POST" and route == "/v1/fleet/heartbeat" and role_ok("fleet"):
                # Fleet heartbeat allowed in online modes; blocked when disconnected.
                if mode == ServiceMode.DISCONNECTED:
                    raise PermissionError("capability 'fleet' unavailable in mode disconnected")
                device_id = body.get("device_id", "fleet-dev-001")
                record = {
                    "device_id": device_id,
                    "ring": body.get("ring", "dev"),
                    "health": body.get("health", "healthy"),
                    "mode": mode.value,
                    "at": utc_now_iso(),
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["fleet"][device_id] = record
                    self.store.persist()
                self._maybe_trace(
                    "fleet",
                    mode,
                    {"gunnchos.device.id": device_id, "gunnchos.fleet.ring": record["ring"]},
                )
                return 200, record

            if method == "GET" and route == "/v1/fleet/inventory" and role_ok("fleet"):
                if mode == ServiceMode.DISCONNECTED:
                    raise PermissionError("capability 'fleet' unavailable in mode disconnected")
                with self.store._lock:
                    devices = list(self.store.data["fleet"].values())
                return 200, {"devices": devices, "mode": mode.value, "mock": False}

            if method == "POST" and route == "/v1/diagnostics/report" and role_ok("diagnostics"):
                if mode == ServiceMode.DISCONNECTED:
                    # Local diagnostics still allowed offline.
                    pass
                report = {
                    "device_id": body.get("device_id", "diag-dev-001"),
                    "checks": redact_payload(dict(body.get("checks") or {"ok": True})),
                    "mode": mode.value,
                    "at": utc_now_iso(),
                    "mock": False,
                    "claim_boundary": CLAIM_BOUNDARY,
                }
                with self.store._lock:
                    self.store.data["diagnostics"].append(report)
                    self.store.persist()
                self._maybe_trace("diagnostics", mode, {"gunnchos.device.id": report["device_id"]})
                return 200, report

            if method == "GET" and route == "/v1/diagnostics/list" and role_ok("diagnostics"):
                with self.store._lock:
                    items = list(self.store.data["diagnostics"][-50:])
                return 200, {"reports": items, "mode": mode.value, "mock": False}

        except PermissionError as exc:
            return 403, {"error": str(exc), "mode": mode.value, "mock": False}
        except KeyError as exc:
            return 400, {"error": f"missing field: {exc}", "mock": False}

        return 404, {"error": f"no route {method} {route} for role {self.role}", "mock": False}


def make_handler(app: DevPlaneApp) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
            return

        def _read_json(self) -> dict[str, Any]:
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return {}
            raw = self.rfile.read(length)
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))

        def _respond(self, status: int, payload: dict[str, Any]) -> None:
            body = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self) -> None:  # noqa: N802
            headers = {k.lower(): v for k, v in self.headers.items()}
            status, payload = app.handle("GET", self.path, headers, {})
            self._respond(status, payload)

        def do_POST(self) -> None:  # noqa: N802
            headers = {k.lower(): v for k, v in self.headers.items()}
            try:
                body = self._read_json()
            except json.JSONDecodeError:
                self._respond(400, {"error": "invalid json", "mock": False})
                return
            status, payload = app.handle("POST", self.path, headers, body)
            self._respond(status, payload)

    return Handler


class DevPlaneServer:
    """Background ThreadingHTTPServer wrapper for tests and local launch."""

    def __init__(
        self,
        app: DevPlaneApp | None = None,
        host: str = "127.0.0.1",
        port: int = 0,
    ) -> None:
        self.app = app or DevPlaneApp()
        self._httpd = ThreadingHTTPServer((host, port), make_handler(self.app))
        self.host, self.port = self._httpd.server_address[:2]
        self._thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def start(self) -> "DevPlaneServer":
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread:
            self._thread.join(timeout=2.0)


def serve_forever_from_env() -> None:
    role = os.environ.get("GUNNCHOS_SERVICE", "gateway")
    port = int(os.environ.get("GUNNCHOS_PORT", DEFAULT_PORTS.get(role, 8100)))
    store_path = os.environ.get("GUNNCHOS_STORE_PATH", "/tmp/gunnchos-dev-plane-store.json")
    mode = ServiceMode(os.environ.get("GUNNCHOS_MODE", "local").lower())
    otel_ep = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:4318/v1/traces")
    store = DevPlaneStore(store_path)
    otel = OtelRoundTrip(endpoint=otel_ep)
    app = DevPlaneApp(store, default_mode=mode, otel=otel, role=role)
    server = DevPlaneServer(app, host="0.0.0.0", port=port)
    print(
        json.dumps(
            {
                "listening": server.base_url,
                "role": role,
                "realm": REALM,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        ),
        flush=True,
    )
    try:
        server._httpd.serve_forever()
    except KeyboardInterrupt:
        server.stop()
