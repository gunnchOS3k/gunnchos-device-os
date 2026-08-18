"""Supervisor-ready UML pack is present and maps to real source."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UML = ROOT / "docs" / "uml"

REQUIRED = [
    UML / "README.md",
    UML / "traceability_matrix.md",
    UML / "current" / "index.md",
    UML / "current" / "use_case.md",
    UML / "current" / "component.md",
    UML / "current" / "package.md",
    UML / "current" / "deployment.md",
    UML / "current" / "sequence_boot.md",
    UML / "current" / "state_mode.md",
    UML / "current" / "activity_update_recovery.md",
    UML / "future" / "index.md",
    UML / "legacy" / "index.md",
]


def test_uml_pack_replaces_placeholder():
    text = (UML / "README.md").read_text(encoding="utf-8")
    assert "SpectrumX: full UML pack" not in text
    assert "current/" in text
    assert "Not" in text or "not" in text


def test_required_uml_files_exist():
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.is_file()]
    assert not missing, missing


def test_traceability_names_real_sources():
    text = (UML / "traceability_matrix.md").read_text(encoding="utf-8")
    for needle in (
        "apps/launcher_mock",
        "gunnchos_device_os",
        "gate1-boot",
        "service_continuity",
        "Makefile",
    ):
        assert needle in text


def test_boot_sequence_does_not_claim_physical():
    text = (UML / "current" / "sequence_boot.md").read_text(encoding="utf-8")
    assert "PHYSICAL_BOOT_PENDING" in text
    assert "run_boot_probe" in text
