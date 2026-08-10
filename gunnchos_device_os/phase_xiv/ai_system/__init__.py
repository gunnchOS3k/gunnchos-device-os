"""OS AI System API — apps call OS capabilities, never raw model paths.

Capabilities: summarize/translate/tutor/code/search/reason/diagnose/classify.
Routes through local_ai runtime and optional gunnchAI HTTP router.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
from typing import Any, Callable
from urllib.parse import urlparse

CAPABILITIES = (
    "summarize",
    "translate",
    "tutor",
    "code",
    "search",
    "reason",
    "diagnose",
    "classify",
)


@dataclass
class AiRequest:
    capability: str
    input: str
    user_id: str = "u_demo"
    cloud_consent: bool = False
    grant: list[str] = field(default_factory=list)
    timeout_s: float = 30.0


@dataclass
class AiResponse:
    ok: bool
    capability: str
    user_id: str
    text: str
    route: dict[str, Any] = field(default_factory=dict)
    source: str = "os_ai_system"
    model_path_exposed: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "capability": self.capability,
            "user_id": self.user_id,
            "text": self.text,
            "route": self.route,
            "source": self.source,
            "model_path_exposed": self.model_path_exposed,
        }


class OsAiSystemApi:
    """Production OS client/service surface."""

    def __init__(
        self,
        *,
        local_runtime: Any | None = None,
        gunnchai_base: str | None = None,
    ):
        self.local_runtime = local_runtime
        self.gunnchai_base = (gunnchai_base or "").rstrip("/") or None
        self._handlers: dict[str, Callable[[AiRequest], AiResponse]] = {
            c: self._default_capability for c in CAPABILITIES
        }

    def list_capabilities(self) -> list[str]:
        return list(CAPABILITIES)

    def invoke(self, req: AiRequest) -> AiResponse:
        if req.capability not in CAPABILITIES:
            return AiResponse(
                ok=False,
                capability=req.capability,
                user_id=req.user_id,
                text=f"unknown capability: {req.capability}",
                route={"error": "unknown_capability"},
            )
        # Prefer local OS runtime; optionally forward to gunnchAI router.
        if self.local_runtime is not None:
            result = self.local_runtime.run_capability(
                req.capability, req.input, timeout_s=req.timeout_s
            )
            # Strip any absolute model paths from public response
            route = {
                k: v
                for k, v in (result.get("route") or {}).items()
                if k not in ("model_path", "absolute_path")
            }
            route["tier"] = result.get("tier")
            route["runtime"] = result.get("runtime")
            return AiResponse(
                ok=bool(result.get("ok")),
                capability=req.capability,
                user_id=req.user_id,
                text=str(result.get("text") or ""),
                route=route,
                source="os_local_ai",
                model_path_exposed=False,
            )
        if self.gunnchai_base:
            return self._forward_gunnchai(req)
        return self._handlers[req.capability](req)

    def _default_capability(self, req: AiRequest) -> AiResponse:
        return AiResponse(
            ok=False,
            capability=req.capability,
            user_id=req.user_id,
            text="no local runtime or gunnchAI router configured",
            route={"error": "no_backend"},
        )

    def _forward_gunnchai(self, req: AiRequest) -> AiResponse:
        assert self.gunnchai_base
        url = f"{self.gunnchai_base}/v1/capability/{req.capability}"
        body = json.dumps(
            {
                "user_id": req.user_id,
                "input": req.input,
                "cloudConsent": req.cloud_consent,
                "grant": req.grant,
            }
        ).encode()
        request = urllib.request.Request(
            url,
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=req.timeout_s) as resp:
                data = json.loads(resp.read().decode())
            return AiResponse(
                ok=bool(data.get("ok")),
                capability=req.capability,
                user_id=req.user_id,
                text=str(data.get("text") or ""),
                route={"via": "gunnchai", "raw_ok": data.get("ok")},
                source="gunnchai_router",
                model_path_exposed=False,
            )
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            return AiResponse(
                ok=False,
                capability=req.capability,
                user_id=req.user_id,
                text=f"gunnchai forward failed: {exc}",
                route={"error": "gunnchai_unreachable"},
            )


class _Handler(BaseHTTPRequestHandler):
    api: OsAiSystemApi

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/health":
            self._json(200, {"ok": True, "service": "gunnchos-os-ai-system"})
            return
        if path == "/v1/capabilities":
            self._json(200, {"capabilities": self.api.list_capabilities()})
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if not path.startswith("/v1/capability/"):
            self._json(404, {"ok": False, "error": "not_found"})
            return
        name = path.rsplit("/", 1)[-1]
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            parsed = json.loads(raw.decode() or "{}")
        except json.JSONDecodeError:
            self._json(400, {"ok": False, "error": "bad_json"})
            return
        req = AiRequest(
            capability=name,
            input=str(parsed.get("input") or ""),
            user_id=str(parsed.get("user_id") or "anonymous"),
            cloud_consent=bool(parsed.get("cloudConsent")),
            grant=list(parsed.get("grant") or []),
        )
        result = self.api.invoke(req)
        self._json(200 if result.ok else 503, result.to_dict())


def start_os_ai_server(api: OsAiSystemApi, port: int = 0) -> tuple[ThreadingHTTPServer, int]:
    class Bound(_Handler):
        pass

    Bound.api = api
    server = ThreadingHTTPServer(("127.0.0.1", port), Bound)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, int(server.server_address[1])
