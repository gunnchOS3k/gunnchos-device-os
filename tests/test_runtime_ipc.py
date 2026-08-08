"""Host-side Unix socket / local HTTP IPC for runtime services."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from gunnchos_device_os.runtime.ipc import (
    TOKEN_IPC_PASS,
    IpcRuntimePlane,
    unix_call,
)


def _short_socket_dir(label: str) -> Path:
    """macOS AF_UNIX sun_path is short; avoid long pytest tmp paths."""
    root = Path(tempfile.gettempdir()) / f"gchos-ipc-{os.getpid()}-{label}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_unix_socket_and_http_cross_service_calls():
    sock_dir = _short_socket_dir("cross")
    plane = IpcRuntimePlane(socket_dir=sock_dir, enable_http=True)
    try:
        started = plane.start_services(
            ["hal", "identity", "diagnostics", "connectivity", "updater", "fleet_agent"]
        )
        assert started["full_gunnchos_platform_digital_complete"] is False
        assert started["token"] == TOKEN_IPC_PASS
        assert (sock_dir / "hal.sock").exists()

        probe = plane.cross_call_probe()
        assert probe["ok"] is True
        assert probe["token"] == TOKEN_IPC_PASS
        assert probe["transport"] == "unix_socket"
        assert "Student14" in probe["profiles"]

        health = unix_call(plane.endpoints["hal"].socket_path, {"op": "health"})
        assert health["ok"] is True
        assert health["ipc"] == "unix_socket"

        http_profiles = plane.call_http("hal", "list_profiles")
        assert "Student14" in http_profiles
    finally:
        plane.stop()


def test_ipc_plane_never_claims_full_platform():
    plane = IpcRuntimePlane(socket_dir=_short_socket_dir("claim"), enable_http=False)
    try:
        report = plane.start_services(["hal", "identity"])
        assert report["full_gunnchos_platform_digital_complete"] is False
        assert report.get("full_gunnchos_platform_digital_complete") is False
        assert report.get("token") == TOKEN_IPC_PASS
    finally:
        plane.stop()
