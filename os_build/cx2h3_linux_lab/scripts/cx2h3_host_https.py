#!/usr/bin/env python3
"""Deterministic HTTPS source for CX2H.3 J2 — real TLS, request logging, download."""

from __future__ import annotations

import hashlib
import json
import os
import ssl
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HOST = os.environ.get("CX2H3_HTTPS_BIND", "0.0.0.0")
PORT = int(os.environ.get("CX2H3_HTTPS_PORT", "18443"))
ROOT = Path(os.environ.get("CX2H3_HTTPS_ROOT", "/tmp/cx2h3-https"))
DOC_NAME = "cx2h3_j2_source.odt"
TITLE = "CX2H3 Deterministic HTTPS Document Source"
MARKER = "CX2H3-J2-HTTPS-SOURCE-alpha-7gc"

STATE = {"requests": [], "downloads": 0, "started_at": None}


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def ensure_doc() -> Path:
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / DOC_NAME
    # Keep stable bytes across restarts when marker unchanged
    if path.is_file() and (ROOT / "manifest.json").is_file():
        try:
            man = json.loads((ROOT / "manifest.json").read_text())
            if man.get("marker") == MARKER and man.get("sha256") == _sha256(path.read_bytes()):
                return path
        except Exception:
            pass
    # Minimal ODT (zip) with deterministic content marker in content.xml
    import io
    import zipfile

    content_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0" office:version="1.2">
 <office:body><office:text>
  <text:p>{MARKER}</text:p>
 </office:text></office:body>
</office:document-content>
"""
    meta = b'<?xml version="1.0"?><office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"/>'
    mime = b"application/vnd.oasis.opendocument.text"
    manifest = b"""<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0">
 <manifest:file-entry manifest:full-path="/" manifest:media-type="application/vnd.oasis.opendocument.text"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
</manifest:manifest>
"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", mime, compress_type=zipfile.ZIP_STORED)
        zf.writestr("content.xml", content_xml.encode())
        zf.writestr("meta.xml", meta)
        zf.writestr("META-INF/manifest.xml", manifest)
    data = buf.getvalue()
    path = ROOT / DOC_NAME
    path.write_bytes(data)
    (ROOT / "manifest.json").write_text(
        json.dumps(
            {
                "title": TITLE,
                "document": DOC_NAME,
                "sha256": _sha256(data),
                "marker": MARKER,
                "size": len(data),
            },
            indent=2,
        )
        + "\n"
    )
    return path


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # noqa: N802
        STATE["requests"].append(
            {
                "ts": time.time(),
                "client": self.client_address[0],
                "line": fmt % args,
                "path": getattr(self, "path", ""),
            }
        )

    def _html(self) -> bytes:
        man = json.loads((ROOT / "manifest.json").read_text())
        body = f"""<!DOCTYPE html>
<html><head><title>{TITLE}</title>
<meta name="cx2h3-sha256" content="{man['sha256']}">
<meta name="cx2h3-marker" content="{MARKER}">
</head><body>
<h1 id="title">{TITLE}</h1>
<p id="marker">{MARKER}</p>
<p>SHA256: <code id="sha256">{man['sha256']}</code></p>
<p><a id="download" href="/download/{DOC_NAME}" download="{DOC_NAME}">Download deterministic document</a></p>
</body></html>"""
        return body.encode()

    def do_GET(self):  # noqa: N802
        if self.path in ("/", "/index.html"):
            data = self._html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path.startswith("/download/"):
            path = ROOT / DOC_NAME
            data = path.read_bytes()
            STATE["downloads"] += 1
            self.send_response(200)
            self.send_header("Content-Type", "application/vnd.oasis.opendocument.text")
            self.send_header("Content-Disposition", f'attachment; filename="{DOC_NAME}"')
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-CX2H3-SHA256", _sha256(data))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/manifest.json":
            data = (ROOT / "manifest.json").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        if self.path == "/api/stats":
            data = json.dumps(
                {
                    "downloads": STATE["downloads"],
                    "requests": len(STATE["requests"]),
                    "recent": STATE["requests"][-20:],
                }
            ).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_error(404)


def main() -> None:
    ensure_doc()
    cert = Path(os.environ["CX2H3_HTTPS_CERT"])
    key = Path(os.environ["CX2H3_HTTPS_KEY"])
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(str(cert), str(key))
    httpd = ThreadingHTTPServer((HOST, PORT), Handler)
    httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
    STATE["started_at"] = time.time()
    (ROOT / "server.pid").write_text(str(os.getpid()))
    (ROOT / "server.json").write_text(
        json.dumps({"host": HOST, "port": PORT, "pid": os.getpid(), "url": f"https://cx2h3.test:{PORT}/"}, indent=2)
    )
    print(f"CX2H3 HTTPS listening on {HOST}:{PORT}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
