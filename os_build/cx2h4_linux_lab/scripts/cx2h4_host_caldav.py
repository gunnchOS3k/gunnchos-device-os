#!/usr/bin/env python3
"""Minimal real CalDAV/CardDAV + browser GUI surface for CX2H.4 (no radicale dependency).

Stores ICS/VCF on disk. Serves a simple HTML GUI so Chromium can create calendar
events and contacts through a real browser window; persistence is verified via
CalDAV/CardDAV HTTP GET (authoritative server state).
"""

from __future__ import annotations

import json
import os
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(os.environ.get("CX2H4_CALDAV_ROOT", "/tmp/cx2h4-caldav"))
BIND = os.environ.get("CX2H4_CALDAV_BIND", "0.0.0.0")
PORT = int(os.environ.get("CX2H4_CALDAV_PORT", "18580"))
PIDFILE = ROOT / "server.pid"

CAL_DIR = ROOT / "caldav" / "user" / "calendar"
CARD_DIR = ROOT / "carddav" / "user" / "contacts"

HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/><title>CX2H4 Connect Calendar</title>
<style>
body{font-family:system-ui,sans-serif;margin:2rem;background:#f7f5f0;color:#1a1a1a}
h1{font-size:1.4rem} section{margin:1.5rem 0;padding:1rem;border:1px solid #ccc;background:#fff}
label{display:block;margin:.4rem 0} input,button{font-size:1rem;padding:.4rem}
#status{margin-top:1rem;font-weight:600}
</style></head><body>
<h1>CX2H4 Connect — Calendar &amp; Contacts</h1>
<p>Real CalDAV/CardDAV lab provider GUI. Persistence is server-side.</p>
<section id="calendar">
  <h2>Calendar</h2>
  <label>Summary <input id="summary" value="CX2H4-P0-CAL-EVENT"/></label>
  <label>UID <input id="uid" value="cx2h4-evt-1"/></label>
  <button id="create-event" type="button">Create calendar event</button>
</section>
<section id="contacts">
  <h2>Contacts</h2>
  <label>Full name <input id="fn" value="CX2H4 Peer"/></label>
  <label>Email <input id="email" value="peer@cx2h4.test"/></label>
  <label>UID <input id="cuid" value="cx2h4-c1"/></label>
  <button id="create-contact" type="button">Create contact</button>
</section>
<div id="status">ready</div>
<script>
async function put(path, body, ctype) {
  const r = await fetch(path, {method:'PUT', headers:{'Content-Type': ctype}, body});
  return {ok: r.ok || r.status===201 || r.status===204, status: r.status, text: await r.text()};
}
document.getElementById('create-event').onclick = async () => {
  const uid = document.getElementById('uid').value.trim();
  const summary = document.getElementById('summary').value.trim();
  const ics = [
    'BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//gunnchOS//CX2H4//EN','BEGIN:VEVENT',
    'UID:'+uid,'SUMMARY:'+summary,'DTSTART:20260917T150000Z','DTEND:20260917T160000Z',
    'END:VEVENT','END:VCALENDAR',''
  ].join('\\r\\n');
  const res = await put('/caldav/user/calendar/'+encodeURIComponent(uid)+'.ics', ics, 'text/calendar');
  document.getElementById('status').textContent = 'event:'+JSON.stringify(res);
  window.__CX2H4_EVENT__ = res;
};
document.getElementById('create-contact').onclick = async () => {
  const uid = document.getElementById('cuid').value.trim();
  const fn = document.getElementById('fn').value.trim();
  const email = document.getElementById('email').value.trim();
  const vcf = [
    'BEGIN:VCARD','VERSION:3.0','FN:'+fn,'EMAIL:'+email,'UID:'+uid,'END:VCARD',''
  ].join('\\r\\n');
  const res = await put('/carddav/user/contacts/'+encodeURIComponent(uid)+'.vcf', vcf, 'text/vcard');
  document.getElementById('status').textContent = 'contact:'+JSON.stringify(res);
  window.__CX2H4_CONTACT__ = res;
};
</script>
</body></html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # quiet
        pass

    def _send(self, code: int, body: bytes, ctype: str = "text/plain"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, PUT, PROPFIND, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Depth")
        self.end_headers()

    def do_GET(self):
        path = unquote(urlparse(self.path).path)
        if path in ("/", "/index.html"):
            self._send(200, HTML.encode(), "text/html; charset=utf-8")
            return
        if path == "/api/health":
            self._send(200, json.dumps({"ok": True, "service": "cx2h4-caldav"}).encode(), "application/json")
            return
        if path == "/api/list":
            events = sorted(p.name for p in CAL_DIR.glob("*.ics")) if CAL_DIR.is_dir() else []
            contacts = sorted(p.name for p in CARD_DIR.glob("*.vcf")) if CARD_DIR.is_dir() else []
            self._send(200, json.dumps({"events": events, "contacts": contacts}).encode(), "application/json")
            return
        file_path = ROOT / path.lstrip("/")
        if file_path.is_file() and str(file_path.resolve()).startswith(str(ROOT.resolve())):
            ctype = "text/calendar" if file_path.suffix == ".ics" else "text/vcard" if file_path.suffix == ".vcf" else "application/octet-stream"
            self._send(200, file_path.read_bytes(), ctype)
            return
        self._send(404, b"not found")

    def do_PUT(self):
        path = unquote(urlparse(self.path).path)
        length = int(self.headers.get("Content-Length") or 0)
        body = self.rfile.read(length) if length else b""
        if path.startswith("/caldav/"):
            target = ROOT / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            self._send(201, json.dumps({"ok": True, "path": path, "bytes": len(body)}).encode(), "application/json")
            return
        if path.startswith("/carddav/"):
            target = ROOT / path.lstrip("/")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
            self._send(201, json.dumps({"ok": True, "path": path, "bytes": len(body)}).encode(), "application/json")
            return
        self._send(404, b"not found")

    def do_PROPFIND(self):
        # Minimal WebDAV discovery response for honest protocol surface
        path = unquote(urlparse(self.path).path)
        xml = f"""<?xml version="1.0"?><d:multistatus xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav" xmlns:card="urn:ietf:params:xml:ns:carddav">
<d:response><d:href>{path}</d:href><d:propstat><d:prop><d:resourcetype><d:collection/></d:resourcetype></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>
</d:multistatus>"""
        self._send(207, xml.encode(), "application/xml")


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    CAL_DIR.mkdir(parents=True, exist_ok=True)
    CARD_DIR.mkdir(parents=True, exist_ok=True)
    PIDFILE.write_text(str(os.getpid()))
    httpd = ThreadingHTTPServer((BIND, PORT), Handler)
    print(json.dumps({"ok": True, "bind": BIND, "port": PORT, "root": str(ROOT)}), flush=True)
    try:
        httpd.serve_forever()
    finally:
        try:
            PIDFILE.unlink(missing_ok=True)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
