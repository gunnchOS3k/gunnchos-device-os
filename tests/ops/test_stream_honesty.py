from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.ops.claim import COMMERCIAL_WARRANTY, PRODUCTION_RELEASE_CLAIMED
from gunnchos_device_os.ops.stream_eval import evaluate

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_stream_eval_is_digital_prep_not_production(tmp_path):
    report = evaluate(REPO_ROOT, tmp_path / "eval.json")
    assert report["ok"] is True
    assert report["status"] == "DIGITAL_PREPARATION"
    assert report["PRODUCTION_RELEASE_CLAIMED"] is False
    assert PRODUCTION_RELEASE_CLAIMED is False
    assert report["commercial_warranty"] == COMMERCIAL_WARRANTY == "EXTERNAL"
    assert report["cursor_merges"] is False
    assert report["factory"]["cert_request"] == "EXTERNAL_PENDING"
    assert report["factory"]["esim"] == "EXTERNAL_PENDING"
    assert report["factory"]["physical_media_sanitize"] == "EXTERNAL"
    assert "production_keys" in report["external"]
    assert "rfq_purchase_fab" in report["external"]
    assert "commercial_warranty" in report["external"]
    text = (tmp_path / "eval.json").read_text(encoding="utf-8")
    assert "PRODUCTION_RELEASE_CLAIMED\": false" in text or '"PRODUCTION_RELEASE_CLAIMED": false' in text
