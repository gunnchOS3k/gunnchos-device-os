"""Physical boot evidence capture command helpers.

Never marks physical boot complete — always GUNNCHOS_PHYSICAL_BOOT_PENDING.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.identity import new_boot_id, utc_now_iso


def capture_physical_boot_stub(
    *,
    manifest_path: str | Path,
    mode: str = "physical-candidate",
    operator_notes: str = "",
) -> dict[str, Any]:
    return {
        "schema": "gunnchos.boot_evidence.v1",
        "capture_kind": "physical_boot_template",
        "boot_id": new_boot_id("phys"),
        "timestamp": utc_now_iso(),
        "mode": mode,
        "manifest_path": str(manifest_path),
        "physical_boot": False,
        "physical_evidence_captured": False,
        "checklist": {
            "power_on_observed": None,
            "firmware_handoff_observed": None,
            "kernel_console_observed": None,
            "init_reached": None,
            "required_services_healthy": None,
            "display_input_verified": None,
            "network_verified": None,
            "secure_boot_state_recorded": None,
            "log_bundle_attached": None,
        },
        "operator_notes": operator_notes,
        "status_tokens": ["GUNNCHOS_PHYSICAL_BOOT_PENDING"],
        "claim_boundary": (
            "Physical capture template only. "
            "Do not claim GUNNCHOS physical boot complete until checklist is filled "
            "from a real target and reviewed."
        ),
    }
