"""Phase 4F compliance readiness tests."""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
COMPLIANCE = ROOT / "compliance"
CERT_CLAIMS = re.compile(
    r"\b(certified|certification complete|WCAG conform|GDPR compliant|COPPA compliant|FERPA compliant)\b",
    re.IGNORECASE,
)


def test_compliance_docs_exist():
    required = [
        COMPLIANCE / "README.md",
        COMPLIANCE / "privacy" / "DATA_INVENTORY.md",
        COMPLIANCE / "privacy" / "LOCALSTORAGE_INVENTORY.md",
        COMPLIANCE / "privacy" / "STUDENT_YOUTH_DATA_RISK_REGISTER.md",
        COMPLIANCE / "privacy" / "PRIVACY_POLICY_DRAFT.md",
        COMPLIANCE / "accessibility" / "WCAG_SELF_ASSESSMENT.md",
        COMPLIANCE / "accessibility" / "KEYBOARD_NAVIGATION_CHECKLIST.md",
        COMPLIANCE / "accessibility" / "ACCESSIBILITY_TEST_REPORT_TEMPLATE.md",
        COMPLIANCE / "legal" / "TERMS_OF_USE_DRAFT.md",
        COMPLIANCE / "legal" / "OPEN_SOURCE_LICENSE_INVENTORY.md",
        COMPLIANCE / "legal" / "THIRD_PARTY_DEPENDENCIES.md",
        ROOT / "docs" / "PHASE4F_COMPLIANCE_READINESS.md",
    ]
    for path in required:
        assert path.exists(), f"missing {path}"


def test_data_inventory_includes_localstorage_items():
    text = (COMPLIANCE / "privacy" / "LOCALSTORAGE_INVENTORY.md").read_text(encoding="utf-8")
    for key in (
        "gunnchos-profile",
        "gunnchos-settings-v1",
        "gunnchos-workspace-v1",
        "gunnchos-notes-v1",
        "gunnchos-local-media-recent",
    ):
        assert key in text


def test_accessibility_checklist_exists():
    path = COMPLIANCE / "accessibility" / "WCAG_SELF_ASSESSMENT.md"
    text = path.read_text(encoding="utf-8")
    assert "not WCAG conformance certification" in text or "not certification" in text.lower()


def test_no_certification_claim_without_evidence_in_compliance_docs():
    for md in COMPLIANCE.rglob("*.md"):
        text = md.read_text(encoding="utf-8")
        if "CLAIM_BOUNDARY" in md.name or "DRAFT" in md.name or "TEMPLATE" in md.name:
            continue
        # Allow negated claims like "not certification"
        for match in CERT_CLAIMS.finditer(text):
            start = max(0, match.start() - 40)
            context = text[start : match.end() + 20].lower()
            assert "not " in context or "no " in context or "draft" in context, (
                f"Possible certification claim in {md}: {match.group()}"
            )


def test_beta_gate_legal_privacy_accessibility_is_prototype():
    data = yaml.safe_load((ROOT / "beta_gate" / "beta_gate_status.yaml").read_text(encoding="utf-8"))
    item = data["items"].get("legal_privacy_accessibility", {})
    assert item.get("status") in ("prototype", "missing")
    assert item.get("status") != "validated"
    assert data["beta_ready"] is False
