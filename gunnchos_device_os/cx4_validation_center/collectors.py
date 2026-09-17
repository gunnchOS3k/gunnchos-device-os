"""CX4 collector wiring — mocks only for UI contracts; never physical PASS."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from gunnchos_device_os.cx4_validation_center.contracts import EvidenceSource, _now, sha256_bytes


COLLECTOR_SPECS = [
    {"id": "cups", "harness": "collect_cups_physical_evidence.sh", "mime": "application/json"},
    {"id": "av", "harness": "collect_av_diagnostics.sh", "mime": "application/json"},
    {"id": "peripherals", "harness": "collect_peripheral_matrix.sh", "mime": "application/json"},
    {"id": "a11y", "harness": "collect_a11y_evidence.sh", "mime": "application/json"},
    {"id": "support_bundle", "harness": "generate_support_bundle.py", "mime": "application/json"},
    {"id": "firmware", "harness": "firmware_lifecycle_sim.py", "mime": "application/json"},
]


def mock_collector_payload(collector_id: str) -> Dict[str, Any]:
    return {
        "collector_id": collector_id,
        "source": EvidenceSource.SYSTEM_CAPTURED.value,
        "mock": True,
        "physical_pass": False,
        "human_a11y_pass": False,
        "timestamp": _now(),
        "note": "Mock collector for Validation Center UI contracts only. Not physical evidence.",
    }


def run_collector_mock(collector_id: str) -> Dict[str, Any]:
    ids = {c["id"] for c in COLLECTOR_SPECS}
    if collector_id not in ids:
        raise ValueError(f"unknown_collector:{collector_id}")
    payload = mock_collector_payload(collector_id)
    blob = json.dumps(payload, sort_keys=True).encode("utf-8")
    return {
        "file_name": f"{collector_id}_mock.json",
        "mime": "application/json",
        "data": blob,
        "sha256": sha256_bytes(blob),
        "source": EvidenceSource.SYSTEM_CAPTURED.value,
        "mock": True,
        "privacy_classification": "internal",
        "attribution": "system",
        "notes": "SYSTEM_CAPTURED mock — distinct from HUMAN_OBSERVED",
        "payload": payload,
    }


def list_collectors() -> List[Dict[str, Any]]:
    return list(COLLECTOR_SPECS)


def write_mock_harness_stubs(dest: Path) -> List[str]:
    dest.mkdir(parents=True, exist_ok=True)
    written = []
    for spec in COLLECTOR_SPECS:
        path = dest / f"mock_{spec['id']}.json"
        path.write_text(json.dumps(mock_collector_payload(spec["id"]), indent=2), encoding="utf-8")
        written.append(str(path))
    readme = dest / "README.md"
    readme.write_text(
        "# Validation Center collector mocks\n\n"
        "These mocks exercise UI contracts only.\n"
        "`physical_pass=false` always. Do not treat as field evidence.\n",
        encoding="utf-8",
    )
    written.append(str(readme))
    return written
