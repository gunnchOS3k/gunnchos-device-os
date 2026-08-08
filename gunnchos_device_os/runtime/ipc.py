"""Process-local Unix socket + HTTP IPC for gunnchOS digital runtime services.

This is real cross-process IPC (AF_UNIX stream sockets and optional local HTTP),
not in-process-only method calls. Realm: DEV. Not a production bus.
"""
from __future__ import annotations

from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable
import json
import os
import socket
import threading
import time
import urllib.error
import urllib.request


CLAIM_BOUNDARY = (
    "DEV-realm local IPC only (Unix socket / local HTTP). Not D-Bus, not gRPC "
    "production mesh, not FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE."
)

TOKEN_IPC_PASS = "GUNNCHOS_RUNTIME_IPC_DIGITAL_PASS"


HandlerFn = Callable[[dict[str, Any]], dict[str, Any]]


@dataclass
class IpcEndpoints:
    service_id: str
    socket_path: Path
    http_port: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_id": self.service_id,
            "socket_path": str(self.socket_path),
            "http_port": self.http_port,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def _recv_line(conn: socket.socket, limit: int = 1_000_000) -> bytes:
    buf = bytearray()
    while len(buf) < limit:
        chunk = conn.recv(4096)
        if not chunk:
            break
        buf.extend(chunk)
        if b"\n" in chunk:
            break
    return bytes(buf)


class UnixSocketIpcServer:
    """JSON-line request/response server on an AF_UNIX stream socket."""

    def __init__(self, path: str | Path, handler: HandlerFn) -> None:
        self.path = Path(path)
        self.handler = handler
        self._sock: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()

    def start(self) -> "UnixSocketIpcServer":
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.exists():
            self.path.unlink()
        self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._sock.bind(str(self.path))
        self._sock.listen(16)
        self._sock.settimeout(0.3)
        self._stop.clear()
        self._thread = threading.Thread(target=self._serve, name=f"ipc-{self.path.name}", daemon=True)
        self._thread.start()
        return self

    def _serve(self) -> None:
        assert self._sock is not None
        while not self._stop.is_set():
            try:
                conn, _ = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            with conn:
                try:
                    raw = _recv_line(conn)
                    if not raw:
                        continue
                    req = json.loads(raw.decode("utf-8"))
                    resp = self.handler(req)
                except Exception as exc:  # noqa: BLE001
                    resp = {"ok": False, "error": str(exc), "mock": False}
                conn.sendall((json.dumps(resp, default=str) + "\n").encode("utf-8"))

    def stop(self) -> None:
        self._stop.set()
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None
        if self.path.exists():
            try:
                self.path.unlink()
            except OSError:
                pass


def unix_call(path: str | Path, payload: dict[str, Any], *, timeout: float = 2.0) -> dict[str, Any]:
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect(str(path))
        sock.sendall((json.dumps(payload, default=str) + "\n").encode("utf-8"))
        raw = _recv_line(sock)
        return json.loads(raw.decode("utf-8"))
    finally:
        sock.close()


class LocalHttpIpcServer:
    """Minimal local HTTP JSON IPC surface bound to 127.0.0.1."""

    def __init__(self, handler: HandlerFn, host: str = "127.0.0.1", port: int = 0) -> None:
        self.handler = handler
        self._httpd = ThreadingHTTPServer((host, port), self._make_handler())
        self.host, self.port = self._httpd.server_address[:2]
        self._thread: threading.Thread | None = None

    def _make_handler(self) -> type[BaseHTTPRequestHandler]:
        app = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
                return

            def do_POST(self) -> None:  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length) if length else b"{}"
                try:
                    req = json.loads(raw.decode("utf-8") or "{}")
                    resp = app.handler(req)
                    status = 200
                except Exception as exc:  # noqa: BLE001
                    resp = {"ok": False, "error": str(exc), "mock": False}
                    status = 400
                body = json.dumps(resp, default=str).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path.rstrip("/") in ("/health", "/v1/health"):
                    body = json.dumps({"ok": True, "ipc": "local_http", "mock": False}).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                    return
                self.send_response(404)
                self.end_headers()

        return Handler

    def start(self) -> "LocalHttpIpcServer":
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        self._httpd.shutdown()
        self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2)
            self._thread = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"


def http_call(base_url: str, payload: dict[str, Any], *, timeout: float = 2.0) -> dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/v1/call",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"ok": False, "error": body, "mock": False}


class ServiceIpcFacade:
    """Expose a RuntimeService over Unix socket (+ optional local HTTP)."""

    def __init__(
        self,
        service: Any,
        *,
        socket_dir: str | Path,
        enable_http: bool = True,
    ) -> None:
        self.service = service
        self.socket_path = Path(socket_dir) / f"{service.service_id}.sock"
        self._unix = UnixSocketIpcServer(self.socket_path, self._handle)
        self._http: LocalHttpIpcServer | None = None
        self.enable_http = enable_http

    def _handle(self, req: dict[str, Any]) -> dict[str, Any]:
        op = str(req.get("op") or "call")
        if op == "health":
            return {
                "ok": True,
                "service_id": self.service.service_id,
                "health": self.service.health_check(),
                "state": self.service.state.value,
                "ipc": "unix_socket",
                "mock": False,
            }
        if op == "status":
            return {"ok": True, **self.service.status().to_dict(), "mock": False}
        if op == "call":
            method = str(req["method"])
            kwargs = dict(req.get("kwargs") or {})
            result = self.service.api(method, **kwargs)
            return {
                "ok": True,
                "service_id": self.service.service_id,
                "method": method,
                "result": result,
                "ipc": "unix_socket",
                "mock": False,
            }
        return {"ok": False, "error": f"unknown op {op}", "mock": False}

    def start(self) -> IpcEndpoints:
        self._unix.start()
        port = None
        if self.enable_http:
            self._http = LocalHttpIpcServer(self._handle).start()
            port = int(self._http.port)
        return IpcEndpoints(self.service.service_id, self.socket_path, port)

    def stop(self) -> None:
        if self._http is not None:
            self._http.stop()
            self._http = None
        self._unix.stop()


class IpcRuntimePlane:
    """Start selected runtime services and expose them via real process IPC."""

    def __init__(self, *, socket_dir: str | Path | None = None, enable_http: bool = True) -> None:
        root = Path(socket_dir or (Path(os.environ.get("TMPDIR", "/tmp")) / "gunnchos-ipc"))
        self.socket_dir = root
        self.socket_dir.mkdir(parents=True, exist_ok=True)
        self.enable_http = enable_http
        self.facades: dict[str, ServiceIpcFacade] = {}
        self.endpoints: dict[str, IpcEndpoints] = {}
        self.services: dict[str, Any] = {}

    def start_services(self, service_ids: list[str] | None = None) -> dict[str, Any]:
        from gunnchos_device_os.runtime.adapters import build_service
        from gunnchos_device_os.runtime.catalog import REQUIRED_SERVICE_IDS
        from gunnchos_device_os.runtime.service_base import ServiceConfig

        ids = list(service_ids or REQUIRED_SERVICE_IDS)
        for sid in ids:
            cfg = ServiceConfig(
                service_id=sid,
                persistence_path=str(self.socket_dir / f"{sid}.json"),
            )
            svc = build_service(sid, cfg)
            svc.start()
            facade = ServiceIpcFacade(svc, socket_dir=self.socket_dir, enable_http=self.enable_http)
            ep = facade.start()
            self.services[sid] = svc
            self.facades[sid] = facade
            self.endpoints[sid] = ep
        return {
            "started": list(self.endpoints.keys()),
            "endpoints": {k: v.to_dict() for k, v in self.endpoints.items()},
            "token": TOKEN_IPC_PASS,
            "claim_boundary": CLAIM_BOUNDARY,
            "full_gunnchos_platform_digital_complete": False,
            "mock": False,
        }

    def call(self, service_id: str, method: str, **kwargs: Any) -> Any:
        ep = self.endpoints[service_id]
        resp = unix_call(ep.socket_path, {"op": "call", "method": method, "kwargs": kwargs})
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error") or "ipc call failed")
        return resp["result"]

    def call_http(self, service_id: str, method: str, **kwargs: Any) -> Any:
        ep = self.endpoints[service_id]
        if not ep.http_port:
            raise RuntimeError("http ipc not enabled")
        resp = http_call(
            f"http://127.0.0.1:{ep.http_port}",
            {"op": "call", "method": method, "kwargs": kwargs},
        )
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error") or "http ipc call failed")
        return resp["result"]

    def cross_call_probe(self) -> dict[str, Any]:
        """Prove cross-service calls over Unix socket IPC."""
        profiles = self.call("hal", "list_profiles")
        who = self.call("identity", "create_account", display_name="IpcProbe", email="ipc@dev.local")
        logged = self.call("diagnostics", "log", level="info", message="ipc_probe", source="hal")
        queried = self.call("diagnostics", "query", limit=5)
        enroll = self.call("fleet_agent", "enroll", enrollment_token="DEV_ENROLLMENT_TOKEN")
        fleet = self.call("fleet_agent", "heartbeat")
        ok = (
            bool(profiles)
            and bool(who.get("account_id"))
            and bool(logged)
            and isinstance(queried, list)
            and bool(enroll.get("enrolled"))
            and bool(fleet.get("ok"))
        )
        return {
            "ok": ok,
            "profiles": profiles,
            "identity": who,
            "diagnostics": {"logged": logged, "query": queried},
            "fleet": {"enroll": enroll, "heartbeat": fleet},
            "transport": "unix_socket",
            "token": TOKEN_IPC_PASS if ok else None,
            "claim_boundary": CLAIM_BOUNDARY,
            "full_gunnchos_platform_digital_complete": False,
            "mock": False,
        }

    def stop(self) -> None:
        for facade in self.facades.values():
            facade.stop()
        for svc in self.services.values():
            try:
                svc.stop()
            except Exception:  # noqa: BLE001
                pass
        self.facades.clear()
        self.endpoints.clear()
        self.services.clear()


def wait_brief(seconds: float = 0.05) -> None:
    time.sleep(seconds)
