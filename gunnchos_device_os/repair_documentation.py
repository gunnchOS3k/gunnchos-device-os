"""Repair documentation digital catalog (CG-QUALITY-008).

Structured repair doc index with required sections for field/tech support.
Does not claim physical repair procedures are hardware-validated.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


CLAIM_BOUNDARY = (
    "Digital repair-documentation catalog and completeness checks only. "
    "No claim that physical repair steps are validated on production hardware."
)

TOKEN_REPAIR_DOCUMENTATION_PASS = "GUNNCHOS_REPAIR_DOCUMENTATION_DIGITAL_PASS"

REQUIRED_SECTIONS = (
    "safety_warnings",
    "tools_required",
    "disassembly_steps",
    "part_identification",
    "reassembly_steps",
    "post_repair_checks",
    "escalation_path",
)

_DOCS: dict[str, dict[str, Any]] = {
    "battery_swap": {
        "title": "Battery module swap (prototype)",
        "sections": {
            "safety_warnings": "Power off; ESD precautions; no swollen cells.",
            "tools_required": "Plastic spudger, PH0 screwdriver, ESD strap.",
            "disassembly_steps": "Remove back shell → disconnect BMS → lift pack.",
            "part_identification": "Pack SKU GOS-BATT-EVT1; polarity keyed.",
            "reassembly_steps": "Seat pack → reconnect BMS → torque screws to spec.",
            "post_repair_checks": "Boot to recovery; verify charge path telemetry.",
            "escalation_path": "If BMS fault persists → RMA to depot.",
        },
    },
    "display_flex": {
        "title": "Display flex reseat (prototype)",
        "sections": {
            "safety_warnings": "Power off; avoid bending sharp folds in flex.",
            "tools_required": "Spudger, tweezers, isopropyl wipe.",
            "disassembly_steps": "Open hinge cover → release latch → free flex.",
            "part_identification": "Flex SKU GOS-DISP-FLEX-EVT1.",
            "reassembly_steps": "Align keying → latch → route strain relief.",
            "post_repair_checks": "Display bring-up; touch self-test.",
            "escalation_path": "Persistent artifacts → replace panel assembly.",
        },
    },
    "ring_pairing_reset": {
        "title": "Ring pairing reset (software + hardware support)",
        "sections": {
            "safety_warnings": "Do not force-pair untrusted rings.",
            "tools_required": "Host device; optional USB recovery cable.",
            "disassembly_steps": "N/A — software path preferred.",
            "part_identification": "Ring device_id from pairing log.",
            "reassembly_steps": "N/A",
            "post_repair_checks": "Re-pair; verify authenticated input protocol.",
            "escalation_path": "Auth failures → revoke device + factory ring flash.",
        },
    },
}


@dataclass
class RepairDocResult:
    ok: bool
    doc_id: str
    missing_sections: list[str] = field(default_factory=list)
    present_sections: list[str] = field(default_factory=list)
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RepairDocumentationCatalog:
    """Catalog of repair docs with required-section completeness checks."""

    docs: dict[str, dict[str, Any]] = field(
        default_factory=lambda: {k: dict(v) for k, v in _DOCS.items()}
    )

    def list_docs(self) -> list[str]:
        return sorted(self.docs.keys())

    def validate_doc(self, doc_id: str) -> RepairDocResult:
        doc = self.docs.get(doc_id)
        if not doc:
            return RepairDocResult(
                ok=False,
                doc_id=doc_id,
                missing_sections=list(REQUIRED_SECTIONS),
                details={"error": "unknown_doc", "claim_boundary": CLAIM_BOUNDARY},
            )
        sections = doc.get("sections") or {}
        present = [s for s in REQUIRED_SECTIONS if sections.get(s)]
        missing = [s for s in REQUIRED_SECTIONS if s not in present]
        return RepairDocResult(
            ok=not missing,
            doc_id=doc_id,
            missing_sections=missing,
            present_sections=present,
            details={
                "title": doc.get("title"),
                "claim_boundary": CLAIM_BOUNDARY,
            },
        )

    def validate_all(self) -> dict[str, RepairDocResult]:
        return {doc_id: self.validate_doc(doc_id) for doc_id in self.list_docs()}


def run_repair_documentation() -> dict[str, Any]:
    catalog = RepairDocumentationCatalog()
    results = {k: v.to_dict() for k, v in catalog.validate_all().items()}
    ok = bool(results) and all(r["ok"] for r in results.values())
    return {
        "ok": ok,
        "token": TOKEN_REPAIR_DOCUMENTATION_PASS if ok else f"{TOKEN_REPAIR_DOCUMENTATION_PASS}_FAIL",
        "requirement_id": "CG-QUALITY-008",
        "claim_boundary": CLAIM_BOUNDARY,
        "required_sections": list(REQUIRED_SECTIONS),
        "documents": results,
        "hardware_validated_repair_claimed": False,
    }
