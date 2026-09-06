"""Executable/package version provenance for Learning OS integration."""
from __future__ import annotations

from typing import Any

CONTRACT_VERSION = "waike.learning_os.deviceos_integration_contract.v1"
# Gate C logical integration label — not interchangeable with app package version.
GATE_C_LOGICAL_VERSION = "0.6.0-gate-c"


def build_provenance(
    *,
    app_version: str | None = None,
    artifact_hash: str | None = None,
    platform_sha: str | None = None,
) -> dict[str, Any]:
    return {
        "contract_version": CONTRACT_VERSION,
        "gate_c_logical_version": GATE_C_LOGICAL_VERSION,
        "platform_source_sha": platform_sha,
        "app_version": app_version,
        "artifact_hash": artifact_hash,
        "version_clarity": (
            "gate_c_logical_version is the Platform Gate C integration label; "
            "app_version is the installed Learning OS package/executable version. "
            "Do not equate them."
        ),
    }
