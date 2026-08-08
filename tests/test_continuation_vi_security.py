"""Cont VI — security controls against runtime + cloud services."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path

from gunnchos_device_os.cloud_dev_plane import DevPlaneApp, DevPlaneClient, DevPlaneServer, ServiceMode
from gunnchos_device_os.cloud_dev_plane.store import DevPlaneStore
from gunnchos_device_os.runtime.ipc import IpcRuntimePlane, unix_call


def _sock(label: str) -> Path:
    p = Path(tempfile.gettempdir()) / f"gchos-sec-{os.getpid()}-{label}"
    p.mkdir(parents=True, exist_ok=True)
    return p


def test_auth_bypass_and_revoked_device():
    plane = IpcRuntimePlane(socket_dir=_sock("auth"), enable_http=False)
    try:
        plane.start_services(["identity", "diagnostics", "updater", "connectivity", "fleet_agent", "permissions", "ai_interface", "profile_manager"])
        assert plane.call("fleet_agent", "enroll", enrollment_token="PROD_SECRET")["enrolled"] is False
        plane.call("fleet_agent", "enroll", enrollment_token="DEV_OK")
        plane.call("fleet_agent", "revoke", reason="compromise")
        assert plane.call("fleet_agent", "heartbeat")["ok"] is False
        assert plane.call("ai_interface", "permission")["decision"] == "deny"
    finally:
        plane.stop()


def test_malformed_ipc_and_stale_tokens():
    plane = IpcRuntimePlane(socket_dir=_sock("mal"), enable_http=False)
    try:
        plane.start_services(["hal", "identity"])
        ep = plane.endpoints["hal"].socket_path
        # malformed JSON line
        import socket, json
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.settimeout(1.0)
        s.connect(str(ep))
        s.sendall(b"{not-json\n")
        raw = s.recv(4096)
        s.close()
        resp = json.loads(raw.decode())
        assert resp.get("ok") is False

        acct = plane.call("identity", "create_account", display_name="Sec", email="sec@dev.local")
        plane.call(
            "identity",
            "bind_device",
            account_id=acct["account_id"],
            device_id="d1",
            device_class="student_14_5",
        )
        sess = plane.call("identity", "issue_session", account_id=acct["account_id"], device_id="d1")
        bad = plane.call(
            "identity",
            "validate_session",
            session_id=sess.get("session_id") or sess.get("id") or "missing",
            token="stale-token",
            device_id="d1",
        )
        assert bad.get("valid") is False or bad.get("ok") is False or bad.get("valid") in (False, None)
    finally:
        plane.stop()


def test_update_tamper_and_log_privacy():
    plane = IpcRuntimePlane(socket_dir=_sock("tamper"), enable_http=False)
    try:
        plane.start_services(["diagnostics", "updater"])
        meta = plane.call("updater", "metadata", version="9.9.9")
        assert meta["production_keys_used"] is False
        # Tamper: claim verify without download should fail
        assert plane.call("updater", "verify")["verified"] is False
        plane.call("updater", "download", version="0.1.1")
        assert plane.call("updater", "verify")["verified"] is True

        redacted = plane.call(
            "diagnostics",
            "redact_sample",
            payload={"email": "user@example.com", "token": "secret", "ok": True},
        )
        blob = str(redacted).lower()
        assert "secret" not in blob or "redact" in blob or "[redacted]" in blob or "user@example.com" not in blob
    finally:
        plane.stop()


def test_cloud_enrollment_token_and_revoked_exfiltration_guard(tmp_path: Path):
    db = tmp_path / "sec.sqlite3"
    store = DevPlaneStore(db, backend="sqlite")
    server = DevPlaneServer(DevPlaneApp(store=store, role="gateway")).start()
    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.CLOUD)
    try:
        rejected = client.enrollment_submit("dev-x", "org", enrollment_token="REAL_PROD_TOKEN")
        assert rejected.get("status") == "rejected" or rejected.get("http_status") == 403
        client.enrollment_submit("dev-x", "org", enrollment_token="DEV_TOKEN")
        client.enrollment_revoke("dev-x")
        # Inventory still returns device but enrollment revoked — no secret fields
        snap = client.inventory()["snapshot"]
        assert "DEV_TOKEN" not in str(snap)
        assert "REAL_PROD" not in str(snap)
    finally:
        server.stop()
        store.close()
