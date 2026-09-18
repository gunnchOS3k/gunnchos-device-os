#!/usr/bin/env python3
"""Minimal CDP Runtime.evaluate against Chromium on port 9333."""
from __future__ import annotations

import base64
import json
import os
import socket
import struct
import sys
import time
import urllib.request


def main() -> int:
    expr = sys.argv[1] if len(sys.argv) > 1 else "document.title"
    try:
        tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:9333/json/list", timeout=5).read())
    except Exception as e:
        print(json.dumps({"ok": False, "error": str(e)}))
        return 0
    page = None
    for t in tabs:
        if t.get("type") == "page" and t.get("webSocketDebuggerUrl"):
            page = t
            break
    if not page:
        print(json.dumps({"ok": False, "error": "no_page", "tabs": tabs}))
        return 0
    wsurl = page["webSocketDebuggerUrl"]
    u = wsurl.replace("ws://", "")
    hostport, path = u.split("/", 1)
    host, port_s = hostport.split(":")
    port = int(port_s)
    path = "/" + path
    key = base64.b64encode(os.urandom(16)).decode()
    req = (
        f"GET {path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
        f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    ).encode()
    s = socket.create_connection((host, port), timeout=10)
    s.sendall(req)
    resp = s.recv(4096)
    if b"101" not in resp:
        print(json.dumps({"ok": False, "error": "ws_upgrade", "resp": resp[:200].decode(errors="replace")}))
        return 0

    def send_json(obj):
        data = json.dumps(obj).encode()
        fin_opcode = 0x81
        mask_bit = 0x80
        ln = len(data)
        if ln < 126:
            hdr = bytes([fin_opcode, mask_bit | ln])
        else:
            hdr = bytes([fin_opcode, mask_bit | 126]) + struct.pack("!H", ln)
        mask = os.urandom(4)
        masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        s.sendall(hdr + mask + masked)

    def recv_msg():
        hdr = s.recv(2)
        if len(hdr) < 2:
            return None
        ln = hdr[1] & 0x7F
        if ln == 126:
            ln = struct.unpack("!H", s.recv(2))[0]
        elif ln == 127:
            ln = struct.unpack("!Q", s.recv(8))[0]
        data = b""
        while len(data) < ln:
            chunk = s.recv(ln - len(data))
            if not chunk:
                break
            data += chunk
        return data

    send_json({"id": 1, "method": "Runtime.enable"})
    recv_msg()
    send_json({"id": 2, "method": "Runtime.evaluate", "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}})
    end = time.time() + 20
    result = None
    while time.time() < end:
        raw = recv_msg()
        if not raw:
            break
        try:
            obj = json.loads(raw.decode())
        except Exception:
            continue
        if obj.get("id") == 2:
            result = obj
            break
    print(json.dumps({"ok": True, "ws": wsurl, "title": page.get("title"), "url": page.get("url"), "result": result}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
