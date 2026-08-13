"""Digital inventory — UNKNOWN_RELEASE_BLOCKING, Beat Link, AI licenses."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.digital_inventory.bom import build_inventory, write_inventory
from gunnchos_device_os.digital_inventory.rights import (
    ALLOWED_BEATLINK_LICENSES,
    check_ai_model_licenses,
    check_beatlink,
)
from gunnchos_device_os.digital_inventory.scanner import BLOCKING, _component


def test_unknown_provenance_is_release_blocking():
    row = _component(kind="python", name="mystery-lib", source="requirements.txt")
    assert row["unknown_release_blocking"] is True
    assert row["release_status"] == BLOCKING
    assert row["license"] == "UNKNOWN"


def test_known_license_is_not_blocking():
    known = {"pytest": {"license": "MIT", "provenance": "pypi"}}
    row = _component(kind="python", name="pytest", source="requirements.txt", known=known)
    assert row["unknown_release_blocking"] is False
    assert row["license"] == "MIT"


def test_inventory_builds_and_flags_unknown(tmp_path: Path):
    repo = Path(__file__).resolve().parents[2]
    inventory = build_inventory(repo)
    assert inventory["legal_approval"] == "HUMAN/EXTERNAL"
    assert inventory["EXTERNAL_PENTEST_COMPLETE"] is False
    assert inventory["counts"]["components"] >= 1
    assert "sbom" in inventory["boms"]
    assert "hbom" in inventory["boms"]
    assert "ai_bom" in inventory["boms"]
    dest = tmp_path / "inv"
    written = write_inventory(repo, dest)
    assert (dest / "DIGITAL_INVENTORY.json").exists()
    assert (dest / "sbom.cdx.json").exists()
    assert (dest / "hbom.json").exists()
    assert (dest / "ai_bom.json").exists()
    assert written["schema"] == "gunnchos.digital_inventory.v1"


def test_beatlink_allowed_licenses_exclude_commercial_rips():
    assert "public_domain" in ALLOWED_BEATLINK_LICENSES
    assert "commercial" not in ALLOWED_BEATLINK_LICENSES
    repo = Path(__file__).resolve().parents[2]
    sibling = repo.parent / "beatlink-party"
    result = check_beatlink(sibling if sibling.exists() else None)
    if result["present"]:
        assert result["claim_boundary"]
        # If catalogs are present they must stay in the rights-safe set or block.
        for item in result.get("blocking") or []:
            assert "license" in item or "register" in item


def test_ai_model_unknown_license_blocks():
    models = [
        {
            "kind": "ai_model",
            "name": "mystery-weights",
            "license": "UNKNOWN",
            "unknown_release_blocking": True,
        }
    ]
    result = check_ai_model_licenses(models)
    assert result["unknown_release_blocking"] == 1
    assert result["machine_tracked"] is True


def test_cyclonedx_does_not_claim_certification(tmp_path: Path):
    repo = Path(__file__).resolve().parents[2]
    dest = tmp_path / "inv"
    write_inventory(repo, dest)
    cdx = json.loads((dest / "sbom.cdx.json").read_text(encoding="utf-8"))
    assert cdx["bomFormat"] == "CycloneDX"
    props = cdx["metadata"]["properties"]
    assert any("not a legal" in p["value"].lower() or "HUMAN" in p["value"] for p in props)
