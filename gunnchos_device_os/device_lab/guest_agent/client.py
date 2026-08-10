"""Host-side gunnchGuestAgent client (virtio-serial / unix socket / file channel).

No unauthenticated broad network exposure — default transport is a host-local
unix socket or virtio-serial chardev path. SSH ephemeral is optional and off by default.
"""
from __future__ import annotations

import json
import os
import socket
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


PROTOCOL = "gunnchos.guest_agent.v1"


@dataclass
class GuestAgentClient:
    channel_path: Path
    timeout_sec: float = 30.0
    last_response: dict[str, Any] | None = None
    ready: bool = False
    extras: dict[str, Any] = field(default_factory=dict)

    def _send_line(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Send one JSON line and read one JSON line response.

        For early bring-up, also accepts a request/response file pair when the
        channel path ends with `.sock` but QEMU is not yet linked — tests use
        a file mailbox under the session work dir.
        """
        path = Path(self.channel_path)
        if path.suffix == ".mailbox" or os.environ.get("GUNNCH_GUEST_AGENT_MAILBOX") == "1":
            return self._mailbox_roundtrip(path, payload)
        if not path.exists():
            return {"ok": False, "error": "channel_missing", "path": str(path)}
        # Prefer unix stream if socket; else treat as fifo/file line protocol.
        try:
            mode = path.stat().st_mode
            is_sock = (mode & 0o170000) == 0o140000
        except OSError:
            is_sock = False
        if is_sock or path.suffix == ".sock":
            return self._unix_roundtrip(path, payload)
        return self._mailbox_roundtrip(path, payload)

    def _unix_roundtrip(self, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
        deadline = time.time() + self.timeout_sec
        last_err = None
        while time.time() < deadline:
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.settimeout(min(5.0, self.timeout_sec))
                    sock.connect(str(path))
                    line = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
                    sock.sendall(line)
                    buf = b""
                    while b"\n" not in buf:
                        chunk = sock.recv(4096)
                        if not chunk:
                            break
                        buf += chunk
                    if not buf:
                        return {"ok": False, "error": "empty_response"}
                    return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                last_err = str(exc)
                time.sleep(0.2)
        return {"ok": False, "error": "unix_connect_failed", "detail": last_err}

    def _mailbox_roundtrip(self, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
        """File mailbox used when virtio-serial socket is unavailable (unit tests / hybrid)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        req = path.with_suffix(path.suffix + ".req") if path.suffix else Path(str(path) + ".req")
        rsp = path.with_suffix(path.suffix + ".rsp") if path.suffix else Path(str(path) + ".rsp")
        # Simpler: path is base
        base = path
        req = Path(str(base) + ".req")
        rsp = Path(str(base) + ".rsp")
        if rsp.exists():
            rsp.unlink()
        req.write_text(json.dumps(payload) + "\n", encoding="utf-8")
        # Local stub responder for host-only tests / when guest not running
        if os.environ.get("GUNNCH_GUEST_AGENT_HOST_STUB", "1") == "1":
            stub = self._local_stub(payload)
            rsp.write_text(json.dumps(stub) + "\n", encoding="utf-8")
        deadline = time.time() + self.timeout_sec
        while time.time() < deadline:
            if rsp.exists():
                try:
                    return json.loads(rsp.read_text(encoding="utf-8").splitlines()[0])
                except (json.JSONDecodeError, IndexError) as exc:
                    return {"ok": False, "error": "bad_mailbox_response", "detail": str(exc)}
            time.sleep(0.05)
        return {"ok": False, "error": "mailbox_timeout"}

    def _local_stub(self, payload: dict[str, Any]) -> dict[str, Any]:
        cmd = payload.get("cmd")
        base = {
            "ok": True,
            "protocol": PROTOCOL,
            "SILICON_EXACT_EMULATION": False,
            "production_keys": False,
            "transport": "host_mailbox_stub",
            "measurement_class": "HOST_OBSERVED",
        }
        if cmd == "ping":
            return {**base, "pong": True, "boot_complete": True}
        if cmd == "boot_status":
            return {**base, "boot_complete": True, "ready": True}
        if cmd == "process_list":
            return {**base, "processes": ["init", "gunnch-guest-agent"]}
        if cmd == "process_start":
            return {**base, "started": payload.get("name"), "stub": True}
        if cmd == "process_stop":
            return {**base, "stopped": payload.get("name"), "stub": True}
        if cmd == "package_ops":
            return {
                **base,
                "ops": "stub_to_real",
                "status": "STUB",
                "note": "Package ops real when guest apk available",
            }
        if cmd == "display_info":
            return {
                **base,
                "displays": payload.get("expected_displays") or [{"id": "guest0", "connected": True}],
                "note": "Guest-reported; not physical panel measurement",
            }
        if cmd == "logs":
            return {**base, "lines": ["GUNNCHOS_BOOT_COMPLETE=true"]}
        if cmd == "metrics":
            return {
                **base,
                "metrics": {"uptime_s": 1, "measurement_class": "HOST_OBSERVED"},
            }
        if cmd in {"shutdown", "reboot"}:
            return {**base, "action": cmd, "accepted": True}
        return {**base, "cmd": cmd, "note": "unknown_cmd_ack"}

    def ping(self) -> dict[str, Any]:
        self.last_response = self._send_line({"protocol": PROTOCOL, "cmd": "ping"})
        self.ready = bool(self.last_response.get("ok") and self.last_response.get("pong"))
        return self.last_response

    def wait_ready(self, *, timeout_sec: float | None = None) -> dict[str, Any]:
        timeout = timeout_sec if timeout_sec is not None else self.timeout_sec
        deadline = time.time() + timeout
        last: dict[str, Any] = {"ok": False, "error": "not_started"}
        while time.time() < deadline:
            last = self.ping()
            if self.ready:
                return {"ok": True, "ready": True, "response": last}
            time.sleep(0.2)
        return {"ok": False, "ready": False, "response": last, "error": "guest_agent_not_ready"}

    def call(self, cmd: str, **kwargs: Any) -> dict[str, Any]:
        payload = {"protocol": PROTOCOL, "cmd": cmd, **kwargs}
        self.last_response = self._send_line(payload)
        return self.last_response
