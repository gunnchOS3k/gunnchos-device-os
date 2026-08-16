"""STREAM-A-PKT-002 tests — templates, middleware resilience, host-chain honesty."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.creation_enablement.guest_dogfood import run_in_guest
from gunnchos_device_os.creation_enablement.host_chain import run_host_creator_chain
from gunnchos_device_os.creation_enablement.templates import TEMPLATE_SPECS, run_template_suite
from gunnchos_device_os.middleware.resilience import FAULTS, run_fault_injection, write_artifacts

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_template_suite_eight_kinds(tmp_path, monkeypatch):
    # Isolate artifacts under tmp via chdir? suite writes under repo artifacts — ok for CI.
    result = run_template_suite(REPO_ROOT)
    assert result["ok"] is True, result
    assert result["count"] == 8
    assert {s["id"] for s in TEMPLATE_SPECS} == {r["id"] for r in result["templates"]}


def test_middleware_fault_injection_ten_faults():
    report = run_fault_injection()
    assert report["ok"] is True, report
    assert report["pass_count"] == len(FAULTS) == 10
    assert report["SILICON_EXACT_EMULATION"] is False
    paths = write_artifacts(REPO_ROOT)
    assert paths["matrix"].exists()
    assert paths["faults"].exists()


def test_host_chain_still_does_not_earn_e2e(tmp_path):
    result = run_host_creator_chain(REPO_ROOT, tmp_path / "creation_work")
    assert result["ok_host_chain"] is True
    assert result["CREATOR_END_TO_END_DIGITAL_PASS"] is False


def test_guest_dogfood_logic_on_host_sandbox(tmp_path, monkeypatch):
    """Logic self-check on host filesystem — packet earn still requires QEMU evidence."""
    monkeypatch.setenv("GUNNCHOS_CREATOR_E2E_EVIDENCE", str(tmp_path / "e2e"))
    monkeypatch.setenv("GUNNCHOS_CREATOR_E2E_WORK", str(tmp_path / "work"))
    payload = tmp_path / "payload"
    app_src = REPO_ROOT / "sdk" / "apps" / "stream_a_sample_memo"
    apps = payload / "apps" / "stream_a_sample_memo"
    apps.parent.mkdir(parents=True)
    import shutil

    shutil.copytree(app_src, apps)
    result = run_in_guest(payload_root=payload, repo_python_root=REPO_ROOT)
    assert result["tokens"]["CREATOR_GUEST_BUILD_PASS"] is True
    assert result["tokens"]["CREATOR_GUEST_INSTALL_PASS"] is True
    assert result["tokens"]["CREATOR_GUEST_RUN_PASS"] is True
    assert result["tokens"]["CREATOR_GUEST_UPDATE_PASS"] is True
    assert result["tokens"]["CREATOR_GUEST_ROLLBACK_PASS"] is True
    assert result["tokens"]["CREATOR_END_TO_END_DIGITAL_PASS"] is True
    assert (tmp_path / "e2e" / "RESULT.json").exists()