
from __future__ import annotations

import json
import shutil
import socket
import threading
import uuid
from dataclasses import dataclass, field
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class _Router(BaseHTTPRequestHandler):
    stack: "LocalServiceStack"

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        return

    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            return {}

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        st = self.stack
        if path in ("/health", "/"):
            return self._json(200, {"ok": True, "services": sorted(st.endpoints.keys())})
        if path.startswith("/lms"):
            return self._json(200, {"ok": True, "service": "lms_dev", "assignment": "assignment.pdf"})
        if path.startswith("/caldav") or path.startswith("/carddav"):
            return self._json(200, {"ok": True, "service": "caldav", "events": st.calendar, "contacts": st.contacts})
        if path.startswith("/webdav"):
            files = sorted(p.name for p in st.webdav_root.glob("**/*") if p.is_file())
            return self._json(200, {"ok": True, "service": "webdav", "files": files})
        if path.startswith("/matrix"):
            return self._json(200, {"ok": True, "service": "matrix_dev", "rooms": st.matrix_rooms, "messages": st.matrix_messages[-20:]})
        if path.startswith("/webrtc"):
            return self._json(200, {"ok": True, "service": "webrtc_test", "sessions": st.webrtc_sessions})
        if path.startswith("/imap"):
            return self._json(200, {"ok": True, "service": "imap_dev", "mailbox": st.mailbox})
        if path.startswith("/ring"):
            return self._json(200, {"ok": True, "service": "ring_sim", "packets": st.ring_packets[-10:]})
        if path.startswith("/mdm"):
            return self._json(200, {"ok": True, "service": "mdm_dev", "policies": st.mdm_policies})
        self._json(404, {"ok": False, "error": "not_found", "path": path})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        data = self._read_json()
        st = self.stack
        if path == "/smtp/send":
            msg = {
                "id": str(uuid.uuid4()),
                "from": data.get("from", "dev@localhost"),
                "to": data.get("to", "peer@localhost"),
                "subject": data.get("subject", ""),
                "body": data.get("body", ""),
            }
            st.mailbox.append(msg)
            return self._json(200, {"ok": True, "queued": msg})
        if path == "/lms/submit":
            receipt = {"id": str(uuid.uuid4()), "status": "submitted", "bytes": data.get("bytes", 0)}
            st.lms_receipts.append(receipt)
            return self._json(200, {"ok": True, "receipt": receipt})
        if path == "/webdav/put":
            name = data.get("name", "file.txt")
            content = data.get("content", "")
            version = int(data.get("version", 1))
            target = st.webdav_root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            # versioning
            if target.exists():
                hist = st.webdav_root / ".versions" / name
                hist.mkdir(parents=True, exist_ok=True)
                prev = hist / f"v{version-1}"
                prev.write_text(target.read_text(encoding="utf-8"), encoding="utf-8")
            target.write_text(str(content), encoding="utf-8")
            st.share_links[name] = f"webdav://local/{name}?v={version}"
            return self._json(200, {"ok": True, "path": name, "version": version, "share": st.share_links[name]})
        if path == "/webdav/share":
            name = data.get("name", "")
            link = st.share_links.get(name) or f"webdav://local/{name}"
            st.share_links[name] = link
            return self._json(200, {"ok": True, "share": link})
        if path == "/matrix/send":
            msg = {"id": str(uuid.uuid4()), "room": data.get("room", "!general"), "body": data.get("body", ""), "from": data.get("from", "user")}
            st.matrix_messages.append(msg)
            return self._json(200, {"ok": True, "message": msg})
        if path == "/webrtc/session":
            sid = str(uuid.uuid4())
            sess = {"id": sid, "state": "connected", "screen_share": bool(data.get("screen_share", False))}
            st.webrtc_sessions[sid] = sess
            return self._json(200, {"ok": True, "session": sess})
        if path == "/ring/packet":
            pkt = {"id": str(uuid.uuid4()), "gesture": data.get("gesture", "tap"), "ts": data.get("ts", 0)}
            st.ring_packets.append(pkt)
            return self._json(200, {"ok": True, "packet": pkt})
        if path == "/caldav/event":
            ev = {"id": str(uuid.uuid4()), **data}
            st.calendar.append(ev)
            return self._json(200, {"ok": True, "event": ev})
        if path == "/mdm/push":
            pol = {"id": str(uuid.uuid4()), **data}
            st.mdm_policies.append(pol)
            return self._json(200, {"ok": True, "policy": pol})
        if path == "/sync/queue":
            item = {"id": str(uuid.uuid4()), **data, "state": "queued"}
            st.sync_queue.append(item)
            return self._json(200, {"ok": True, "item": item})
        if path == "/sync/flush":
            for item in st.sync_queue:
                item["state"] = "flushed"
            return self._json(200, {"ok": True, "flushed": len(st.sync_queue)})
        self._json(404, {"ok": False, "error": "not_found"})

    def do_PROPFIND(self) -> None:  # noqa: N802
        self.do_GET()


@dataclass
class LocalServiceStack:
    """In-process protocol-compatible services for journey E2E."""

    root: Path
    work_dir: Path | None = None
    endpoints: dict[str, str] = field(default_factory=dict)
    mailbox: list[dict[str, Any]] = field(default_factory=list)
    calendar: list[dict[str, Any]] = field(default_factory=list)
    contacts: list[dict[str, Any]] = field(default_factory=list)
    matrix_rooms: list[str] = field(default_factory=lambda: ["!general", "!class"])
    matrix_messages: list[dict[str, Any]] = field(default_factory=list)
    webrtc_sessions: dict[str, Any] = field(default_factory=dict)
    ring_packets: list[dict[str, Any]] = field(default_factory=list)
    mdm_policies: list[dict[str, Any]] = field(default_factory=list)
    lms_receipts: list[dict[str, Any]] = field(default_factory=list)
    share_links: dict[str, str] = field(default_factory=dict)
    sync_queue: list[dict[str, Any]] = field(default_factory=list)
    webdav_root: Path = field(init=False)
    _httpd: ThreadingHTTPServer | None = field(default=None, init=False, repr=False)
    _thread: threading.Thread | None = field(default=None, init=False, repr=False)
    base_url: str = ""

    def __post_init__(self) -> None:
        base = self.work_dir or (self.root / "user_journeys" / "services" / "runtime")
        base.mkdir(parents=True, exist_ok=True)
        self.webdav_root = base / "webdav"
        self.webdav_root.mkdir(parents=True, exist_ok=True)
        # seed fixtures
        fixtures = self.root / "user_journeys" / "fixtures"
        if fixtures.exists():
            for src in fixtures.iterdir():
                if src.is_file() and src.name != "README.md":
                    dest = self.webdav_root / src.name
                    if not dest.exists():
                        shutil.copy2(src, dest)

    def start(self) -> dict[str, Any]:
        if self._httpd is not None:
            return {"ok": True, "base_url": self.base_url, "endpoints": self.endpoints}
        port = _free_port()
        handler = type("BoundRouter", (_Router,), {"stack": self})
        self._httpd = ThreadingHTTPServer(("127.0.0.1", port), handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        self.base_url = f"http://127.0.0.1:{port}"
        self.endpoints = {
            "health": f"{self.base_url}/health",
            "lms": f"{self.base_url}/lms",
            "imap": f"{self.base_url}/imap",
            "smtp": f"{self.base_url}/smtp/send",
            "caldav": f"{self.base_url}/caldav",
            "webdav": f"{self.base_url}/webdav",
            "matrix": f"{self.base_url}/matrix",
            "webrtc": f"{self.base_url}/webrtc",
            "ring": f"{self.base_url}/ring",
            "mdm": f"{self.base_url}/mdm",
            "sync": f"{self.base_url}/sync/queue",
        }
        # Write discovery without host home paths
        discovery = {
            "schema": "gunnchos.phase_xi_local_services.v1",
            "base_url": self.base_url,
            "endpoints": self.endpoints,
            "commercial_cloud_creds_required": False,
            "bind": "127.0.0.1",
        }
        out = self.root / "user_journeys" / "services" / "DISCOVERY.json"
        out.write_text(json.dumps(discovery, indent=2) + "\n", encoding="utf-8")
        return {"ok": True, "base_url": self.base_url, "endpoints": self.endpoints}

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None

    def request(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        import urllib.request

        url = path if path.startswith("http") else f"{self.base_url}{path}"
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method=method)
        if data is not None:
            req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
