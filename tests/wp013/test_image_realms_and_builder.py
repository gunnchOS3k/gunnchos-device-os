from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering import image_realms
from gunnchos_device_os.release_engineering.os_image_builder import RealmImageBuilder

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_all_five_realms_load_and_validate():
    result = image_realms.validate_all(REPO_ROOT)
    assert result["ok"] is True
    assert result["IMAGE_REALMS_DIGITALLY_COMPLETE"] is True
    assert set(result["realms"]) == set(image_realms.REALM_FILES)


@pytest.mark.parametrize("alias", ["lab", "evt", "factory", "recovery", "production"])
def test_realm_alias_resolution(alias):
    realm_id = image_realms.resolve_realm_id(alias)
    assert realm_id in image_realms.REALM_FILES


def test_unknown_realm_alias_raises():
    with pytest.raises(KeyError):
        image_realms.resolve_realm_id("not_a_real_realm")


def test_production_realm_forbids_production_keys_present():
    realm = image_realms.load_realm(REPO_ROOT, "production")
    assert realm["trust_roots"]["production_private_keys_present"] is False
    assert realm["status"] == "NOT_RELEASED"


def test_recovery_realm_requires_recovery_partition():
    realm = image_realms.load_realm(REPO_ROOT, "recovery")
    assert realm["recovery_behavior"]["recovery_partition_required"] is True


def test_factory_realm_declares_factory_only_services():
    realm = image_realms.load_realm(REPO_ROOT, "factory")
    assert realm["factory_only_services"]


def test_validate_realm_flags_tampered_production_key_source():
    realm = image_realms.load_realm(REPO_ROOT, "production")
    tampered = dict(realm)
    tampered["trust_roots"] = dict(realm["trust_roots"])
    tampered["trust_roots"]["production_private_keys_present"] = True
    failures = image_realms.validate_realm(tampered)
    assert "production_private_keys_present_not_false" in failures


@pytest.fixture()
def builder():
    return RealmImageBuilder(REPO_ROOT)


@pytest.mark.parametrize("realm", ["lab", "evt", "factory", "recovery", "production"])
def test_build_inspect_verify_each_realm(builder, realm):
    build_result = builder.build(realm, unsigned=False)
    assert build_result["ok"] is True

    inspect_result = builder.inspect(realm)
    assert inspect_result["ok"] is True
    manifest = inspect_result["manifest"]
    assert manifest["package_manifest"]
    assert manifest["sbom"]["components"]
    assert manifest["source_shas"]["repo_head_sha"]

    verify_result = builder.verify(realm)
    assert verify_result["ok"] is True, verify_result["failures"]


def test_production_realm_always_builds_unsigned_and_not_released(builder):
    result = builder.build("production", unsigned=False)  # even asking for signed
    assert result["ok"] is True
    assert result["signed"] is False
    assert result["PRODUCTION_RELEASE_CLAIMED"] is False
    assert result["SHIPPING_IMAGE"] is False
    assert result["payload_class"] == "production_intent_digital"

    manifest = builder.inspect("production")["manifest"]
    assert manifest["status"] == "NOT_RELEASED"
    assert manifest["production_keys_used"] is False
    assert manifest["SHIPPING_IMAGE"] is False
    assert manifest["payload_class"] == "production_intent_digital"
    assert manifest["artifacts"]["rootfs_tarball"]["size_bytes"] >= 2 * 1024 * 1024


def test_evt_build_is_reproducible_across_two_builds(builder):
    first = builder.build("evt", unsigned=True)
    second = builder.build("evt", unsigned=True)
    assert first["rootfs_sha256"] == second["rootfs_sha256"]


def test_evt_realm_rootfs_carries_dev_toolchain_but_factory_does_not(builder):
    builder.build("evt", unsigned=True)
    builder.build("factory", unsigned=True)
    evt_manifest = builder.inspect("evt")["manifest"]
    factory_manifest = builder.inspect("factory")["manifest"]
    evt_paths = {row["path"] for row in evt_manifest["package_manifest"]}
    factory_paths = {row["path"] for row in factory_manifest["package_manifest"]}
    assert any("bin/gunnchctl" in p for p in evt_paths)
    assert not any("bin/gunnchctl" in p for p in factory_paths)
    # Production-intent: Alpine base present in both.
    assert any(p.endswith("etc/alpine-release") or "alpine-release" in p for p in evt_paths)
    assert any("alpine-release" in p for p in factory_paths)
    # Full userspace on EVT; factory gets device-os lib but not games tree.
    assert any("userspace/games" in p for p in evt_paths)
    assert not any("userspace/games" in p for p in factory_paths)


def test_recovery_is_lean_production_intent(builder):
    result = builder.build("recovery", unsigned=True)
    assert result["ok"] is True
    manifest = builder.inspect("recovery")["manifest"]
    assert manifest["payload_class"] == "production_intent_digital"
    assert manifest["payload"]["payload_profile"] == "production_intent_recovery"
    paths = {row["path"] for row in manifest["package_manifest"]}
    assert any("alpine-release" in p for p in paths)
    assert not any("userspace/games" in p for p in paths)
    assert manifest["artifacts"]["rootfs_tarball"]["size_bytes"] >= 2 * 1024 * 1024


def test_verify_detects_rootfs_tamper(builder, tmp_path):
    builder.build("recovery", unsigned=False)
    inspect_result = builder.inspect("recovery")
    manifest = inspect_result["manifest"]
    rootfs_path = REPO_ROOT / manifest["artifacts"]["rootfs_tarball"]["path"]
    original = rootfs_path.read_bytes()
    try:
        rootfs_path.write_bytes(original + b"tampered")
        verify_result = builder.verify("recovery")
        assert verify_result["ok"] is False
        assert "rootfs_hash_mismatch" in verify_result["failures"]
    finally:
        rootfs_path.write_bytes(original)
