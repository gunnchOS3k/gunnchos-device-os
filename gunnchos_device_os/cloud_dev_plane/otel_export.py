"""Minimal OTLP/HTTP JSON exporter + local collector sink (stdlib only)."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from gunnchos_device_os.cloud_dev_plane.otel_conventions import SPAN_NAMES, build_attributes
from gunnchos_device_os.cloud_dev_plane.privacy_redaction import redact_payload


def _ns_now() -> int:
    return time.time_ns()


@dataclass
class OtelRoundTrip:
    """Builds OTLP JSON spans and POSTs them to a local collector endpoint."""

    endpoint: str = "http://127.0.0.1:4318/v1/traces"
    service_name: str = "gunnchos-cloud-dev-plane"
    sent: list[dict[str, Any]] = field(default_factory=list)
    last_status: int | None = None
    last_error: str | None = None

    def build_span(
        self,
        *,
        surface: str,
        mode: str,
        attributes: dict[str, Any] | None = None,
        status_ok: bool = True,
    ) -> dict[str, Any]:
        name = SPAN_NAMES.get(surface, f"gunnchos.{surface}")
        attrs = build_attributes(service=surface, mode=mode, extra=attributes or {})
        start = _ns_now()
        end = start + 1_000_000
        otel_attrs = [{"key": k, "value": _otel_value(v)} for k, v in attrs.items()]
        return {
            "traceId": uuid4().hex + uuid4().hex[:16],
            "spanId": uuid4().hex[:16],
            "name": name,
            "kind": 1,
            "startTimeUnixNano": str(start),
            "endTimeUnixNano": str(end),
            "attributes": otel_attrs,
            "status": {"code": 1 if status_ok else 2},
        }

    def build_payload(self, spans: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "resourceSpans": [
                {
                    "resource": {
                        "attributes": [
                            {"key": "service.name", "value": {"stringValue": self.service_name}},
                            {"key": "gunnchos.realm", "value": {"stringValue": "DEV"}},
                        ]
                    },
                    "scopeSpans": [
                        {
                            "scope": {"name": "gunnchos.cloud_dev_plane", "version": "0.1.0-dev"},
                            "spans": spans,
                        }
                    ],
                }
            ]
        }

    def export_span(
        self,
        *,
        surface: str,
        mode: str,
        attributes: dict[str, Any] | None = None,
        status_ok: bool = True,
    ) -> dict[str, Any]:
        span = self.build_span(
            surface=surface, mode=mode, attributes=attributes, status_ok=status_ok
        )
        payload = self.build_payload([span])
        # Always keep a redacted local copy for tests / offline collector.
        recorded = redact_payload({"endpoint": self.endpoint, "payload": payload})
        self.sent.append(recorded)
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                self.last_status = getattr(resp, "status", 200)
                self.last_error = None
                return {
                    "ok": True,
                    "status": self.last_status,
                    "span_name": span["name"],
                    "mock": False,
                }
        except urllib.error.HTTPError as exc:
            self.last_status = exc.code
            self.last_error = str(exc)
            return {"ok": False, "status": exc.code, "error": str(exc), "mock": False}
        except Exception as exc:  # noqa: BLE001 — transport failures are expected in DEV
            self.last_status = None
            self.last_error = str(exc)
            return {"ok": False, "status": None, "error": str(exc), "mock": False}


def _otel_value(value: Any) -> dict[str, Any]:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int) and not isinstance(value, bool):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    return {"stringValue": str(value)}
