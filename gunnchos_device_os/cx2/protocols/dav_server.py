"""Minimal real CalDAV/CardDAV HTTP server (not JSON fixtures)."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse
import uuid


@dataclass
class LocalDavStack:
    root: Path
    host: str = "127.0.0.1"
    port: int = 0
    events: Dict[str, dict] = field(default_factory=dict)
    contacts: Dict[str, dict] = field(default_factory=dict)
    _httpd: Optional[HTTPServer] = None
    _thread: Optional[threading.Thread] = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def start(self) -> dict:
        stack = self

        class Handler(BaseHTTPRequestHandler):
            def _read(self) -> bytes:
                n = int(self.headers.get("Content-Length", 0))
                return self.rfile.read(n) if n else b""

            def _json(self, code: int, payload: dict) -> None:
                raw = json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def do_PUT(self):  # noqa: N802
                path = urlparse(self.path).path
                body = self._read()
                if path.startswith("/caldav/"):
                    uid = path.rsplit("/", 1)[-1] or str(uuid.uuid4())
                    text = body.decode(errors="ignore")
                    stack.events[uid] = {"uid": uid, "ics": text}
                    (stack.root / f"{uid}.ics").write_text(text)
                    self._json(201, {"uid": uid, "ok": True})
                elif path.startswith("/carddav/"):
                    uid = path.rsplit("/", 1)[-1] or str(uuid.uuid4())
                    text = body.decode(errors="ignore")
                    stack.contacts[uid] = {"uid": uid, "vcf": text}
                    (stack.root / f"{uid}.vcf").write_text(text)
                    self._json(201, {"uid": uid, "ok": True})
                else:
                    self._json(404, {"ok": False})

            def do_GET(self):  # noqa: N802
                path = urlparse(self.path).path
                if path == "/caldav/":
                    self._json(200, {"events": list(stack.events.values())})
                elif path == "/carddav/":
                    self._json(200, {"contacts": list(stack.contacts.values())})
                elif path.startswith("/caldav/"):
                    uid = path.rsplit("/", 1)[-1]
                    ev = stack.events.get(uid)
                    if not ev:
                        self._json(404, {"ok": False})
                    else:
                        raw = ev["ics"].encode()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/calendar")
                        self.send_header("Content-Length", str(len(raw)))
                        self.end_headers()
                        self.wfile.write(raw)
                elif path.startswith("/carddav/"):
                    uid = path.rsplit("/", 1)[-1]
                    c = stack.contacts.get(uid)
                    if not c:
                        self._json(404, {"ok": False})
                    else:
                        raw = c["vcf"].encode()
                        self.send_response(200)
                        self.send_header("Content-Type", "text/vcard")
                        self.send_header("Content-Length", str(len(raw)))
                        self.end_headers()
                        self.wfile.write(raw)
                else:
                    self._json(404, {"ok": False})

            def do_DELETE(self):  # noqa: N802
                path = urlparse(self.path).path
                uid = path.rsplit("/", 1)[-1]
                if path.startswith("/caldav/") and uid in stack.events:
                    del stack.events[uid]
                    p = stack.root / f"{uid}.ics"
                    if p.exists():
                        p.unlink()
                    self._json(200, {"ok": True})
                elif path.startswith("/carddav/") and uid in stack.contacts:
                    del stack.contacts[uid]
                    p = stack.root / f"{uid}.vcf"
                    if p.exists():
                        p.unlink()
                    self._json(200, {"ok": True})
                else:
                    self._json(404, {"ok": False})

            def log_message(self, format, *args):  # noqa: A003
                return

        self._httpd = HTTPServer((self.host, 0), Handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return {
            "base": f"http://{self.host}:{self.port}",
            "caldav": f"http://{self.host}:{self.port}/caldav/",
            "carddav": f"http://{self.host}:{self.port}/carddav/",
            "protocol": "http_dav_subset",
        }

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
