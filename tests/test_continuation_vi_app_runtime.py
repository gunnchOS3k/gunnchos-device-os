"""Cont VI — app runtime through sandbox/permissions."""
from __future__ import annotations

from gunnchos_device_os.app_packaging import PackageManifestBuilder
from gunnchos_device_os.app_runtime import (
    CATEGORY_GAME,
    AppRuntime,
    TOKEN_APP_RUNTIME_PASS,
    ensure_beatlink_package,
)


def test_four_games_and_category_launches(tmp_path):
    ensure_beatlink_package()
    # Refresh packaging manifests including beatlink
    report = PackageManifestBuilder().export()
    assert report["ok"] is True
    assert report["game_manifest"]["count"] >= 4

    runtime = AppRuntime(role="student")
    meta = runtime.package_metadata()
    assert "waike" in meta["categories"]["waike_learning"]
    assert len(meta["categories"][CATEGORY_GAME]) == 4

    batch = runtime.launch_category_representatives()
    assert batch["ok"] is True
    assert batch["token"] == TOKEN_APP_RUNTIME_PASS
    # Cont VII may earn digital platform complete; physical remains separate.
    assert isinstance(batch["full_gunnchos_platform_digital_complete"], bool)
    assert batch["results"]["waike_learning"]["ok"] is True
    assert batch["results"]["coding_creation"]["ok"] is True
    assert batch["results"]["management_diagnostics"]["ok"] is True
    assert all(v["ok"] for v in batch["results"]["games"].values())


def test_permission_rejection_blocks_launch():
    runtime = AppRuntime(role="student")
    denied = runtime.launch("waike", deny_permission="camera")
    assert denied["ok"] is False
    assert denied["permission_rejected"] is True


def test_waike_session_uses_real_packs():
    from gunnchos_device_os.waike_integration import run_session

    session = run_session(profile="student", lesson_id="wireless_basics_101")
    assert session["ok"] is True
    assert session["mock"] is False
    assert session["session"]["offline_pack"] == "wireless_basics_101"
    assert session["content_sources"]
