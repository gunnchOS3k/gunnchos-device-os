"""CLI-level tests for the WP-013 `gunnchctl` subcommands, invoked exactly
like a user would via `scripts/gunnchctl`."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GUNNCHCTL = REPO_ROOT / "scripts" / "gunnchctl"


def _run(*args: str) -> dict:
    proc = subprocess.run(
        [sys.executable, str(GUNNCHCTL), *args],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode in (0, 1), proc.stderr
    return json.loads(proc.stdout)


def test_cli_os_image_build_inspect_verify_lab():
    build = _run("os-image", "build", "lab", "--unsigned")
    assert build["ok"] is True
    inspect = _run("os-image", "inspect", "lab")
    assert inspect["ok"] is True
    verify = _run("os-image", "verify", "lab")
    assert verify["ok"] is True


def test_cli_sdk_init_build_test(tmp_path):
    app_dir = tmp_path / "cli_app"
    init = _run("sdk", "init", "gunnchos.cli_test_app", str(app_dir))
    assert init["ok"] is True

    build = _run("sdk", "build", str(app_dir), "--out", str(tmp_path / "pkgs"))
    assert build["ok"] is True

    test_result = _run("sdk", "test", str(app_dir))
    assert test_result["ok"] is True
    assert test_result["SDK_PACKAGE_INSTALL_RUN_PASS"] is True


def test_cli_package_install_run_uninstall(tmp_path):
    pkgs_dir = tmp_path / "pkgs"
    install_root = tmp_path / "install"

    pkg = _run("package", str(REPO_ROOT / "sdk" / "examples" / "waike_stub"), "--out", str(pkgs_dir))
    assert pkg["ok"] is True

    install = _run("install", pkg["package_path"], "--install-root", str(install_root))
    assert install["ok"] is True

    run = _run("run", "gunnchos.waike_stub", "--install-root", str(install_root))
    assert run["ok"] is True
    assert run["exit_code"] == 0

    uninstall = _run("uninstall", "gunnchos.waike_stub", "--install-root", str(install_root))
    assert uninstall["ok"] is True


def test_cli_run_still_requires_device_lab_session_when_device_flag_given():
    # We don't actually spin up a QEMU session in this fast unit test; we
    # only assert that the CLI still routes to the Device Lab path (it will
    # try to start a session and fail fast without a real profile file, but
    # it must NOT be treated as an SDK package run).
    proc = subprocess.run(
        [sys.executable, str(GUNNCHCTL), "run", "some_app", "--device", "not_a_real_profile"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=30,
    )
    combined = (proc.stdout or "") + (proc.stderr or "")
    assert "no_apps_installed" not in combined
