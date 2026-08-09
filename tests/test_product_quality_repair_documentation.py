"""Product-quality tests for repair documentation (CG-QUALITY-008)."""
from __future__ import annotations

from gunnchos_device_os.repair_documentation import (
    REQUIRED_SECTIONS,
    TOKEN_REPAIR_DOCUMENTATION_PASS,
    RepairDocumentationCatalog,
    run_repair_documentation,
)


def test_product_quality_repair_documentation_pass():
    report = run_repair_documentation()
    assert report["ok"] is True
    assert report["token"] == TOKEN_REPAIR_DOCUMENTATION_PASS
    assert report["requirement_id"] == "CG-QUALITY-008"
    assert report["hardware_validated_repair_claimed"] is False
    assert set(report["required_sections"]) == set(REQUIRED_SECTIONS)


def test_product_quality_repair_documentation_all_docs_complete():
    catalog = RepairDocumentationCatalog()
    assert len(catalog.list_docs()) >= 3
    for doc_id in catalog.list_docs():
        result = catalog.validate_doc(doc_id)
        assert result.ok is True, doc_id
        assert result.missing_sections == []


def test_product_quality_repair_documentation_unknown_doc_fails():
    catalog = RepairDocumentationCatalog()
    result = catalog.validate_doc("not_a_real_repair_doc")
    assert result.ok is False
    assert result.missing_sections == list(REQUIRED_SECTIONS)
