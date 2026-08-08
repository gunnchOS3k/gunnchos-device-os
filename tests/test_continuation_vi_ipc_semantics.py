"""Cont VI — service-specific IPC semantics (not health-only)."""
from __future__ import annotations

import os
import socket
import tempfile
import time
from pathlib import Path

import pytest

from gunnchos_device_os.runtime.ipc import IpcRuntimePlane, unix_call
from gunnchos_device_os.runtime.catalog import REQUIRED_SERVICE_IDS


def _sock_dir(label: str) -> Path:
    root = Path(tempfile.gettempdir()) / f"gchos-vi-{os.getpid()}-{label}"
    root.mkdir(parents=True, exist_ok=True)
    return root


def test_service_specific_request_response_and_mutation():
    plane = IpcRuntimePlane(socket_dir=_sock_dir("sem"), enable_http=False)
    try:
        plane.start_services(list(REQUIRED_SERVICE_IDS))
        inv = plane.call("hal", "inventory")
        assert inv["count"] >= 5
        assert any(i.get("sku") == "RM520N-GL" for i in inv["items"])

        power = plane.call("hal", "set_power_state", state="sleep")
        assert power["power_state"] == "sleep"
        assert plane.call("hal", "power_state")["power_state"] == "sleep"

        routed = plane.call("input", "route_event", source_id="kbd0", event="enter")
        assert routed["routed"] is True

        pair = plane.call("ring", "pair", ring_id="ring-vi")
        assert pair["paired"] is True
        assert pair["physical_ring_claimed"] is False
        assert plane.call("ring", "auth", token="DEV_RING")["authenticated"] is True

        bright = plane.call("display", "set_brightness", level=0.4)
        assert bright["brightness"] == 0.4

        dock = plane.call("dock", "simulate", dock_id="vi-dock")
        assert dock is not None
        assert plane.call("dock", "state")["docked"] is True

        handoff = plane.call(
            "continuity", "app_handoff", app_id="waike", from_device="student", to_device="dock"
        )
        assert handoff["status"] == "handed_off"
        plane.call("continuity", "save_state", save_id="s1", payload={"x": 1})
        assert plane.call("continuity", "resume", save_id="s1")["resumed"] is True
    finally:
        plane.stop()


def test_ipc_persistence_and_dependency_call(tmp_path: Path):
    sock = _sock_dir("persist")
    plane = IpcRuntimePlane(socket_dir=sock, enable_http=False)
    try:
        plane.start_services(["hal", "identity", "diagnostics", "fleet_agent", "connectivity"])
        plane.call("hal", "set_power_state", state="thermal_throttle")
        plane.call("fleet_agent", "enroll", enrollment_token="DEV_ENROLLMENT_TOKEN")
        assert (sock / "hal.json").exists()
        assert (sock / "fleet_agent.json").exists()
        # Dependency-ish cross call via diagnostics logging after fleet heartbeat
        hb = plane.call("fleet_agent", "heartbeat")
        assert hb["ok"] is True
        plane.call("diagnostics", "log", level="info", message="fleet_ok", event_type="fleet")
        rows = plane.call("diagnostics", "query", limit=5)
        assert any("fleet" in str(r).lower() or "fleet_ok" in str(r) for r in rows)
    finally:
        plane.stop()


def test_permission_rejection_timeout_and_restart():
    plane = IpcRuntimePlane(socket_dir=_sock_dir("sec"), enable_http=False)
    try:
        plane.start_services(["permissions", "identity", "sandbox", "ai_interface", "profile_manager", "diagnostics"])
        denied = plane.call("permissions", "request", app_id="evil", permission="camera", explicit_user_grant=False)
        assert denied["decision"] == "deny"

        ai_deny = plane.call("ai_interface", "permission", permission="ai_cloud_export")
        assert ai_deny["decision"] == "deny"

        # Timeout: unreachable socket path
        with pytest.raises((TimeoutError, OSError, socket.timeout, ConnectionError)):
            unix_call("/tmp/gunnchos-does-not-exist-vi.sock", {"op": "health"}, timeout=0.2)

        # Restart path: stop/start service and prove state restore from persistence
        fleet_plane = IpcRuntimePlane(socket_dir=_sock_dir("rst"), enable_http=False)
        try:
            fleet_plane.start_services(["identity", "diagnostics", "updater", "connectivity", "fleet_agent"])
            fleet_plane.call("fleet_agent", "enroll", enrollment_token="DEV_TOKEN")
            path = fleet_plane.endpoints["fleet_agent"].socket_path.parent / "fleet_agent.json"
            assert path.exists()
            # Stop and recreate from same persistence dir
            sock_dir = fleet_plane.socket_dir
            fleet_plane.stop()
            plane2 = IpcRuntimePlane(socket_dir=sock_dir, enable_http=False)
            plane2.start_services(["identity", "diagnostics", "updater", "connectivity", "fleet_agent"])
            report = plane2.call("fleet_agent", "report")
            assert report["enrolled"] is True
            plane2.stop()
        finally:
            pass
    finally:
        plane.stop()


def test_all_required_services_expose_cont_vi_surface():
    from gunnchos_device_os.runtime.adapters import SERVICE_CLASSES

    required = {
        "hal": {"inventory", "capabilities", "power_state"},
        "input": {"enumerate_sources", "route_event", "remap"},
        "ring": {"pair", "auth", "calibrate", "event_stream"},
        "display": {"outputs", "modes", "set_brightness"},
        "dock": {"state", "ethernet", "usb", "continuity_events"},
        "continuity": {"sessions", "app_handoff", "save_state", "resume"},
        "identity": {"local_account", "role", "device_identity"},
        "permissions": {"consent", "check", "app_permissions"},
        "sandbox": {"launch_policy", "filesystem", "network"},
        "connectivity": {"interfaces", "modem_rm520n", "list_bearers"},
        "ai_interface": {"local_request", "capability_route", "provenance"},
        "profile_manager": {"device_profiles", "role_profiles"},
        "a11y": {"global_preferences", "set_captions", "set_scaling"},
        "diagnostics": {"health", "hardware", "network"},
        "updater": {"download", "verify", "stage", "rollback"},
        "recovery": {"enter_recovery", "repair", "data_preservation_policy"},
        "fleet_agent": {"inventory", "command", "revoke", "update_cohort"},
    }
    for sid, methods in required.items():
        surface = set(SERVICE_CLASSES[sid].api_surface)
        missing = methods - surface
        assert not missing, f"{sid} missing {missing}"
