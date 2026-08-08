"""SBOM + provenance helpers for the cloud DEV plane (DEV realm)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.cloud_dev_plane.claim import CLAIM_BOUNDARY, REALM
from gunnchos_device_os.cloud_dev_plane.server import DEFAULT_PORTS, SERVICE_ROLES
from gunnchos_device_os.identity import utc_now_iso

COMPONENTS = [
    {"name": "gunnchos-dev-plane-gateway", "version": "0.1.0-dev", "kind": "gateway"},
    {"name": "gunnchos-dev-plane-identity", "version": "0.1.0-dev", "kind": "identity"},
    {"name": "gunnchos-dev-plane-enrollment", "version": "0.1.0-dev", "kind": "enrollment"},
    {"name": "gunnchos-dev-plane-sync", "version": "0.1.0-dev", "kind": "sync"},
    {"name": "gunnchos-dev-plane-saves", "version": "0.1.0-dev", "kind": "saves"},
    {"name": "gunnchos-dev-plane-matchmaking-meta", "version": "0.1.0-dev", "kind": "matchmaking"},
    {"name": "gunnchos-dev-plane-ota-metadata", "version": "0.1.0-dev", "kind": "ota_metadata"},
    {"name": "gunnchos-dev-plane-telemetry", "version": "0.1.0-dev", "kind": "telemetry"},
    {"name": "gunnchos-dev-plane-fleet", "version": "0.1.0-dev", "kind": "fleet"},
    {"name": "gunnchos-dev-plane-diagnostics", "version": "0.1.0-dev", "kind": "diagnostics"},
    {"name": "gunnchos-otel-collector-dev", "version": "0.96.0", "kind": "otel"},
]


def build_cyclonedx() -> dict[str, Any]:
    return {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "timestamp": utc_now_iso(),
            "component": {
                "type": "application",
                "name": "gunnchos-cloud-dev-plane",
                "version": "0.1.0-dev",
                "properties": [
                    {"name": "gunnchos:realm", "value": REALM},
                    {"name": "gunnchos:claim_boundary", "value": CLAIM_BOUNDARY},
                ],
            },
        },
        "components": [
            {
                "type": "library",
                "name": c["name"],
                "version": c["version"],
                "purl": f"pkg:generic/{c['name']}@{c['version']}",
                "properties": [{"name": "gunnchos:kind", "value": c["kind"]}],
            }
            for c in COMPONENTS
        ],
    }


def build_provenance(materials: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "claim_boundary": CLAIM_BOUNDARY,
        "realm": REALM,
        "predicateType": "https://gunnchos.local/provenance/dev-plane/v1",
        "predicate": {
            "builder": {"id": "gunnchos_device_os.cloud_dev_plane.provenance", "realm": REALM},
            "invocation": {
                "services": sorted(s for s in SERVICE_ROLES if s != "gateway"),
                "ports": DEFAULT_PORTS,
                "production_keys_used": False,
            },
            "materials": materials or {},
        },
        "generated_at": utc_now_iso(),
        "mock": False,
    }


def write_artifacts(out_dir: str | Path) -> dict[str, Any]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    sbom = build_cyclonedx()
    sbom_path = out / "cloud_dev_plane.cdx.json"
    sbom_path.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(sbom_path.read_bytes()).hexdigest()
    prov = build_provenance({"cloud_dev_plane.cdx.json": digest})
    prov_path = out / "cloud_dev_plane.provenance.json"
    prov_path.write_text(json.dumps(prov, indent=2) + "\n", encoding="utf-8")
    return {"sbom": str(sbom_path), "provenance": str(prov_path), "sbom_sha256": digest}
