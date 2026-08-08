"""OpenTelemetry attribute conventions for gunnchos.* namespaces (DEV)."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.cloud_dev_plane.claim import CLAIM_BOUNDARY, REALM
from gunnchos_device_os.cloud_dev_plane.privacy_redaction import redact_payload

# Semantic conventions — gunnchos product namespace (not vendor OTEL forks).
GUNNCHOS_ATTR_SERVICE = "gunnchos.service"
GUNNCHOS_ATTR_MODE = "gunnchos.mode"
GUNNCHOS_ATTR_DEVICE_ID = "gunnchos.device.id"
GUNNCHOS_ATTR_ORG_ID = "gunnchos.org.id"
GUNNCHOS_ATTR_REALM = "gunnchos.realm"
GUNNCHOS_ATTR_CLAIM = "gunnchos.claim_boundary"
GUNNCHOS_ATTR_EVENT = "gunnchos.event.type"
GUNNCHOS_ATTR_FLEET_RING = "gunnchos.fleet.ring"
GUNNCHOS_ATTR_CHANNEL = "gunnchos.ota.channel"

SPAN_NAMES = {
    "identity": "gunnchos.identity.register",
    "enrollment": "gunnchos.enrollment.submit",
    "sync": "gunnchos.sync.enqueue",
    "saves": "gunnchos.saves.put",
    "matchmaking": "gunnchos.matchmaking.publish",
    "telemetry": "gunnchos.telemetry.emit",
    "update_metadata": "gunnchos.ota.metadata_set",
    "fleet": "gunnchos.fleet.heartbeat",
    "diagnostics": "gunnchos.diagnostics.report",
}


def build_attributes(
    *,
    service: str,
    mode: str,
    event_type: str | None = None,
    device_id: str | None = None,
    org_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    attrs: dict[str, Any] = {
        GUNNCHOS_ATTR_SERVICE: service,
        GUNNCHOS_ATTR_MODE: mode,
        GUNNCHOS_ATTR_REALM: REALM,
        GUNNCHOS_ATTR_CLAIM: CLAIM_BOUNDARY,
    }
    if event_type:
        attrs[GUNNCHOS_ATTR_EVENT] = event_type
    if device_id:
        attrs[GUNNCHOS_ATTR_DEVICE_ID] = device_id
    if org_id:
        attrs[GUNNCHOS_ATTR_ORG_ID] = org_id
    if extra:
        attrs.update(extra)
    return redact_payload(attrs)
