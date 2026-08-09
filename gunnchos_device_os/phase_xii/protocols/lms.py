"""Local LMS HTML service for real browser workflows (not JSON-only fake)."""
from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from gunnchos_device_os.phase_xii.protocols.ports import free_port

LMS_HTML = """<!doctype html>
<html><head><meta charset=utf-8><title>gunnchOS LMS Dev</title></head>
<body>
<h1>Campus LMS (dev)</h1>
<p id=assignment>Assignment: Photosynthesis Lab</p>
<a id=download href="/assignment.pdf" download>Download assignment.pdf</a>
<form id=uploadForm>
  <input type=file id=file name=file />
  <button type=submit>Submit</button>
</form>
<pre id=receipt></pre>
<script>
document.getElementById('uploadForm').onsubmit = async (e) => {
  e.preventDefault();
  const f = document.getElementById('file').files[0];
  const body = new FormData();
  if (f) body.append('file', f);
  const r = await fetch('/submit', {method:'POST', body});
  const j = await r.json();
  document.getElementById('receipt').textContent = JSON.stringify(j, null, 2);
  window.__lms_receipt = j;
};
</script>
</body></html>
"""


class LMSStack:
    def __init__(self, fixture_pdf: Path, work: Path) -> None:
        self.fixture_pdf = fixture_pdf
        self.work = work
        self.work.mkdir(parents=True, exist_ok=True)
        self.port = free_port()
        self.receipts: list[dict[str, Any]] = []
        self._httpd = None
        self._thread = None

    def start(self) -> dict[str, Any]:
        outer = self
        pdf_bytes = self.fixture_pdf.read_bytes() if self.fixture_pdf.exists() else b"%PDF-1.4\\n%EOF\\n"

        class H(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

            def do_GET(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path in ("/", "/lms"):
                    body = LMS_HTML.encode()
                    ctype = "text/html"
                elif path == "/assignment.pdf":
                    body = pdf_bytes
                    ctype = "application/pdf"
                else:
                    self.send_response(404)
                    self.end_headers()
                    return
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_POST(self) -> None:  # noqa: N802
                n = int(self.headers.get("Content-Length", "0") or 0)
                raw = self.rfile.read(n) if n else b""
                receipt = {"id": str(uuid.uuid4()), "status": "submitted", "bytes": len(raw)}
                outer.receipts.append(receipt)
                (outer.work / "last_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
                body = json.dumps({"ok": True, "receipt": receipt}).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), H)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True, name="phase-xii-lms")
        self._thread.start()
        time.sleep(0.05)
        return {"ok": True, "url": f"http://127.0.0.1:{self.port}/", "execution_depth": "L3_REAL_SERVICE_API"}

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()
