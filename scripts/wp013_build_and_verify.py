#!/usr/bin/env python3
"""WP-013 exit-token generator.

Runs the real WP-013 subsystems end to end (image realm builds, gunnchSDK
package/install/run pipeline, API compatibility gate, factory provisioning,
recovery/serviceability) and writes the honest results — plus the pytest
suite result — to `artifacts/wp013/WP-013-RESULT.json`. Tokens are only set
`true` when the corresponding step actually passed in this run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.release_engineering import image_realms  # noqa: E402
from gunnchos_device_os.release_engineering.ab_update import (  # noqa: E402
    ABUpdateManager,
    build_update_metadata,
)
from gunnchos_device_os.release_engineering.factory_provisioning import FactoryProvisioningStation  # noqa: E402
from gunnchos_device_os.release_engineering.os_image_builder import RealmImageBuilder  # noqa: E402
from gunnchos_device_os.release_engineering.sdk import compat  # noqa: E402
from gunnchos_device_os.release_engineering.sdk.installer import PackageInstaller  # noqa: E402
from gunnchos_device_os.release_engineering.sdk.manifest import new_manifest  # noqa: E402
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder  # noqa: E402
from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner  # noqa: E402
from gunnchos_device_os.release_engineering import serviceability as svc  # noqa: E402


def run_pytest_suite() -> dict:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/wp013", "-q"],
        cwd=str(ROOT),
        env={"PYTHONPATH": f"{ROOT}:{ROOT / 'src'}"},
        capture_output=True,
        text=True,
        timeout=600,
    )
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "tail": "\n".join((proc.stdout or "").splitlines()[-20:]),
    }


def check_image_realms() -> dict:
    return image_realms.validate_all(ROOT)


def check_os_image_builds() -> dict:
    builder = RealmImageBuilder(ROOT)
    out = {}
    for alias in ("lab", "evt", "factory", "recovery", "production"):
        build_result = builder.build(alias, unsigned=False)
        verify_result = builder.verify(alias)
        # Prefer on-disk manifest fields over the in-memory return so RESULT
        # cannot claim signed=true when a later step rewrote the artifact.
        disk = builder.inspect(alias).get("manifest") or {}
        out[alias] = {
            "build_ok": build_result.get("ok", False),
            "verify_ok": verify_result.get("ok", False),
            "verify_failures": verify_result.get("failures", []),
            "signed": bool(disk.get("signed", build_result.get("signed"))),
            "PRODUCTION_RELEASE_CLAIMED": bool(
                disk.get("PRODUCTION_RELEASE_CLAIMED", build_result.get("PRODUCTION_RELEASE_CLAIMED"))
            ),
            "rootfs_file_count": ((disk.get("artifacts") or {}).get("rootfs_tarball") or {}).get("file_count"),
            "claim_boundary": disk.get("claim_boundary"),
        }
    return out


def check_sdk_pipeline() -> dict:
    # Stubs may remain as tutorials under sdk/examples — they are NOT adoption proof.
    real_apps = [
        ("creator_studio", ROOT / "sdk" / "apps" / "creator_studio"),
        ("waike_learning", ROOT / "sdk" / "apps" / "waike_learning"),
        ("gunnchai_tutor", ROOT / "sdk" / "apps" / "gunnchai_tutor"),
        ("pedestrian_pursuit_ref", ROOT / "sdk" / "apps" / "pedestrian_pursuit_ref"),
    ]
    with tempfile.TemporaryDirectory(prefix="wp013_sdk_") as tmp:
        tmp_path = Path(tmp)
        builder = PackageBuilder(ROOT)
        installer = PackageInstaller(ROOT, tmp_path / "install")
        runner = PackageRunner(tmp_path / "install", repo_root=ROOT)
        results = {}
        for name, app_dir in real_apps:
            build_result = builder.build(app_dir, tmp_path / "pkgs")
            install_result = installer.install(Path(build_result["package_path"]))
            run_result = runner.run(install_result["app_id"]) if install_result.get("ok") else {"ok": False}
            results[name] = {
                "build_ok": build_result.get("ok", False),
                "install_ok": install_result.get("ok", False),
                "run_ok": run_result.get("ok", False),
                "exit_code": run_result.get("exit_code"),
                "stub_content": False,
                "app_dir": str(app_dir.relative_to(ROOT)),
            }
        results["FIRST_PARTY_SDK_ADOPTION_PASS"] = all(
            bool(results[n].get("build_ok") and results[n].get("install_ok") and results[n].get("run_ok"))
            for n, _ in real_apps
        )
        results["stubs_retained_as_tutorials_only"] = True
        return results


def check_api_compat_gate() -> dict:
    accept = new_manifest(app_id="gunnchos.gate_accept", name="x", capabilities_required=["ring.read"])
    reject_os = new_manifest(app_id="gunnchos.gate_reject_os", name="x", min_os_version="9.9.9")
    reject_cap = new_manifest(app_id="gunnchos.gate_reject_cap", name="x", capabilities_required=["legacy.raw_socket"])

    accept_result = compat.check_compatibility(accept)
    reject_os_result = compat.check_compatibility(reject_os)
    reject_cap_result = compat.check_compatibility(reject_cap)

    ok = accept_result["ok"] is True and reject_os_result["ok"] is False and reject_cap_result["ok"] is False
    return {
        "ok": ok,
        "accept_case_ok": accept_result["ok"],
        "reject_os_case_rejected": not reject_os_result["ok"],
        "reject_capability_case_rejected": not reject_cap_result["ok"],
    }


def check_ab_update() -> dict:
    with tempfile.TemporaryDirectory(prefix="wp013_ab_") as tmp:
        mgr = ABUpdateManager(ROOT, Path(tmp) / "state.json")
        mgr.init_device("wp013-verify-device")
        meta = build_update_metadata(
            ROOT, realm_id="EVT_ENGINEERING_IMAGE", from_version="1.0.0", to_version="1.1.0",
            image_hash="deadbeef", anti_rollback_counter=1,
        )
        stage = mgr.stage_update(meta)
        boot = mgr.commit_boot("B", boot_succeeds=True)
        rollback = mgr.manual_rollback()
        crash = mgr.stage_update(meta, simulate_crash_before_commit=True)
        recovery = mgr.recover_from_interrupted_update()
        return {
            "ok": all([stage.get("ok"), boot.get("ok"), rollback.get("ok"), recovery.get("ok")]),
            "stage_ok": stage.get("ok"),
            "boot_ok": boot.get("ok"),
            "rollback_ok": rollback.get("ok"),
            "interrupted_update_recovered": recovery.get("recovered_slots") == ["B"],
        }


def check_factory_provisioning() -> dict:
    with tempfile.TemporaryDirectory(prefix="wp013_factory_") as tmp:
        station = FactoryProvisioningStation(ROOT, Path(tmp) / "factory_store.json")
        provision = station.provision_new_device()
        device_id = provision["device_id"]
        cal = station.import_calibration(
            device_id,
            {
                "device_id": device_id,
                "test_station_id": "STATION-1",
                "measurements": {"battery_v": 4.2},
                "result": "PASS",
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
        builder = RealmImageBuilder(ROOT)
        builder.build("factory", unsigned=False)
        manifest = builder.inspect("factory")["manifest"]
        flash = station.flash(device_id, manifest)
        verify = station.post_flash_verify(device_id)
        export = station.export_device_record(device_id)
        repair = station.record_repair_event(device_id, component="battery", technician_id="tech-1", reason="test")
        rework = station.wipe_and_rework(device_id, reason="wp013_verification")
        ok = all(
            r.get("ok")
            for r in (provision, cal, flash, verify, export, repair, rework)
        )
        return {
            "ok": ok,
            "provision_ok": provision.get("ok"),
            "calibration_ok": cal.get("ok"),
            "flash_ok": flash.get("ok"),
            "post_flash_verify_ok": verify.get("ok"),
            "export_ok": export.get("ok"),
            "repair_log_ok": repair.get("ok"),
            "wipe_and_rework_ok": rework.get("ok"),
        }


def check_recovery_serviceability() -> dict:
    with tempfile.TemporaryDirectory(prefix="wp013_svc_") as tmp:
        tmp_path = Path(tmp)
        device_root = tmp_path / "device"
        (device_root / "logs").mkdir(parents=True)
        (device_root / "logs" / "app.log").write_text("user a@b.com token=SECRET123\n", encoding="utf-8")
        (device_root / "user_data.json").write_text(json.dumps({"accounts": ["owner"]}), encoding="utf-8")
        (device_root / "identity.json").write_text(json.dumps({"device_id": "svc-dev-1"}), encoding="utf-8")

        diag = svc.export_diagnostic_bundle(device_root, tmp_path / "bundle.tar.gz")
        backup = svc.backup_user_data(ROOT, device_root, tmp_path / "backup.json")
        new_root = tmp_path / "new_device"
        restore = svc.restore_user_data(ROOT, tmp_path / "backup.json", new_root)
        transfer = svc.transfer_device_replacement(ROOT, device_root, tmp_path / "replacement_device", transfer_reason="verify")
        migration = svc.migrate_user_data({"accounts": ["owner"]})
        svc.enter_repair_mode(new_root, reason="verify")
        repair_active = svc.is_in_repair_mode(new_root)
        svc.exit_repair_mode(new_root)
        wipe = svc.secure_wipe(new_root)

        ok = all(
            [
                diag.get("ok"), diag.get("any_redaction_applied"),
                backup.get("ok"), restore.get("ok"), transfer.get("ok"),
                migration.get("schema") == svc.USER_DATA_SCHEMA_V2,
                repair_active, wipe.get("ok"),
            ]
        )
        return {
            "ok": ok,
            "diagnostic_bundle_ok": diag.get("ok"),
            "redaction_applied": diag.get("any_redaction_applied"),
            "backup_restore_ok": backup.get("ok") and restore.get("ok"),
            "transfer_ok": transfer.get("ok"),
            "migration_ok": migration.get("schema") == svc.USER_DATA_SCHEMA_V2,
            "repair_mode_ok": repair_active,
            "secure_wipe_ok": wipe.get("ok"),
        }



def check_realm_runtime() -> dict:
    """Behaviorally verify EVT/FACTORY/RECOVERY realm artifacts under QEMU.

    Rootfs-tarball presence alone never earns RUNTIME_PASS. Tokens flip true
    only when ``realm_runtime.verify_all_realm_runtimes`` boots each artifact
    and serial evidence shows realm identity + executed probe markers.
    """
    from gunnchos_device_os.release_engineering.realm_runtime import (
        verify_all_realm_runtimes,
    )

    timeout = float(os.environ.get("WP013_REALM_RUNTIME_TIMEOUT_SEC", "90"))
    return verify_all_realm_runtimes(ROOT, timeout_sec=timeout)

def main() -> int:
    result: dict = {
        "schema": "gunnchos.wp013.result.v1",
        "work_package": "WP-013",
        "title": "gunnchOS Release Engineering + Developer Platform",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "evidence": {},
        "exit_tokens": {},
    }

    # Pytest first: some wp013 tests rebuild EVT/FACTORY with unsigned=True into
    # os_build/realm_images/. Live checks below must run afterward so RESULT and
    # on-disk manifests agree on signed=true for DEV-signed realms.
    pytest_result = run_pytest_suite()
    result["evidence"]["pytest_tests_wp013"] = pytest_result

    realms = check_image_realms()
    result["evidence"]["image_realms"] = realms

    sdk_pipeline = check_sdk_pipeline()
    result["evidence"]["sdk_pipeline"] = sdk_pipeline

    api_gate = check_api_compat_gate()
    result["evidence"]["api_compatibility_gate"] = api_gate

    ab_update = check_ab_update()
    result["evidence"]["ab_update"] = ab_update

    factory = check_factory_provisioning()
    result["evidence"]["factory_provisioning"] = factory

    recovery_svc = check_recovery_serviceability()
    result["evidence"]["recovery_serviceability"] = recovery_svc

    realm_runtime = check_realm_runtime()
    result["evidence"]["realm_runtime"] = realm_runtime

    # Image builds last so committed realm artifacts match RESULT signed claims.
    os_image_builds = check_os_image_builds()
    result["evidence"]["os_image_builds"] = os_image_builds

    all_tests_green = pytest_result["ok"]

    result["exit_tokens"] = {
        "IMAGE_REALMS_DIGITALLY_COMPLETE": bool(realms.get("IMAGE_REALMS_DIGITALLY_COMPLETE")) and all_tests_green,
        "EVT_IMAGE_BUILD_PASS": bool(
            os_image_builds["evt"]["build_ok"] and os_image_builds["evt"]["verify_ok"]
        )
        and all_tests_green,
        "FACTORY_IMAGE_BUILD_PASS": bool(
            os_image_builds["factory"]["build_ok"] and os_image_builds["factory"]["verify_ok"]
        )
        and all_tests_green,
        "RECOVERY_IMAGE_BUILD_PASS": bool(
            os_image_builds["recovery"]["build_ok"] and os_image_builds["recovery"]["verify_ok"]
        )
        and all_tests_green,
        "PRODUCTION_IMAGE_DEFINITION_COMPLETE": bool(
            os_image_builds["production"]["build_ok"]
            and os_image_builds["production"]["verify_ok"]
            and os_image_builds["production"]["signed"] is False
            and os_image_builds["production"]["PRODUCTION_RELEASE_CLAIMED"] is False
        )
        and all_tests_green,
        "SDK_PACKAGE_INSTALL_RUN_PASS": bool(
            all(
                isinstance(v, dict) and v.get("build_ok") and v.get("install_ok") and v.get("run_ok")
                for k, v in sdk_pipeline.items()
                if k not in ("FIRST_PARTY_SDK_ADOPTION_PASS", "stubs_retained_as_tutorials_only")
            )
        )
        and all_tests_green,
        "FIRST_PARTY_SDK_ADOPTION_PASS": bool(sdk_pipeline.get("FIRST_PARTY_SDK_ADOPTION_PASS"))
        and all_tests_green,
        "API_COMPATIBILITY_GATE_PASS": bool(api_gate["ok"]) and all_tests_green,
        "FACTORY_PROVISIONING_DIGITAL_PASS": bool(factory["ok"]) and all_tests_green,
        "RECOVERY_SERVICEABILITY_DIGITAL_PASS": bool(recovery_svc["ok"]) and all_tests_green,
        "EVT_IMAGE_RUNTIME_PASS": bool(realm_runtime.get("EVT_IMAGE_RUNTIME_PASS")) and all_tests_green,
        "FACTORY_IMAGE_RUNTIME_PASS": bool(realm_runtime.get("FACTORY_IMAGE_RUNTIME_PASS")) and all_tests_green,
        "RECOVERY_IMAGE_RUNTIME_PASS": bool(realm_runtime.get("RECOVERY_IMAGE_RUNTIME_PASS")) and all_tests_green,
        "IMAGE_REALM_POLICY_SEPARATION_PASS": bool(realm_runtime.get("IMAGE_REALM_POLICY_SEPARATION_PASS")) and all_tests_green,
    }
    result["PRODUCTION_RELEASE_CLAIMED"] = False
    result["claim_boundary"] = (
        "All exit tokens require both a passing live evidence run in this "
        "script AND a green `tests/wp013` pytest run in the same invocation. "
        "Realm 'image builds' are deterministic digital rootfs-tarball + "
        "manifest/SBOM/DEV-sign artifacts (not physical disk images / not "
        "bootable shipping builds). No production image is built, signed, or "
        "released by this work package; PRODUCTION_SHIPPING_IMAGE_DEFINITION "
        "always stays unsigned/NOT_RELEASED."
    )

    out_dir = ROOT / "artifacts" / "wp013"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "WP-013-RESULT.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps(result["exit_tokens"], indent=2))
    print(f"Wrote {out_path}")
    return 0 if all_tests_green else 1


if __name__ == "__main__":
    raise SystemExit(main())
