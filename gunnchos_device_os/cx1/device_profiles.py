"""Device-profile qualification matrix for CX1 ordinary-user foundations."""

from __future__ import annotations

from typing import Dict

# Status vocabulary from CX1 prompt
SUPPORTED = "SUPPORTED"
DEGRADED = "DEGRADED_SUPPORTED"
PROVIDER_REQUIRED = "PROVIDER_REQUIRED"
NOT_APPLICABLE = "NOT_APPLICABLE"
PHYSICAL_PENDING = "PHYSICAL_PENDING"

PROFILES = (
    "student_14_5",
    "handheld_hybrid",
    "ds_xl_coder",
    "edge_io_rings",
    "docked",
    "generic_ci_qemu",
)

DOMAINS = (
    "identity",
    "vault",
    "app_center",
    "permissions",
    "browser",
    "productivity",
    "connect",
    "printing",
    "assist",
    "offline",
    "security",
    "care",
)


def qualification_matrix() -> Dict[str, Dict[str, str]]:
    """Honest CX1 digital qualification — not Device Lab gate evidence."""
    base = {
        "identity": SUPPORTED,
        "vault": SUPPORTED,
        "app_center": SUPPORTED,
        "permissions": DEGRADED,  # xdg portal often absent on CI/macOS
        "browser": DEGRADED,  # digital equivalent when browser binary absent
        "productivity": DEGRADED,  # LibreOffice may be present (PASS) or fixture
        "connect": DEGRADED,  # local fixtures; no Gmail/Outlook
        "printing": DEGRADED,  # virtual PDF digital; physical pending
        "assist": DEGRADED,  # DIGITAL_A11Y_PASS paths; human pending
        "offline": SUPPORTED,
        "security": DEGRADED,  # discovery honest, no fake TPM claims
        "care": SUPPORTED,
    }
    matrix = {profile: dict(base) for profile in PROFILES}
    # Edge IO / Rings — rings physical pending
    matrix["edge_io_rings"]["printing"] = PHYSICAL_PENDING
    matrix["edge_io_rings"]["assist"] = DEGRADED
    # Docked — print more relevant but physical still pending
    matrix["docked"]["printing"] = DEGRADED
    # CI/QEMU — provider-dependent lanes
    matrix["generic_ci_qemu"]["browser"] = PROVIDER_REQUIRED
    matrix["generic_ci_qemu"]["productivity"] = PROVIDER_REQUIRED
    matrix["generic_ci_qemu"]["printing"] = DEGRADED
    # Student handheld — games/media not in CX1 scope
    matrix["student_14_5"]["connect"] = DEGRADED
    return matrix


def matrix_document() -> dict:
    return {
        "schema": "gunnchos.cx1.device_profile_qualification.v1",
        "profiles": list(PROFILES),
        "domains": list(DOMAINS),
        "matrix": qualification_matrix(),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "claim_boundary": "cx1_digital_qualification_not_device_lab_gate",
    }
