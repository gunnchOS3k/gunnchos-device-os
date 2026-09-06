"""Learning OS thin-launcher / companion integration (Gate C / C-OWNER-02)."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.app_registry import (
    LEARNING_OS_BUNDLE_ID,
    LEARNING_OS_REGISTRY_ID,
    get_app,
    list_apps,
    resolve_app_id,
)
from gunnchos_device_os.learning_os_launcher import (
    continuity_handoff,
    invoke_updater_contract,
    ipc_handshake,
    launch_learning_os,
    map_permissions_for_platform_role,
    parse_deep_link,
    resolve_learning_os_target,
)
from gunnchos_device_os.permissions_manager import Permission, PermissionsManager
from gunnchos_device_os.policy_engine import evaluate


def test_registry_lookup_learning_os_canonical():
    assert LEARNING_OS_REGISTRY_ID in list_apps("education")
    app = get_app(LEARNING_OS_REGISTRY_ID)
    assert app["bundle_id"] == LEARNING_OS_BUNDLE_ID
    assert app["relationship"] == "thin_launcher_companion"
    assert app["system_of_record"] == "platform_tauri_learning_os"
    assert resolve_app_id("waike_offline") == LEARNING_OS_REGISTRY_ID
    aliased = get_app("waike_offline", resolve_alias=True)
    assert aliased["app_id"] == LEARNING_OS_REGISTRY_ID
    assert aliased["resolved_from_alias"] is True


def test_policy_allows_canonical_via_alias_allowlist():
    # modes.yaml still lists waike_offline; canonical id must resolve as allowed.
    assert evaluate("student", "School", LEARNING_OS_REGISTRY_ID)["allowed"] is True
    assert evaluate("student", "School", "waike_offline")["allowed"] is True


def test_launcher_returns_thin_launcher_handoff_not_seed_sor():
    result = launch_learning_os("student", "School", deep_link="waike://learn/home")
    assert result["launched"] is True
    assert result["relationship"] == "thin_launcher_companion"
    assert result["system_of_record"] == "platform_tauri_learning_os"
    assert result["seed_is_system_of_record"] is False
    assert result["handoff"]["bundle_id"] == LEARNING_OS_BUNDLE_ID
    assert result["handoff"]["ipc"]["allow_ipc"] is True
    assert result["companion_seed"] is not None
    assert result["companion_seed"]["is_system_of_record"] is False
    assert result["companion_seed"]["role"] == "discovery_lab_seed_only"
    # Must not claim seed HTML index as SoR
    assert result.get("entry") != "apps/waike_learning/index.html" or result["seed_is_system_of_record"] is False


def test_resolve_and_ipc_handshake():
    target = resolve_learning_os_target("waike_offline")
    assert target["registry_id"] == LEARNING_OS_REGISTRY_ID
    assert target["bundle_id"] == LEARNING_OS_BUNDLE_ID
    hs = ipc_handshake(profile="student", mode="School", deep_link="waike://section/sec-1")
    assert hs["ok"] is True
    assert hs["protocol"] == "gunnchos.learning_os.ipc.v1"
    assert hs["seed_is_system_of_record"] is False
    bad = parse_deep_link("https://evil.example/x")
    assert bad["valid"] is False


def test_permissions_manager_semantics_for_learning_os_roles():
    learner = map_permissions_for_platform_role("learner")
    assert learner["device_os_role"] == "student"
    assert "files_read" in learner["allowlist"]
    assert "ai_cloud_export" not in learner["allowlist"]

    instructor = map_permissions_for_platform_role("instructor")
    assert instructor["device_os_role"] == "educator"
    assert "camera" in instructor["allowlist"]

    pm = PermissionsManager(role="student")
    denied = pm.request(LEARNING_OS_REGISTRY_ID, Permission.AI_CLOUD_EXPORT)
    assert denied["decision"] == "deny"
    allowed = pm.request(LEARNING_OS_REGISTRY_ID, Permission.FILES_READ)
    assert allowed["decision"] == "allow"


def test_continuity_excludes_secrets(tmp_path: Path):
    ok = continuity_handoff(
        from_profile="handheld_hybrid",
        to_profile="student_14_5",
        lesson_progress={"lesson": "w01", "pct": 40},
        storage_root=tmp_path / "ok",
    )
    assert ok["ok"] is True
    assert ok["contains_secrets"] is False
    blob = json.dumps(ok["payload"]).lower()
    assert "password" not in blob
    assert "private_key" not in blob

    bad = continuity_handoff(
        from_profile="a",
        to_profile="b",
        lesson_progress={"password": "nope"},
        storage_root=tmp_path / "bad",
    )
    assert bad["ok"] is False
    assert bad["contains_secrets"] is True
    assert bad["reason"] == "CONTINUITY_SECRET_REJECTED"


def test_updater_check_rollback_contract_invoked():
    update = invoke_updater_contract("0.0.9-evt0")
    assert "device_os_updater" in update
    assert update["device_os_updater"]["update_available"] is True
    assert update["learning_os_updater"]["signing_truth"] == "UNSIGNED_DIGITAL_FIXTURE"
    assert update["rollback"]["success"] is True
    assert update["rollback_supported"] is True
    assert update["update_owner"] == "platform_tauri_bundle"

    handoff = launch_learning_os("student", "School", include_companion_seed=False)
    assert handoff["update_contract"]["invoked"] is True
    assert handoff["update_contract"]["signing_truth"] == "UNSIGNED_DIGITAL_FIXTURE"


def test_sdk_manifest_allows_ipc():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "sdk" / "apps" / "waike_learning" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["sandbox_profile"]["allow_ipc"] is True
    assert manifest["relationship"]["system_of_record"] == "platform_tauri_learning_os"
    assert manifest["relationship"]["platform_tauri_bundle_id"] == LEARNING_OS_BUNDLE_ID
