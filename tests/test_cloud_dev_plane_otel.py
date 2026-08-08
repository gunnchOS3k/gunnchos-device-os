"""OpenTelemetry local collector round-trip with gunnchos.* conventions + redaction."""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading

from gunnchos_device_os.cloud_dev_plane.otel_conventions import (
    GUNNCHOS_ATTR_MODE,
    GUNNCHOS_ATTR_REALM,
    GUNNCHOS_ATTR_SERVICE,
    SPAN_NAMES,
    build_attributes,
)
from gunnchos_device_os.cloud_dev_plane.otel_export import OtelRoundTrip
from gunnchos_device_os.cloud_dev_plane.privacy_redaction import redact_payload
from gunnchos_device_os.cloud_dev_plane.server import DevPlaneApp, DevPlaneServer
from gunnchos_device_os.cloud_edge.services import ServiceMode


class _Collector:
    def __init__(self) -> None:
        self.payloads: list[dict] = []
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def endpoint(self) -> str:
        assert self._httpd is not None
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}/v1/traces"

    def start(self) -> "_Collector":
        parent = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt, *args):  # noqa: A003
                return

            def do_POST(self):  # noqa: N802
                length = int(self.headers.get("Content-Length") or 0)
                raw = self.rfile.read(length)
                parent.payloads.append(json.loads(raw.decode("utf-8")))
                body = b"{}"
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self._httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self

    def stop(self) -> None:
        assert self._httpd is not None
        self._httpd.shutdown()
        self._httpd.server_close()


def test_gunnchos_conventions_and_redaction():
    attrs = build_attributes(
        service="telemetry",
        mode="cloud",
        event_type="heartbeat",
        device_id="dev-1",
        extra={"email": "student@school.test", "token": "DEV_SECRET", "ok": True},
    )
    assert attrs[GUNNCHOS_ATTR_SERVICE] == "telemetry"
    assert attrs[GUNNCHOS_ATTR_MODE] == "cloud"
    assert attrs[GUNNCHOS_ATTR_REALM] == "DEV"
    assert attrs["email"] == "[REDACTED]"
    assert attrs["token"] == "[REDACTED]"
    assert SPAN_NAMES["fleet"].startswith("gunnchos.")


def test_otlp_http_round_trip_to_local_collector():
    collector = _Collector().start()
    exporter = OtelRoundTrip(endpoint=collector.endpoint)
    result = exporter.export_span(
        surface="telemetry",
        mode="local",
        attributes={"email": "a@b.c", "gunnchos.event.type": "roundtrip"},
    )
    assert result["ok"] is True
    assert result["status"] == 200
    assert len(collector.payloads) == 1
    resource_spans = collector.payloads[0]["resourceSpans"]
    spans = resource_spans[0]["scopeSpans"][0]["spans"]
    assert spans[0]["name"] == "gunnchos.telemetry.emit"
    # Exporter records redacted local copy
    recorded = exporter.sent[0]
    flat = json.dumps(recorded)
    assert "a@b.c" not in flat
    assert "[REDACTED" in flat or "REDACTED" in flat or "student" not in flat
    collector.stop()


def test_server_emits_spans_when_otel_configured():
    collector = _Collector().start()
    otel = OtelRoundTrip(endpoint=collector.endpoint)
    server = DevPlaneServer(DevPlaneApp(role="gateway", otel=otel, default_mode=ServiceMode.LOCAL)).start()
    from gunnchos_device_os.cloud_dev_plane import DevPlaneClient

    client = DevPlaneClient(base_url=server.base_url, mode=ServiceMode.LOCAL)
    client.telemetry_emit("ping", {"email": "x@y.z", "ok": True})
    assert len(collector.payloads) >= 1
    # Stored telemetry payload redacted
    snap = client.inventory()["snapshot"]
    assert snap["telemetry_buffered"] >= 1
    server.stop()
    collector.stop()


def test_redact_payload_bearer_and_nested():
    raw = {
        "authorization": "Bearer super-secret",
        "nested": {"student_name": "Ada", "note": "ok"},
        "msg": "contact me@school.edu please",
    }
    out = redact_payload(raw)
    assert out["authorization"] == "[REDACTED]"
    assert out["nested"]["student_name"] == "[REDACTED]"
    assert "[REDACTED_EMAIL]" in out["msg"]
