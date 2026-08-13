"""Honesty gates for Handheld IMAGE_FIT_MANIFEST evidence."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.release_engineering.handheld_image_fit import (
    build_handheld_image_fit_manifest,
    write_handheld_image_fit_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
MANIFEST = REPO_ROOT / "artifacts" / "handheld_image_fit" / "IMAGE_FIT_MANIFEST.json"
BOOT_PIN = REPO_ROOT / "artifacts" / "handheld_image_fit" / "SHARED_BOOT_PIN.json"


def test_emit_manifest_matches_tracked_artifact():
    live = build_handheld_image_fit_manifest(REPO_ROOT)
    assert MANIFEST.is_file(), "IMAGE_FIT_MANIFEST.json must be tracked evidence"
    assert BOOT_PIN.is_file(), "SHARED_BOOT_PIN.json must pin boot sizes for CI"
    tracked = json.loads(MANIFEST.read_text(encoding="utf-8"))
    pin = json.loads(BOOT_PIN.read_text(encoding="utf-8"))
    for doc in (live, tracked):
        doc.pop("generated_at_utc", None)
        doc.pop("device_os_tip", None)
    assert live["PRODUCTION_RELEASE_CLAIMED"] is False
    assert tracked["PRODUCTION_RELEASE_CLAIMED"] is False
    assert live["SHIPPING_IMAGE"] is False
    assert tracked["SHIPPING_IMAGE"] is False
    assert live["larger_emmc_sku_invented"] is False
    assert tracked["npi"]["recommended_status"] == live["npi"]["recommended_status"]
    assert tracked["npi"]["closure_gate_met"] == live["npi"]["closure_gate_met"]
    assert tracked["fit_assessment"]["production_image_fit_verdict"] == live["fit_assessment"][
        "production_image_fit_verdict"
    ]
    for realm in ("production_shipping_image_definition", "recovery_image"):
        t = tracked["realms"][realm]["rootfs_tarball"]
        l = live["realms"][realm]["rootfs_tarball"]
        assert t["sha256"] == l["sha256"]
        assert t["compressed_bytes"] == l["compressed_bytes"]
        assert t["uncompressed_file_bytes"] == l["uncompressed_file_bytes"]
    assert live["shared_bootable_reference"]["size_source"] == "shared_boot_pin"
    assert live["shared_bootable_reference"]["combined_bytes"] == pin["combined_bytes"]
    assert tracked["shared_bootable_reference"]["combined_bytes"] == pin["combined_bytes"]
    assert tracked["sizes_summary_gib"]["slot_a_composed"] == live["sizes_summary_gib"][
        "slot_a_composed"
    ]
    assert tracked["sizes_summary_gib"]["recovery_composed"] == live["sizes_summary_gib"][
        "recovery_composed"
    ]


def test_slot_numeric_margins_positive_production_intent():
    m = build_handheld_image_fit_manifest(REPO_ROOT)
    for slot in ("slot_a", "slot_b", "recovery"):
        fit = m["slot_fit"][slot]
        assert fit["fits_budget"] is True
        assert fit["margin_gib"] > 0
        assert fit["production_intent_digital"] is True
    assert m["fit_assessment"]["stub_like_rootfs_payloads"] is False
    assert m["fit_assessment"]["production_intent_digital_present"] is True
    assert m["fit_assessment"]["production_mlp_disk_image_present"] is False
    assert m["fit_assessment"]["production_image_fit_verdict"] == (
        "PASS_PRODUCTION_INTENT_DIGITAL_FIT"
    )
    assert m["npi"]["closure_gate_met"] is True
    assert m["npi"]["recommended_status"] == "CLOSE"
    assert m["realms"]["production_shipping_image_definition"]["status"] == "NOT_RELEASED"
    assert m["realms"]["production_shipping_image_definition"]["PRODUCTION_RELEASE_CLAIMED"] is False
    assert m["realms"]["production_shipping_image_definition"]["SHIPPING_IMAGE"] is False
    assert m["slot_fit"]["slot_a"]["realm_id"] == "PRODUCTION_SHIPPING_IMAGE_DEFINITION"
    prod = m["realms"]["production_shipping_image_definition"]["rootfs_tarball"]
    assert prod["compressed_bytes"] >= 2 * 1024 * 1024


def test_writer_roundtrip(tmp_path):
    out = tmp_path / "IMAGE_FIT_MANIFEST.json"
    written = write_handheld_image_fit_manifest(REPO_ROOT, out_path=out)
    assert out.is_file()
    assert written["PRODUCTION_RELEASE_CLAIMED"] is False
    assert written["SHIPPING_IMAGE"] is False
    reloaded = json.loads(out.read_text(encoding="utf-8"))
    assert reloaded["schema"] == "gunnchos.device_os.handheld_image_fit_manifest.v1"
    assert reloaded["npi"]["defect_id"] == "NPI_DEFECT-HANDHELD-IMAGE-SLOT-FIT-001"
