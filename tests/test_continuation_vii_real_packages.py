"""Cont VII — real packages, stub ban, platform digital token."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.app_packaging import PackageManifestBuilder
from gunnchos_device_os.app_runtime import (
    AppRuntime,
    TOKEN_APP_RUNTIME_PASS,
    ensure_beatlink_package,
)
from gunnchos_device_os.carrier_grade_digital import (
    TOKEN as CARRIER_TOKEN,
    evaluate_carrier_grade_digital,
)
from gunnchos_device_os.connectivity.cellular_stack import CellularSoftwareStack
from gunnchos_device_os.cross_repo_cont_vii_hooks import probe_hooks
from gunnchos_device_os.ipc_robustness import TOKEN as IPC_TOKEN, audit_ipc_robustness
from gunnchos_device_os.platform_digital import TOKEN as PLATFORM_TOKEN, evaluate_platform_digital_complete


ROOT = Path(__file__).resolve().parents[1]


def test_beatlink_is_not_stub():
    index = ensure_beatlink_package(ROOT)
    text = index.read_text(encoding="utf-8")
    assert "GUNNCHOS_GAME_STUB_CONTENT=true" not in text
    assert "DEV stub" not in text
    man = (ROOT / "games/beatlink-party-web/PACKAGE_MANIFEST.json")
    assert man.exists()
    data = __import__("json").loads(man.read_text())
    assert data["stub_content"] is False
    assert data["accepted_sha"].startswith("9948646")
    assert data["artifact_tree_sha256"]


def test_first_party_apps_are_real_not_mocks():
    for rel in (
        "apps/waike_learning/index.html",
        "apps/creator_studio/index.html",
        "apps/device_management/index.html",
    ):
        assert (ROOT / rel).exists()
    report = PackageManifestBuilder(root=ROOT).validate()
    assert report["ok"] is True
    dash = next(r for r in report["apps"] if r["id"] == "device_dashboard")
    assert "device_dashboard_mock" not in dash["source_detail"]
    assert "device_management" in dash["source_detail"]


def test_runtime_launches_without_stubs():
    batch = AppRuntime(role="student").launch_category_representatives()
    assert batch["ok"] is True
    assert batch["token"] == TOKEN_APP_RUNTIME_PASS
    assert batch["stub_as_product"] is False
    assert all(not v.get("stub_content") for v in batch["results"]["games"].values())
    assert batch["results"]["coding_creation"]["payload"]["workspace"]["ok"] is True
    assert batch["results"]["management_diagnostics"]["payload"]["diagnostics_surface"]["ok"] is True


def test_ipc_robustness_keeps_unix_socket():
    report = audit_ipc_robustness(run_live=True)
    assert report["ok"] is True
    assert report["decision"] == "KEEP_UNIX_SOCKET_IPC"
    assert report["token"] == IPC_TOKEN
    assert all(report["criteria"].values())


def test_platform_digital_complete_without_physical_blocker():
    plat = evaluate_platform_digital_complete(root=ROOT, quick=False)
    assert plat["non_blockers"]["physical_boot_pending"] == "NOT_A_DIGITAL_BLOCKER"
    assert plat["non_blockers"]["production_cloud_credentials"] == "NOT_A_DIGITAL_BLOCKER"
    assert plat["earned"] is True
    assert plat["token"] == PLATFORM_TOKEN


def test_cellular_stack_and_carrier_grade():
    stack = CellularSoftwareStack()
    attach = stack.enumerate_and_attach()
    assert attach["ok"] is True
    assert attach["ntn_claimed"] is False
    assert attach["physical_attach"] is False
    assert stack.handover_matrix()["ok"] is True
    carrier = evaluate_carrier_grade_digital()
    assert carrier["ok"] is True
    assert carrier["token"] == CARRIER_TOKEN


def test_cross_repo_e2e_hooks_prefer_real_packages():
    report = probe_hooks()
    assert report["stub_as_product"] is False
    assert report["usable_count"] >= 7
    beat = next(h for h in report["hooks"] if h["id"] == "E2E-07")
    assert beat["usable"] is True
    assert report["beatlink_accepted_sha"]
