"""Companion HTML shells ↔ gunnchSDK first-party sandbox I/O bridge.

Serves apps/{creator_studio,waike_learning,gunnchai_tutor} and exposes JSON
APIs that invoke the same ``run_*`` entrypoints used by sdk/apps package
lifecycle dogfood. Digital platform integration only — not production hosting,
not frontier model quality, not HUMAN_E6.
"""
from __future__ import annotations

import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from gunnchos_device_os.first_party_apps.creator_studio import run_creator_studio
from gunnchos_device_os.first_party_apps.gunnchai_tutor import run_gunnchai_tutor
from gunnchos_device_os.first_party_apps.waike_app import run_waike_app

CLAIM_BOUNDARY = (
    "Local companion bridge wiring HTML shells to first_party gunnchSDK sandbox "
    "I/O. Not production CDN hosting, not store distribution, not HUMAN_E6."
)

APP_STATIC = {
    "creator_studio": "apps/creator_studio",
    "waike_learning": "apps/waike_learning",
    "gunnchai_tutor": "apps/gunnchai_tutor",
}

MIME = {
    ".html": "text/html; charset=utf-8",
    ".js": "application/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
}


def _json_bytes(payload: Any, *, status: int = 200) -> tuple[int, bytes, str]:
    body = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return status, body, "application/json; charset=utf-8"


def _read_json_body(handler: BaseHTTPRequestHandler) -> dict[str, Any]:
    length = int(handler.headers.get("Content-Length") or 0)
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        data = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def _ensure_runtime_env(data_dir: Path, *, app_id: str) -> None:
    os.environ["GUNNCHOS_SANDBOX_DATA_DIR"] = str(data_dir)
    os.environ.setdefault(
        "GUNNCHOS_APP_PERMISSIONS",
        "storage_read,storage_write,ai_interface",
    )
    os.environ["GUNNCHOS_APP_ID"] = app_id
    os.environ.setdefault("GUNNCHOS_APP_VERSION", "0.3.1")
    os.environ.setdefault("GUNNCHOS_SANDBOX_NETWORK_POLICY", "deny_all")


def make_handler(repo_root: Path, data_dir: Path) -> type[BaseHTTPRequestHandler]:
    root = Path(repo_root).resolve()
    sandbox = Path(data_dir).resolve()
    sandbox.mkdir(parents=True, exist_ok=True)

    class CompanionBridgeHandler(BaseHTTPRequestHandler):
        server_version = "gunnchos-companion-bridge/1.0"

        def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
            # Keep dogfood/CI quiet unless debugging.
            return

        def _send(self, status: int, body: bytes, content_type: str) -> None:
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(body)

        def do_OPTIONS(self) -> None:  # noqa: N802
            self._send(204, b"", "text/plain")

        def do_GET(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            if path in ("/", "/api/health"):
                status, body, ctype = _json_bytes(
                    {
                        "ok": True,
                        "service": "companion_bridge",
                        "wired": True,
                        "sandbox_data_dir": str(sandbox),
                        "apps": sorted(APP_STATIC),
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                )
                self._send(status, body, ctype)
                return
            if path == "/api/gunnchai/memory":
                _ensure_runtime_env(sandbox, app_id="gunnchos.gunnchai_tutor")
                mem_path = sandbox / "tutor_memory.json"
                memory = {}
                if mem_path.exists():
                    memory = json.loads(mem_path.read_text(encoding="utf-8"))
                status, body, ctype = _json_bytes(
                    {
                        "ok": True,
                        "wired": True,
                        "source": "sandbox_tutor_memory",
                        "memory": memory,
                        "path": str(mem_path),
                    }
                )
                self._send(status, body, ctype)
                return
            if path == "/api/creator/state":
                _ensure_runtime_env(sandbox, app_id="gunnchos.creator_studio")
                state_path = sandbox / "creator_state.json"
                state = {}
                if state_path.exists():
                    state = json.loads(state_path.read_text(encoding="utf-8"))
                status, body, ctype = _json_bytes(
                    {"ok": True, "wired": True, "state": state, "path": str(state_path)}
                )
                self._send(status, body, ctype)
                return
            if path == "/api/waike/progress":
                _ensure_runtime_env(sandbox, app_id="gunnchos.waike_learning")
                progress_path = sandbox / "waike_progress.json"
                state_path = sandbox / "waike_app_state.json"
                portfolio_path = sandbox / "waike_portfolio.json"
                payload = {
                    "ok": True,
                    "wired": True,
                    "progress": (
                        json.loads(progress_path.read_text(encoding="utf-8"))
                        if progress_path.exists()
                        else {}
                    ),
                    "app_state": (
                        json.loads(state_path.read_text(encoding="utf-8"))
                        if state_path.exists()
                        else {}
                    ),
                    "portfolio": (
                        json.loads(portfolio_path.read_text(encoding="utf-8"))
                        if portfolio_path.exists()
                        else {}
                    ),
                }
                status, body, ctype = _json_bytes(payload)
                self._send(status, body, ctype)
                return

            # Static companion shells: /apps/<name>/...
            if path.startswith("/apps/"):
                rel = path[len("/apps/") :]
                parts = rel.split("/", 1)
                if not parts or parts[0] not in APP_STATIC:
                    self._send(404, b'{"ok":false,"error":"not_found"}\n', "application/json")
                    return
                app_name = parts[0]
                rest = parts[1] if len(parts) > 1 else "index.html"
                if rest.endswith("/") or rest == "":
                    rest = "index.html"
                file_path = (root / APP_STATIC[app_name] / rest).resolve()
                app_root = (root / APP_STATIC[app_name]).resolve()
                if not str(file_path).startswith(str(app_root)) or not file_path.is_file():
                    self._send(404, b'{"ok":false,"error":"not_found"}\n', "application/json")
                    return
                data = file_path.read_bytes()
                ctype = MIME.get(file_path.suffix.lower(), "application/octet-stream")
                self._send(200, data, ctype)
                return

            self._send(404, b'{"ok":false,"error":"not_found"}\n', "application/json")

        def do_POST(self) -> None:  # noqa: N802
            path = urlparse(self.path).path
            body_in = _read_json_body(self)
            try:
                if path == "/api/creator/run":
                    _ensure_runtime_env(sandbox, app_id="gunnchos.creator_studio")
                    layout = str(body_in.get("layout") or "single")
                    result = run_creator_studio(layout=layout)
                    payload = {
                        "ok": bool(result.get("ok")),
                        "wired": True,
                        "runtime": "first_party_apps.creator_studio",
                        "action": "run_build_assist",
                        "result": result,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                    status, body, ctype = _json_bytes(payload, status=200 if payload["ok"] else 400)
                    self._send(status, body, ctype)
                    return
                if path == "/api/waike/start":
                    _ensure_runtime_env(sandbox, app_id="gunnchos.waike_learning")
                    lesson_id = str(body_in.get("lesson_id") or "wireless_basics_101")
                    role = str(body_in.get("role") or "learner")
                    result = run_waike_app(lesson_id=lesson_id, role=role)
                    payload = {
                        "ok": bool(result.get("ok")),
                        "wired": True,
                        "runtime": "first_party_apps.waike_app",
                        "action": "start_lesson",
                        "result": result,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                    status, body, ctype = _json_bytes(payload, status=200 if payload["ok"] else 400)
                    self._send(status, body, ctype)
                    return
                if path == "/api/gunnchai/ask":
                    _ensure_runtime_env(sandbox, app_id="gunnchos.gunnchai_tutor")
                    prompt = str(body_in.get("prompt") or "").strip()
                    if not prompt:
                        status, body, ctype = _json_bytes(
                            {
                                "ok": False,
                                "wired": True,
                                "error": "empty_prompt",
                                "degraded": False,
                            },
                            status=400,
                        )
                        self._send(status, body, ctype)
                        return
                    profile = str(body_in.get("profile") or "student")
                    topic = str(body_in.get("topic") or "general")
                    lesson = body_in.get("lesson")
                    bind = str(lesson) if lesson else None
                    result = run_gunnchai_tutor(
                        profile=profile,
                        topic=topic,
                        prompt=prompt,
                        bind_waike_lesson=bind,
                    )
                    payload = {
                        "ok": bool(result.get("ok")),
                        "wired": True,
                        "runtime": "first_party_apps.gunnchai_tutor",
                        "continuity": "SDK_SANDBOX_MEMORY",
                        "action": "ask",
                        "result": result,
                        "claim_boundary": CLAIM_BOUNDARY,
                    }
                    # Prompt blocked is an honest fail-closed outcome, still wired.
                    http_status = 200 if payload["ok"] or result.get("error") == "prompt_blocked" else 400
                    if result.get("error") == "prompt_blocked":
                        payload["ok"] = False
                        http_status = 403
                    status, body, ctype = _json_bytes(payload, status=http_status)
                    self._send(status, body, ctype)
                    return
            except Exception as exc:  # noqa: BLE001 — surface as fail-closed API error
                status, body, ctype = _json_bytes(
                    {
                        "ok": False,
                        "wired": True,
                        "error": "runtime_exception",
                        "detail": str(exc),
                        "claim_boundary": CLAIM_BOUNDARY,
                    },
                    status=500,
                )
                self._send(status, body, ctype)
                return

            self._send(404, b'{"ok":false,"error":"not_found"}\n', "application/json")

    return CompanionBridgeHandler


def start_bridge(
    repo_root: Path,
    data_dir: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> tuple[ThreadingHTTPServer, str]:
    handler = make_handler(repo_root, data_dir)
    server = ThreadingHTTPServer((host, port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    bound = server.server_address[1]
    base = f"http://{host}:{bound}"
    return server, base


def prove_companion_shell_wiring(
    repo_root: Path,
    work: Path,
) -> dict[str, Any]:
    """Digitally prove companion shells invoke first_party sandbox I/O."""
    import urllib.error
    import urllib.request

    data_dir = work / "companion_sandbox"
    data_dir.mkdir(parents=True, exist_ok=True)
    server, base = start_bridge(repo_root, data_dir)
    evidence: dict[str, Any] = {
        "base_url": base,
        "sandbox_data_dir": str(data_dir),
        "claim_boundary": CLAIM_BOUNDARY,
    }
    try:
        def _post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
            req = urllib.request.Request(
                base + path,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))

        def _get(path: str) -> dict[str, Any]:
            with urllib.request.urlopen(base + path, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))

        health = _get("/api/health")
        creator = _post("/api/creator/run", {"layout": "dsxl"})
        waike = _post(
            "/api/waike/start",
            {"lesson_id": "wireless_basics_101", "role": "learner"},
        )
        ask = _post(
            "/api/gunnchai/ask",
            {
                "profile": "student",
                "topic": "wireless_basics",
                "lesson": "wireless_basics_101",
                "prompt": "Explain OFDM at a high level",
            },
        )
        memory = _get("/api/gunnchai/memory")
        creator_state = _get("/api/creator/state")
        waike_progress = _get("/api/waike/progress")

        # Shell sources must call bridge APIs (not mock-only).
        shell_checks = {}
        for name, needle in (
            ("creator_studio", "/api/creator/run"),
            ("waike_learning", "/api/waike/start"),
            ("gunnchai_tutor", "/api/gunnchai/ask"),
        ):
            app_js = (repo_root / "apps" / name / "app.js").read_text(encoding="utf-8")
            shell_checks[name] = {
                "calls_bridge_api": needle in app_js,
                "no_disconnected_preview_success": "DISCONNECTED_PREVIEW" not in app_js
                or "RUNTIME_UNAVAILABLE" in app_js,
            }

        sandbox_files = {
            "creator_state": (data_dir / "creator_state.json").exists(),
            "creator_run": (data_dir / "creator_studio_run.json").exists(),
            "waike_state": (data_dir / "waike_app_state.json").exists(),
            "waike_run": (data_dir / "waike_learning_run.json").exists(),
            "tutor_memory": (data_dir / "tutor_memory.json").exists(),
            "tutor_run": (data_dir / "gunnchai_tutor_run.json").exists(),
            "app_runtime_log": (data_dir / "app_runtime.log").exists(),
        }

        ask_continuity = ask.get("continuity") == "SDK_SANDBOX_MEMORY" and bool(
            (memory.get("memory") or {}).get("turns")
        )
        ok = all(
            [
                health.get("ok") and health.get("wired"),
                creator.get("ok") and creator.get("wired"),
                waike.get("ok") and waike.get("wired"),
                ask.get("ok") and ask.get("wired") and ask_continuity,
                all(sandbox_files.values()),
                all(v["calls_bridge_api"] for v in shell_checks.values()),
                shell_checks["gunnchai_tutor"]["no_disconnected_preview_success"],
                bool((creator_state.get("state") or {}).get("run_count")),
                bool(waike_progress.get("app_state")),
            ]
        )
        evidence.update(
            {
                "ok": ok,
                "health": {"ok": health.get("ok"), "wired": health.get("wired")},
                "creator": {
                    "ok": creator.get("ok"),
                    "wired": creator.get("wired"),
                    "runtime": creator.get("runtime"),
                    "persisted_run_count": (creator.get("result") or {}).get(
                        "persisted_run_count"
                    ),
                },
                "waike": {
                    "ok": waike.get("ok"),
                    "wired": waike.get("wired"),
                    "runtime": waike.get("runtime"),
                    "persisted_progress_pct": (waike.get("result") or {}).get(
                        "persisted_progress_pct"
                    ),
                },
                "gunnchai": {
                    "ok": ask.get("ok"),
                    "wired": ask.get("wired"),
                    "continuity": ask.get("continuity"),
                    "runtime": ask.get("runtime"),
                    "memory_turns": len((memory.get("memory") or {}).get("turns") or []),
                },
                "sandbox_files": sandbox_files,
                "shell_source_checks": shell_checks,
                "proved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
        )
        return evidence
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
        evidence["ok"] = False
        evidence["error"] = str(exc)
        return evidence
    finally:
        server.shutdown()
        server.server_close()
