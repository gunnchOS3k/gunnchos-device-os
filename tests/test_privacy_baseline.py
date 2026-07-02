"""Privacy baseline evidence tests."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_privacy_baseline_doc_exists():
    doc = ROOT / "docs" / "PRIVACY_BETA_BASELINE.md"
    assert doc.exists()
    text = doc.read_text(encoding="utf-8")
    assert "localStorage" in text
    assert "certification" in text.lower()


def test_privacy_status_module():
    privacy = ROOT / "apps" / "launcher_mock" / "src" / "services" / "privacyStatus.ts"
    assert privacy.exists()
    assert "localStorage" in privacy.read_text(encoding="utf-8")
