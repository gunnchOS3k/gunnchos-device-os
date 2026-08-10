"""Live guest framebuffer path — QEMU VNC (+ optional WebSocket) → Lab UI.

Not screenshot-only. Proves a live RFB/WebSocket endpoint or returns
SKIPPED_ENVIRONMENT honestly when QEMU/display tooling is absent.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


CLAIM = (
    "Live Lab display is QEMU VNC/WebSocket pixels for a virt machine — "
    "not physical panel measurement. SILICON_EXACT_EMULATION=false. "
    "fake_screenshot_only must remain false when this path is claimed."
)


def _port_open(host: str, port: int, *, timeout: float = 0.4) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_vnc_endpoint(host: str, port: int) -> dict[str, Any]:
    """RFB handshake probe — proves a live VNC server, not a static PNG."""
    try:
        with socket.create_connection((host, port), timeout=2.0) as sock:
            sock.settimeout(2.0)
            banner = sock.recv(64)
    except OSError as exc:
        return {
            "ok": False,
            "live": False,
            "error": str(exc),
            "host": host,
            "port": port,
            "fake_screenshot_only": False,
        }
    text = banner.decode("latin-1", errors="replace")
    is_rfb = text.startswith("RFB ")
    return {
        "ok": is_rfb,
        "live": is_rfb,
        "banner": text.strip()[:32],
        "host": host,
        "port": port,
        "protocol": "rfb",
        "fake_screenshot_only": False,
        "measurement_class": "HOST_OBSERVED",
        "claim_boundary": CLAIM,
    }


@dataclass
class LiveDisplayBridge:
    """Attaches Lab UI to a QEMU VNC listen (+ optional local websockify)."""

    vnc_host: str = "127.0.0.1"
    vnc_port: int = 5907
    ws_port: int = 5707
    work: Path | None = None
    websockify_proc: subprocess.Popen[str] | None = None
    bridge_thread: threading.Thread | None = None
    _stop: threading.Event = field(default_factory=threading.Event)
    state: dict[str, Any] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        probe = probe_vnc_endpoint(self.vnc_host, self.vnc_port)
        ws_live = _port_open(self.vnc_host, self.ws_port)
        return {
            "ok": bool(probe.get("ok")),
            "kind": "vnc_websocket",
            "vnc": {"host": self.vnc_host, "port": self.vnc_port, **probe},
            "websocket": {
                "host": self.vnc_host,
                "port": self.ws_port,
                "live": ws_live,
                "url": f"ws://{self.vnc_host}:{self.ws_port}/",
            },
            "novnc_path": "/lab/novnc/",
            "ui_ready": bool(probe.get("ok")),
            "fake_screenshot_only": False,
            "SILICON_EXACT_EMULATION": False,
            "claim_boundary": CLAIM,
        }

    def start_websockify_if_available(self) -> dict[str, Any]:
        """Prefer system websockify; else mark SKIPPED for WS and keep raw VNC."""
        if _port_open(self.vnc_host, self.ws_port):
            return {"ok": True, "already_listening": True, "port": self.ws_port}
        which = None
        for cand in ("websockify", "/opt/homebrew/bin/websockify"):
            from shutil import which as _which

            if "/" in cand and Path(cand).exists():
                which = cand
                break
            w = _which(cand)
            if w:
                which = w
                break
        if which is None:
            # Try python -m websockify
            try:
                import websockify  # noqa: F401

                which = "python-module"
            except Exception:
                return {
                    "ok": False,
                    "SKIPPED_ENVIRONMENT": True,
                    "reason": "websockify_absent",
                    "note": "Raw VNC still valid live path; WS proxy optional",
                    "vnc_port": self.vnc_port,
                }
        log = (self.work / "websockify.log") if self.work else Path("/tmp/gunnch-websockify.log")
        if self.work:
            self.work.mkdir(parents=True, exist_ok=True)
        target = f"{self.vnc_host}:{self.vnc_port}"
        listen = f"{self.vnc_host}:{self.ws_port}"
        if which == "python-module":
            cmd = [
                os.environ.get("PYTHON", "python3"),
                "-m",
                "websockify",
                "--heartbeat=30",
                listen,
                target,
            ]
        else:
            cmd = [which, "--heartbeat=30", listen, target]
        try:
            self.websockify_proc = subprocess.Popen(
                cmd,
                stdout=log.open("w", encoding="utf-8"),
                stderr=subprocess.STDOUT,
                text=True,
            )
        except OSError as exc:
            return {"ok": False, "error": str(exc), "SKIPPED_ENVIRONMENT": True}
        for _ in range(30):
            if _port_open(self.vnc_host, self.ws_port):
                return {
                    "ok": True,
                    "pid": self.websockify_proc.pid,
                    "listen": listen,
                    "upstream": target,
                    "fake_screenshot_only": False,
                }
            if self.websockify_proc.poll() is not None:
                break
            time.sleep(0.1)
        return {
            "ok": False,
            "error": "websockify_did_not_listen",
            "SKIPPED_ENVIRONMENT": True,
            "log": str(log),
        }

    def stop(self) -> dict[str, Any]:
        self._stop.set()
        if self.websockify_proc and self.websockify_proc.poll() is None:
            self.websockify_proc.terminate()
            try:
                self.websockify_proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.websockify_proc.kill()
        return {"ok": True, "stopped": True}


def prove_live_display_path(
    *,
    vnc_host: str = "127.0.0.1",
    vnc_port: int,
    require_websocket: bool = False,
) -> dict[str, Any]:
    """CI/Mac honesty probe for live display."""
    probe = probe_vnc_endpoint(vnc_host, vnc_port)
    if not probe.get("ok"):
        return {
            "ok": False,
            "result": "FAIL_OR_SKIP",
            "SKIPPED_ENVIRONMENT": not _port_open(vnc_host, vnc_port),
            "probe": probe,
            "fake_screenshot_only": False,
            "note": "No live RFB endpoint — do not claim LIVE_VISUAL_PASS",
            "LIVE_VISUAL_PASS": False,
        }
    ws_port = int(os.environ.get("GUNNCHDEVICE_LAB_WS_PORT", str(vnc_port - 200)))
    ws_live = _port_open(vnc_host, ws_port)
    if require_websocket and not ws_live:
        return {
            "ok": False,
            "result": "SKIPPED_ENVIRONMENT",
            "SKIPPED_ENVIRONMENT": True,
            "probe": probe,
            "websocket_live": False,
            "LIVE_VISUAL_PASS": False,
            "note": "VNC live but websockify/WS absent",
        }
    return {
        "ok": True,
        "result": "PASS",
        "LIVE_VISUAL_PASS": True,
        "probe": probe,
        "websocket_live": ws_live,
        "fake_screenshot_only": False,
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": CLAIM,
    }


def write_display_evidence(work: Path, payload: dict[str, Any]) -> Path:
    work.mkdir(parents=True, exist_ok=True)
    path = work / "live_display_evidence.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path
