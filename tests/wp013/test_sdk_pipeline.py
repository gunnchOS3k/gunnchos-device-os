"""Real package/install/run pipeline tests for gunnchSDK, plus the API
compatibility gate."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.sdk import compat
from gunnchos_device_os.release_engineering.sdk.installer import InstallError, PackageInstaller
from gunnchos_device_os.release_engineering.sdk.manifest import new_manifest, validate_manifest
from gunnchos_device_os.release_engineering.sdk.packager import PackageBuilder, PackageError
from gunnchos_device_os.release_engineering.sdk.runner import PackageRunner

REPO_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = REPO_ROOT / "sdk" / "examples"
REAL_APPS = REPO_ROOT / "sdk" / "apps"


@pytest.fixture()
def rig(tmp_path):
    out_dir = tmp_path / "pkgs"
    install_root = tmp_path / "install"
    return {
        "builder": PackageBuilder(REPO_ROOT),
        "installer": PackageInstaller(REPO_ROOT, install_root),
        "runner": PackageRunner(install_root, repo_root=REPO_ROOT),
        "out_dir": out_dir,
    }


@pytest.mark.parametrize(
    "app_name",
    ["creator_studio", "waike_learning", "gunnchai_tutor"],
)
def test_first_party_real_app_full_pipeline(rig, app_name):
    """FIRST_PARTY_SDK_ADOPTION evidence — real apps, not sdk/examples stubs.

    Pedestrian Pursuit is covered by FIRST_PARTY_GAME_SDK_ADOPTION_PASS (Godot
    export-pack runtime), not a Python PACKAGE_MANIFEST wrapper.
    """
    build_result = rig["builder"].build(REAL_APPS / app_name, rig["out_dir"])
    assert build_result["ok"] is True
    assert build_result["signed"] is True

    pkg_path = Path(build_result["package_path"])
    assert pkg_path.exists()

    install_result = rig["installer"].install(pkg_path)
    assert install_result["ok"] is True
    assert install_result["action"] == "installed"

    run_result = rig["runner"].run(install_result["app_id"])
    assert run_result["ok"] is True
    assert run_result["exit_code"] == 0
    assert Path(run_result["log_path"]).exists()
    assert run_result["crash_report_path"] is None

    registry = rig["installer"].list_installed()
    assert install_result["app_id"] in registry["apps"]


def test_pedestrian_pursuit_python_wrapper_is_not_adoption_proof():
    """Guardrail: the old manifest-check wrapper must not be treated as the game."""
    wrapper = REAL_APPS / "pedestrian_pursuit_ref"
    assert not wrapper.exists(), "python wrapper pedestrian_pursuit_ref must be removed"
    harness = REAL_APPS / "pedestrian_pursuit" / "tools" / "gunnchos_sdk_adoption_harness.gd"
    assert harness.exists()


@pytest.mark.parametrize("app_name", ["creator_stub", "waike_stub", "gunnchai_client_stub"])
def test_tutorial_stub_pipeline_still_works(rig, app_name):
    """Stubs remain valid tutorials — not adoption proof."""
    build_result = rig["builder"].build(EXAMPLES / app_name, rig["out_dir"])
    assert build_result["ok"] is True
    install_result = rig["installer"].install(Path(build_result["package_path"]))
    assert install_result["ok"] is True
    run_result = rig["runner"].run(install_result["app_id"])
    assert run_result["ok"] is True


def test_tampered_package_rejected(rig):
    build_result = rig["builder"].build(EXAMPLES / "creator_stub", rig["out_dir"])
    pkg_path = Path(build_result["package_path"])

    # Corrupt one payload byte in place while keeping the zip structurally valid.
    import zipfile

    with zipfile.ZipFile(pkg_path, "a") as zf:
        names = [n for n in zf.namelist() if n.startswith("payload/") and n.endswith(".py")]
    assert names
    tmp_extract = pkg_path.parent / "tamper_extract"
    with zipfile.ZipFile(pkg_path, "r") as zf:
        zf.extractall(tmp_extract)
    target = tmp_extract / names[0]
    target.write_text(target.read_text() + "\n# tampered\n")

    import zipfile as zf_mod

    new_pkg = pkg_path.parent / "tampered.gunnchpkg"
    with zf_mod.ZipFile(pkg_path, "r") as src, zf_mod.ZipFile(new_pkg, "w") as dst:
        for item in src.infolist():
            if item.filename == names[0]:
                dst.writestr(item, target.read_bytes())
            else:
                dst.writestr(item, src.read(item.filename))

    with pytest.raises(InstallError):
        rig["installer"].install(new_pkg)


def test_uninstall_removes_registry_entry(rig):
    build_result = rig["builder"].build(EXAMPLES / "waike_stub", rig["out_dir"])
    pkg_path = Path(build_result["package_path"])
    install_result = rig["installer"].install(pkg_path)
    app_id = install_result["app_id"]

    result = rig["installer"].uninstall(app_id)
    assert result["ok"] is True
    assert app_id not in rig["installer"].list_installed()["apps"]


def test_update_bumps_version_and_tracks_previous(rig):
    app_dir = rig["out_dir"].parent / "versioned_app"
    manifest = new_manifest(app_id="gunnchos.versioned_stub", name="Versioned", version="0.1.0")
    app_dir.mkdir(parents=True, exist_ok=True)
    (app_dir / "manifest.json").write_text(json.dumps(manifest))
    (app_dir / "main.py").write_text("print('ok')\n")

    v1 = rig["builder"].build(app_dir, rig["out_dir"])
    rig["installer"].install(Path(v1["package_path"]))

    manifest["version"] = "0.2.0"
    (app_dir / "manifest.json").write_text(json.dumps(manifest))
    v2 = rig["builder"].build(app_dir, rig["out_dir"])
    update_result = rig["installer"].update(Path(v2["package_path"]))
    assert update_result["ok"] is True
    assert update_result["action"] == "updated"
    assert update_result["previous_version"] == "0.1.0"

    registry_entry = rig["installer"].list_installed()["apps"]["gunnchos.versioned_stub"]
    assert registry_entry["version"] == "0.2.0"
    assert registry_entry["previous_version"] == "0.1.0"


def test_package_builder_rejects_invalid_manifest(rig, tmp_path):
    app_dir = tmp_path / "bad_app"
    app_dir.mkdir()
    (app_dir / "manifest.json").write_text(json.dumps({"schema": "wrong"}))
    (app_dir / "main.py").write_text("print('x')\n")
    with pytest.raises(PackageError):
        rig["builder"].build(app_dir, rig["out_dir"])


def test_run_of_uninstalled_app_fails_cleanly(rig):
    result = rig["runner"].run("does.not.exist")
    assert result["ok"] is False
    assert result["error"] == "no_apps_installed"


# ---------------------------------------------------------------------
# API compatibility gate
# ---------------------------------------------------------------------

def test_compat_gate_accepts_compatible_manifest():
    manifest = new_manifest(
        app_id="gunnchos.compat_ok",
        name="Compat OK",
        min_os_version="0.1.0",
        api_version="1.0.0",
        capabilities_required=["ring.read", "display.render"],
    )
    result = compat.check_compatibility(manifest, os_version="0.3.0")
    assert result["ok"] is True
    assert result["failures"] == []


def test_compat_gate_rejects_too_new_min_os_version():
    manifest = new_manifest(app_id="gunnchos.needs_future_os", name="Future", min_os_version="9.9.9")
    result = compat.check_compatibility(manifest, os_version="0.3.0")
    assert result["ok"] is False
    assert any("os_too_old" in f for f in result["failures"])


def test_compat_gate_rejects_api_major_mismatch():
    manifest = new_manifest(app_id="gunnchos.wrong_api", name="Wrong API", api_version="2.0.0")
    result = compat.check_compatibility(manifest, os_version="0.3.0", api_version="1.1.0")
    assert result["ok"] is False
    assert any("api_major_version_mismatch" in f for f in result["failures"])


def test_compat_gate_rejects_removed_capability():
    manifest = new_manifest(
        app_id="gunnchos.uses_removed_cap", name="Removed cap", capabilities_required=["legacy.raw_socket"]
    )
    result = compat.check_compatibility(manifest, os_version="0.3.0")
    assert result["ok"] is False
    assert any("capability_removed" in f for f in result["failures"])


def test_compat_gate_warns_on_deprecated_capability():
    manifest = new_manifest(
        app_id="gunnchos.uses_deprecated_cap",
        name="Deprecated cap",
        capabilities_required=["legacy.input_poll"],
    )
    result = compat.check_compatibility(manifest, os_version="0.3.0")
    assert result["ok"] is True
    assert any("capability_deprecated" in w for w in result["warnings"])


def test_installer_rejects_incompatible_package(rig, tmp_path):
    app_dir = tmp_path / "incompatible_app"
    app_dir.mkdir()
    manifest = new_manifest(
        app_id="gunnchos.incompatible_stub", name="Incompatible", min_os_version="9.9.9"
    )
    (app_dir / "manifest.json").write_text(json.dumps(manifest))
    (app_dir / "main.py").write_text("print('should not run')\n")

    build_result = rig["builder"].build(app_dir, rig["out_dir"])
    result = rig["installer"].install(Path(build_result["package_path"]))
    assert result["ok"] is False
    assert result["error"] == "api_compatibility_gate_rejected"


def test_manifest_validation_catches_bad_permission():
    manifest = new_manifest(app_id="gunnchos.bad_perm", name="Bad", permissions=["not_a_real_permission"])
    failures = validate_manifest(manifest)
    assert "unknown_permission" in failures
