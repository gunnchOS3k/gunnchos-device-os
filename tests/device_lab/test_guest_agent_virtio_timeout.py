"""Regression: virtio-serial host I/O must return within a bounded timeout."""
from __future__ import annotations

import json
import os
import socket
import tempfile
import threading
import time
from pathlib import Path

from gunnchos_device_os.device_lab.guest_agent.client import GuestAgentClient


def _short_sock(name: str) -> Path:
    # macOS AF_UNIX sun_path is short; prefer /tmp over deep pytest tmp paths.
    return Path(tempfile.gettempdir()) / f"gdl-ga-{os.getpid()}-{name}.sock"


def test_unix_roundtrip_returns_when_peer_does_not_reply():
    """Stalled peer must not hang the host past timeout_sec (prior Ring killer)."""
    sock_path = _short_sock("stall")
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.listen(1)
    server.settimeout(0.5)

    def _accept_and_stall() -> None:
        try:
            conn, _ = server.accept()
            # Accept then never reply; hold connection open.
            time.sleep(12)
            try:
                conn.close()
            except OSError:
                pass
        except OSError:
            pass

    t = threading.Thread(target=_accept_and_stall, daemon=True)
    t.start()
    client = GuestAgentClient(sock_path, timeout_sec=3.0)
    started = time.time()
    try:
        rsp = client.call("ping")
        elapsed = time.time() - started
    finally:
        server.close()
        sock_path.unlink(missing_ok=True)
    assert elapsed < 10.0, f"hung too long: {elapsed}s rsp={rsp}"
    assert rsp.get("ok") is False
    assert rsp.get("pong") is not True


def test_unix_roundtrip_happy_path():
    sock_path = _short_sock("ok")
    if sock_path.exists():
        sock_path.unlink()
    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(str(sock_path))
    server.listen(1)

    def _serve() -> None:
        conn, _ = server.accept()
        buf = b""
        while b"\n" not in buf:
            chunk = conn.recv(4096)
            if not chunk:
                break
            buf += chunk
        req = json.loads(buf.split(b"\n", 1)[0].decode())
        assert req.get("cmd") == "ping"
        rsp = {
            "ok": True,
            "pong": True,
            "cmd": "ping",
            "protocol": "gunnchos.guest_agent.v1",
        }
        conn.sendall((json.dumps(rsp) + "\n").encode())
        conn.close()

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    client = GuestAgentClient(sock_path, timeout_sec=5.0)
    try:
        rsp = client.call("ping")
    finally:
        server.close()
        sock_path.unlink(missing_ok=True)
    assert rsp.get("pong") is True
    assert rsp.get("transport") == "virtio_serial"
