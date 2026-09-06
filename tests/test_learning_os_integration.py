"""Learning OS thin-launcher / companion integration — D-OWNER closure."""
from __future__ import annotations

import ast
import inspect
import json
import os
import stat
import tempfile
from pathlib import Path

import pytest

from gunnchos_device_os.app_registry import (
    LEARNING_OS_BUNDLE_ID,
    LEARNING_OS_REGISTRY_ID,
    get_app,
    list_apps,
    resolve_app_id,
)
from gunnchos_device_os import launcher as launcher_mod
from gunnchos_device_os.launcher import launch_app, list_launchable
from gunnchos_device_os.learning_os.ipc_protocol import PROTOCOL_ID, build_launch_request
from gunnchos_device_os.learning_os.ipc_transport import (
    DeterministicTestTransport,
    FileIpcTransport,
)
from gunnchos_device_os.learning_os.native_launch import NativeLaunchAdapter
from gunnchos_device_os.learning_os.package_lifecycle import LearningOsPackageLifecycle
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

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "learning_os" / "waike-learning-os"


@pytest.fixture
def installed_learning_os(tmp_path: Path):
    root = tmp_path / "install"
    bin_dir = root / "bin"
    bin_dir.mkdir(parents=True)
    dest = bin_dir / "waike-learning-os"
    dest.write_bytes(FIXTURE.read_bytes())
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    (bin_dir / "VERSION").write_text("0.1.0-fixture\n", encoding="utf-8")
    return root


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
    assert evaluate("student", "School", LEARNING_OS_REGISTRY_ID)["allowed"] is True
    assert evaluate("student", "School", "waike_offline")["allowed"] is True


def test_launch_absent_native_fails_closed():
    result = launch_learning_os(
        "student",
        "School",
        deep_link="waike://learn/home",
        include_companion_seed=False,
        install_root=Path(tempfile.mkdtemp(prefix="los-missing-")),
    )
    assert result["registered"] is True
    assert result["available"] is False
    assert result["launched"] is False
    assert result["reason"] == "learning_os_not_installed"
    assert result["seed_is_system_of_record"] is False
    assert result["relationship"] == "thin_launcher_companion"


def test_launch_native_fixture_process_and_ack(installed_learning_os: Path):
    adapter = NativeLaunchAdapter(install_root=installed_learning_os, timeout_s=5.0)
    result = launch_learning_os(
        "student",
        "School",
        deep_link="waike://learn/home",
        include_companion_seed=True,
        adapter=adapter,
    )
    assert result["available"] is True
    assert result["launch_attempted"] is True
    assert result["process_started"] is True
    assert result["deep_link_delivered"] is True
    assert result["acknowledged"] is True
    assert result["launched"] is True
    assert result["companion_seed"]["is_system_of_record"] is False
    assert result["provenance"]["contract_version"]
    assert result["provenance"]["gate_c_logical_version"] == "0.6.0-gate-c"
    assert result["handoff"]["bundle_id"] == LEARNING_OS_BUNDLE_ID


def test_launch_timeout_fails(installed_learning_os: Path):
    adapter = NativeLaunchAdapter(
        install_root=installed_learning_os,
        transport=DeterministicTestTransport(fail_reason="timeout"),
        timeout_s=0.1,
    )
    # Still starts process; transport reports timeout → launched False
    result = launch_learning_os(
        "student",
        "School",
        include_companion_seed=False,
        adapter=adapter,
    )
    assert result["process_started"] is True
    assert result["launched"] is False
    assert result["reason"] == "timeout"


def test_ipc_transport_round_trip_and_faults(tmp_path: Path):
    ok_tx = DeterministicTestTransport(app_version="1.2.3")
    req = build_launch_request(
        request_id="r1",
        deep_link={"uri": "waike://learn/home", "valid": True, "kind": "learn", "path": "home"},
        context={"profile": "student", "mode": "School", "bundle_id": LEARNING_OS_BUNDLE_ID},
        bundle_id=LEARNING_OS_BUNDLE_ID,
    )
    got = ok_tx.send_and_await_ack(req)
    assert got["ok"] is True
    assert got["ack"]["app_version"] == "1.2.3"
    replay = ok_tx.send_and_await_ack(req)
    assert replay["replay"] is True

    bad = ok_tx.send_and_await_ack({**req, "protocol": "wrong"})
    assert bad["ok"] is False
    assert bad["reason"] == "wrong_protocol_version"

    missing = DeterministicTestTransport(fail_reason="missing_receiver")
    assert missing.send_and_await_ack({**req, "request_id": "r2"})["reason"] == "missing_receiver"

    # File transport with fixture writing ack
    ipc = tmp_path / "ipc"
    file_tx = FileIpcTransport(ipc, receiver_present=True)
    rid = "file-1"
    req2 = {**req, "request_id": rid}
    # Simulate receiver
    (ipc / f"ack-{rid}.json").write_text(
        json.dumps(
            {
                "protocol": PROTOCOL_ID,
                "message_type": "ack",
                "request_id": rid,
                "status": "ok",
                "bundle_id": LEARNING_OS_BUNDLE_ID,
                "app_version": "0.1.0-fixture",
            }
        )
        + "\n"
    )
    # Pre-write ack before send (receiver already responded) — send writes request then sees ack
    assert file_tx.send_and_await_ack(req2, timeout_s=1.0)["ok"] is True

    hs = ipc_handshake(profile="student", mode="School", deep_link="waike://section/sec-1", deliver=True)
    assert hs["ok"] is True
    assert hs["protocol"] == PROTOCOL_ID
    assert hs["transport_result"]["ok"] is True


def test_deep_link_normalization_rejects_traversal():
    assert parse_deep_link("waike://learn/home")["valid"] is True
    assert parse_deep_link("waike://learn/home")["canonical"] == "waike://learn/home"
    for bad in (
        "waike://learn/%2e%2e/etc",
        "waike://learn/%2E%2E/secret",
        "waike://learn/%252e%252e/x",
        "waike://learn/%5cwindows",
        "waike://learn/..%2f..",
        "waike://learn/foo%00bar",
        "https://evil.example/x",
        "waike://learn/foo\\bar",
    ):
        parsed = parse_deep_link(bad)
        assert parsed["valid"] is False, bad


def test_list_launchable_single_impl_and_canonical():
    src = Path(inspect.getsourcefile(launcher_mod)).read_text(encoding="utf-8")
    tree = ast.parse(src)
    defs = [
        n
        for n in tree.body
        if isinstance(n, ast.FunctionDef) and n.name == "list_launchable"
    ]
    assert len(defs) == 1
    apps = list_launchable("student", "School")
    by_id = {a["app"]: a for a in apps}
    assert by_id[LEARNING_OS_REGISTRY_ID]["canonical"] == LEARNING_OS_REGISTRY_ID
    assert by_id["waike_offline"]["canonical"] == LEARNING_OS_REGISTRY_ID
    # Alias does not create a second product identity at resolve time
    assert resolve_app_id("waike_offline") == LEARNING_OS_REGISTRY_ID


def test_launch_via_alias_same_native_target(installed_learning_os: Path):
    os.environ["LEARNING_OS_INSTALL_ROOT"] = str(installed_learning_os)
    try:
        r = launch_app("student", "School", "waike_offline")
        assert r["app"] == LEARNING_OS_REGISTRY_ID or r.get("handoff", {}).get("registry_id") == LEARNING_OS_REGISTRY_ID
        assert r["system_of_record"] == "platform_tauri_learning_os"
        assert r["seed_is_system_of_record"] is False
        # With install root set, native launch should succeed
        assert r["launched"] is True
    finally:
        os.environ.pop("LEARNING_OS_INSTALL_ROOT", None)


def test_permissions_and_grader_mapping():
    learner = map_permissions_for_platform_role("learner")
    assert learner["device_os_role"] == "student"
    assert "files_read" in learner["allowlist"]
    assert "ai_cloud_export" not in learner["allowlist"]

    grader = map_permissions_for_platform_role("grader")
    assert grader["device_os_role"] == "grader"
    assert "camera" not in grader["allowlist"]
    assert "files_write" not in grader["allowlist"]
    assert "files_read" in grader["allowlist"]

    instructor = map_permissions_for_platform_role("instructor")
    assert instructor["device_os_role"] == "educator"
    assert "camera" in instructor["allowlist"]

    admin = map_permissions_for_platform_role("site_admin")
    assert admin["device_os_role"] == "admin"

    guardian = map_permissions_for_platform_role("guardian")
    assert guardian["device_os_role"] == "guardian"

    pm = PermissionsManager(role="grader")
    denied = pm.request(LEARNING_OS_REGISTRY_ID, Permission.CAMERA)
    assert denied["decision"] == "deny"
    allowed = pm.request(LEARNING_OS_REGISTRY_ID, Permission.FILES_READ)
    assert allowed["decision"] == "allow"


def test_continuity_allowlist_and_secret_sabotage(tmp_path: Path):
    ok = continuity_handoff(
        from_profile="handheld_hybrid",
        to_profile="student_14_5",
        lesson_progress={"lesson_id": "w01", "pct": 40, "evil_extra": "drop-me"},
        storage_root=tmp_path / "ok",
    )
    assert ok["ok"] is True
    assert ok["contains_secrets"] is False
    assert "evil_extra" in ok["dropped_fields"]
    assert "pct" in ok["included_fields"] or any("pct" in f for f in ok["included_fields"])
    blob = json.dumps(ok["payload"]).lower()
    assert "password" not in blob
    assert "drop-me" not in blob

    cases = [
        {"password": "nope"},
        {"auth": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig"},
        {"context": {"jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.sig"}},
        {"metadata": {"note": "sk_live_abcdefghijklmnop"}},
        {"checkpoint_label": "-----BEGIN PRIVATE KEY-----\nABC\n-----END PRIVATE KEY-----"},
        {"answer_key": "A,B,C"},
    ]
    for i, progress in enumerate(cases):
        bad = continuity_handoff(
            from_profile="a",
            to_profile="b",
            lesson_progress=progress,
            storage_root=tmp_path / f"bad-{i}",
        )
        assert bad["ok"] is False, progress
        assert bad["contains_secrets"] is True
        assert bad["reason"] == "CONTINUITY_SECRET_REJECTED"
        # Receipt must not leak stripped values
        assert "nope" not in json.dumps(bad)
        assert "sk_live" not in json.dumps(bad)


def test_updater_package_lifecycle_ab_rollback(tmp_path: Path):
    life = LearningOsPackageLifecycle(tmp_path / "pkg")
    proof = life.run_ab_proof(fixture=FIXTURE)
    assert proof["ok"] is True
    assert proof["userdata_preserved"] is True
    assert proof["final_version"] == "1.0.0"
    assert "Not OS-level OTA" in proof["claim_boundary"]

    # Without prior version, rollback_supported is false (not mock true)
    empty = invoke_updater_contract("0.0.9-evt0", package_root=tmp_path / "empty")
    assert empty["rollback_supported"] is False
    assert empty["rollback"]["mock"] is False
    assert empty["signing_truth"] == "UNSIGNED_DIGITAL_FIXTURE"

    # After A→B, rollback supported
    life2 = LearningOsPackageLifecycle(tmp_path / "pkg2")
    life2.publish_and_install("1.0.0", executable_source=FIXTURE)
    life2.update("1.1.0", executable_source=FIXTURE)
    status = invoke_updater_contract("1.1.0", package_root=tmp_path / "pkg2")
    assert status["rollback_supported"] is True
    rb = life2.rollback()
    assert rb["success"] is True
    assert rb["mock"] is False
    assert rb["userdata_preserved"] is True or rb.get("userdata_after") == rb.get("userdata_before")


def test_sdk_manifest_allows_ipc():
    root = Path(__file__).resolve().parents[1]
    manifest = json.loads(
        (root / "sdk" / "apps" / "waike_learning" / "manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["sandbox_profile"]["allow_ipc"] is True
    assert manifest["relationship"]["system_of_record"] == "platform_tauri_learning_os"
    assert manifest["relationship"]["platform_tauri_bundle_id"] == LEARNING_OS_BUNDLE_ID


def test_resolve_target():
    target = resolve_learning_os_target("waike_offline")
    assert target["registry_id"] == LEARNING_OS_REGISTRY_ID
    assert target["bundle_id"] == LEARNING_OS_BUNDLE_ID
