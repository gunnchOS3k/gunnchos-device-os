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

# Full command list, including WP-011R Interactive Guest additions
# (framebuffer_capture, compositor_info, app_launch). See
# gunnchos_device_os/device_lab/guest_agent/PROTOCOL.md for the honest
# per-command contract.
SUPPORTED_COMMANDS = (
    "ping",
    "boot_status",
    "process_list",
    "process_start",
    "process_run",
    "process_stop",
    "package_ops",
    "display_info",
    "input_inject",
    "input_observe",
    "logs",
    "metrics",
    "shutdown",
    "reboot",
    "framebuffer_capture",
    "compositor_info",
    "app_launch",
    "file_put",
    "file_get",
)


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
        """QEMU virtio-serial chardev is a host unix socket (server=on).

        Guest agent may emit unsolicited heartbeats; drain until matching cmd/pong.
        Connect retries use a short budget so a dead agent cannot burn a 20min apt timeout.
        """
        deadline = time.time() + self.timeout_sec
        last_err = None
        want_cmd = payload.get("cmd")
        # Ping/boot may wait minutes for agent; long process_run must not spin connect for 20min.
        if want_cmd == "ping":
            connect_deadline = deadline
        else:
            connect_deadline = time.time() + min(25.0, max(5.0, self.timeout_sec))
        while time.time() < deadline:
            if (
                want_cmd != "ping"
                and time.time() > connect_deadline
                and last_err
                and ("Connection refused" in last_err or "connect" in last_err.lower())
            ):
                return {
                    "ok": False,
                    "error": "unix_connect_failed",
                    "detail": last_err,
                    "note": "guest_agent_not_listening",
                }
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                    sock.settimeout(min(5.0, self.timeout_sec))
                    sock.connect(str(path))
                    # Drain any pending guest heartbeats before request.
                    sock.settimeout(0.15)
                    try:
                        while True:
                            peek = sock.recv(4096)
                            if not peek:
                                break
                    except (OSError, TimeoutError):
                        pass
                    # framebuffer_capture / file_get / process_run can take >8s; honor timeout_sec.
                    sock.settimeout(min(30.0, max(0.5, deadline - time.time())))
                    line = (json.dumps(payload, separators=(",", ":")) + "\n").encode("utf-8")
                    sock.sendall(line)
                    buf = b""
                    matched: dict[str, Any] | None = None
                    read_budget = max(1.0, deadline - time.time())
                    # Long guest cmds need the full remaining budget, not a hard 8s cap.
                    if want_cmd in {
                        "framebuffer_capture",
                        "process_run",
                        "package_ops",
                        "app_launch",
                        "file_get",
                        "file_put",
                    }:
                        read_deadline = time.time() + read_budget
                    else:
                        read_deadline = time.time() + min(12.0, read_budget)
                    idle_timeouts = 0
                    while time.time() < read_deadline:
                        try:
                            # Keep socket timeout short so we can poll deadline, but do NOT
                            # abort a partial JSON line on the first idle recv.
                            sock.settimeout(1.0)
                            chunk = sock.recv(65536)
                        except (OSError, TimeoutError):
                            # If we already have an incomplete line, keep waiting for more.
                            if buf and b"\n" not in buf:
                                idle_timeouts += 1
                                if idle_timeouts < 45:
                                    continue
                            break
                        idle_timeouts = 0
                        if not chunk:
                            # Peer closed — only stop if we have nothing useful pending.
                            if not buf:
                                break
                            time.sleep(0.05)
                            continue
                        buf += chunk
                        while b"\n" in buf:
                            raw, buf = buf.split(b"\n", 1)
                            if not raw.strip():
                                continue
                            try:
                                obj = json.loads(raw.decode("utf-8"))
                            except json.JSONDecodeError:
                                continue
                            # Accept pong / matching cmd / boot_complete
                            if want_cmd == "ping" and (obj.get("pong") or obj.get("cmd") == "ping"):
                                matched = obj
                                break
                            if want_cmd and obj.get("cmd") == want_cmd:
                                matched = obj
                                break
                            if want_cmd is None and obj.get("ok") is True:
                                matched = obj
                                break
                            # Keep scanning past unsolicited heartbeats
                        if matched is not None:
                            break
                    if matched is not None:
                        # Label transport honestly for virtio-serial path.
                        if "transport" not in matched:
                            matched["transport"] = "virtio_serial"
                        matched.setdefault("agent_path_label", "virtio-serial")
                        return matched
                    last_err = "empty_or_unmatched_response"
            except (OSError, json.JSONDecodeError) as exc:
                last_err = str(exc)
                time.sleep(0.2)
        return {"ok": False, "error": "unix_connect_failed", "detail": last_err}

    def _mailbox_roundtrip(self, path: Path, payload: dict[str, Any]) -> dict[str, Any]:
        """File mailbox used when virtio-serial socket is unavailable (unit tests / hybrid)."""
        path.parent.mkdir(parents=True, exist_ok=True)
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
            "agent_path_label": "host_mailbox_stub",
            "measurement_class": "HOST_OBSERVED",
        }
        if cmd == "ping":
            return {**base, "pong": True, "boot_complete": True}
        if cmd == "boot_status":
            return {**base, "boot_complete": True, "ready": True}
        if cmd == "process_list":
            return {**base, "processes": ["init", "gunnch-guest-agent"]}
        if cmd == "process_start":
            return {
                **base,
                "started": payload.get("name"),
                "stub": True,
                "note": "Host mailbox stub — not a real guest process",
            }
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
                "displays": payload.get("expected_displays")
                or [
                    {"id": "guest0", "connected": True},
                    {"id": "guest1", "connected": True},
                ],
                "stub": True,
                "note": "Mailbox stub displays — not guest-proven dual",
            }
        if cmd in {"input_inject", "input_observe"}:
            return {
                **base,
                "observed": True,
                "stub": True,
                "kind": payload.get("kind"),
                "note": "Mailbox stub input observe — prefer QEMU monitor/virtio path",
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
        if cmd == "framebuffer_capture":
            # Interactive Guest command. Mailbox stub has no real guest
            # compositor to capture from — never fabricate a framebuffer.
            return {
                **base,
                "ok": False,
                "stub": True,
                "reason": "host_mailbox_stub_no_real_framebuffer",
                "note": (
                    "framebuffer_capture requires a live Interactive Guest "
                    "(DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST) over virtio-serial; "
                    "mailbox stub cannot produce real pixels."
                ),
            }
        if cmd == "compositor_info":
            # Interactive Guest command. Honest: no compositor process exists
            # in the mailbox stub, so report unavailable rather than inventing one.
            return {
                **base,
                "ok": True,
                "stub": True,
                "compositor": None,
                "available": False,
                "outputs": 0,
                "surfaces": 0,
                "note": "No compositor running in host mailbox stub",
            }
        if cmd == "app_launch":
            # Interactive Guest command. Never claim a fabricated PID.
            return {
                **base,
                "ok": False,
                "stub": True,
                "started": False,
                "app": payload.get("app"),
                "note": (
                    "app_launch requires an Interactive Guest with a real compositor "
                    "and installed apps; not available via mailbox stub"
                ),
            }
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
