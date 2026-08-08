"""Reproducible system image digital path tests."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.system_image import (
    TOKEN_DIGITAL_PASS,
    TOKEN_PHYSICAL_PENDING,
    ImageBuildRequest,
    ReproducibleImageBuilder,
    build_and_validate,
    validate_image_bundle,
)


def test_build_and_validate_earns_digital_pass(tmp_path: Path):
    out = tmp_path / "artifacts"
    result = build_and_validate(out)
    assert result["build"]["production_keys_used"] is False
    assert result["build"]["bootable"] is False
    validation = result["validation"]
    assert validation["ok"] is True, validation["checks"]
    assert validation["token"] == TOKEN_DIGITAL_PASS
    assert TOKEN_PHYSICAL_PENDING in validation["status_tokens"]
    assert validation["full_operational_product_claimed"] is False
    assert (out / "blueprint.json").exists()
    assert (out / "sbom.cdx.json").exists()
    assert (out / "provenance.json").exists()
    assert (out / "dev_factory_image.json").exists()
    assert (out / "version_manifest.json").exists()
    assert (out / "dev_signature.json").exists()


def test_reproducible_digest_stable(tmp_path: Path):
    req = ImageBuildRequest(build_id="repro-test", out_dir=str(tmp_path / "a"))
    d1 = ReproducibleImageBuilder(req).build()["content_digest_sha256"]
    req2 = ImageBuildRequest(build_id="repro-test", out_dir=str(tmp_path / "b"))
    d2 = ReproducibleImageBuilder(req2).build()["content_digest_sha256"]
    assert d1 == d2


def test_blueprint_covers_required_image_path_topics(tmp_path: Path):
    built = ReproducibleImageBuilder(
        ImageBuildRequest(out_dir=str(tmp_path / "artifacts"))
    ).build()
    validation = validate_image_bundle(built["out_dir"])
    names = {c["check"] for c in validation["checks"]}
    for topic in (
        "blueprint_has_kernel",
        "blueprint_has_bootloader",
        "blueprint_has_init",
        "blueprint_has_drivers",
        "blueprint_has_filesystem",
        "blueprint_has_compositor_shell",
        "blueprint_has_packages",
        "blueprint_has_sandbox",
        "blueprint_has_updater",
        "blueprint_has_recovery",
        "blueprint_has_vm_emulation_target",
        "no_production_keys",
        "dev_signature_valid",
        "reproducible_digest",
    ):
        assert topic in names


def test_tampered_bundle_fails_validation(tmp_path: Path):
    out = tmp_path / "artifacts"
    ReproducibleImageBuilder(ImageBuildRequest(out_dir=str(out))).build()
    # Tamper factory image
    path = out / "dev_factory_image.json"
    path.write_text(path.read_text(encoding="utf-8").replace("DEV", "PROD"), encoding="utf-8")
    validation = validate_image_bundle(out)
    assert validation["ok"] is False
    assert validation["token"] is None
