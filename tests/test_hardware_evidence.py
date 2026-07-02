"""Hardware evidence baseline tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_hardware_validation_docs_exist():
    for name in (
        "REFERENCE_HARDWARE_VALIDATION_TEMPLATE.md",
        "CONTAINER_KIOSK_VALIDATION_LOG.md",
        "HARDWARE_CLAIM_BOUNDARY.md",
    ):
        assert (ROOT / "hardware_validation" / name).exists()


def test_no_false_physical_validation_claim():
    boundary = (ROOT / "hardware_validation" / "HARDWARE_CLAIM_BOUNDARY.md").read_text(encoding="utf-8")
    assert "No physical hardware validation" in boundary or "not" in boundary.lower()
