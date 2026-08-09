"""Continuation VIII — release readiness digital suites."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cont_viii.productivity_stack import build_productivity_stack
from gunnchos_device_os.cont_viii.student_e2e import run_student_e2e
from gunnchos_device_os.cont_viii.office_e2e import run_office_e2e
from gunnchos_device_os.cont_viii.office_file_compat import run_office_file_compat
from gunnchos_device_os.cont_viii.api_abi_policy import evaluate_api_abi_policy
from gunnchos_device_os.cont_viii.reproducibility import evaluate_reproducibility
from gunnchos_device_os.cont_viii.factory_station import run_factory_station
from gunnchos_device_os.cont_viii.device_management_plane import run_device_management_plane
from gunnchos_device_os.cont_viii.baselines import evaluate_baselines
from gunnchos_device_os.cont_viii.media_baseline import evaluate_media_baseline
from gunnchos_device_os.cont_viii.dock_daily_workflow import run_dock_daily_workflow
from gunnchos_device_os.cont_viii.performance_models import evaluate_performance_models
from gunnchos_device_os.cont_viii.audience_docs import evaluate_audience_docs
from gunnchos_device_os.cont_viii.adopter_sdk_check import evaluate_adopter_sdk
from gunnchos_device_os.cont_viii.recreation_reprove import reprove_recreation
from gunnchos_device_os.cont_viii.release_readiness import (
    evaluate_release_readiness,
    scan_false_ready_claims,
)
from gunnchos_device_os.cont_viii import (
    TOKEN_ADOPTER_SDK_PASS,
    TOKEN_API_ABI_PASS,
    TOKEN_AUDIENCE_DOCS_PASS,
    TOKEN_BASELINES_PASS,
    TOKEN_DEVICE_MGMT_PASS,
    TOKEN_DOCK_DAILY_PASS,
    TOKEN_FACTORY_PASS,
    TOKEN_MEDIA_PASS,
    TOKEN_OFFICE_E2E_PASS,
    TOKEN_OFFICE_FILE_COMPAT_PASS,
    TOKEN_PERF_MODELS_PASS,
    TOKEN_PRODUCTIVITY_STACK_PASS,
    TOKEN_RECREATION_REPROVE_PASS,
    TOKEN_RELEASE_SCORECARD_PASS,
    TOKEN_REPRO_PASS,
    TOKEN_STUDENT_E2E_PASS,
)

# Schema close evidence on Cont VII main
SCHEMA_IDS = (
    "CG-QUALITY-001",
    "CG-QUALITY-007",
    "CG-QUALITY-008",
    "RING-RELIAB-016",
)


def test_productivity_stack():
    r = build_productivity_stack()
    assert r["ok"] and r["token"] == TOKEN_PRODUCTIVITY_STACK_PASS
    assert r["office_choice"] == "libreoffice"
    assert r["rewrites_ms_office"] is False


def test_student_e2e():
    r = run_student_e2e()
    assert r["ok"] and r["token"] == TOKEN_STUDENT_E2E_PASS
    assert r["missing"] == []


def test_office_e2e():
    r = run_office_e2e()
    assert r["ok"] and r["token"] == TOKEN_OFFICE_E2E_PASS
    assert r["ms_fidelity_claimed"] is False


def test_office_file_compat():
    r = run_office_file_compat()
    assert r["ok"] and r["token"] == TOKEN_OFFICE_FILE_COMPAT_PASS
    assert r["ms_fidelity_claimed"] is False
    assert len(r["results"]) >= 13


def test_api_abi_policy():
    r = evaluate_api_abi_policy()
    assert r["ok"] and r["token"] == TOKEN_API_ABI_PASS
    assert "app_manifest" in r["surfaces"]


def test_reproducibility():
    r = evaluate_reproducibility()
    assert r["ok"] and r["token"] == TOKEN_REPRO_PASS
    assert r["checks"]["no_laptop_only_paths"] is True


def test_factory_station():
    r = run_factory_station()
    assert r["ok"] and r["token"] == TOKEN_FACTORY_PASS
    assert r["production_private_keys_in_repo"] == []
    assert r["simulated_hal"] is True


def test_device_management_plane():
    r = run_device_management_plane()
    assert r["ok"] and r["token"] == TOKEN_DEVICE_MGMT_PASS
    assert r["release_runtime_is_mock"] is False


def test_baselines():
    r = evaluate_baselines()
    assert r["ok"] and r["token"] == TOKEN_BASELINES_PASS


def test_media_baseline():
    r = evaluate_media_baseline()
    assert r["ok"] and r["token"] == TOKEN_MEDIA_PASS
    assert r["drm_certified"] is False


def test_dock_daily():
    r = run_dock_daily_workflow()
    assert r["ok"] and r["token"] == TOKEN_DOCK_DAILY_PASS


def test_performance_models():
    r = evaluate_performance_models()
    assert r["ok"] and r["token"] == TOKEN_PERF_MODELS_PASS
    assert r["measured_physical"] is False


def test_audience_docs():
    r = evaluate_audience_docs()
    assert r["ok"] and r["token"] == TOKEN_AUDIENCE_DOCS_PASS
    assert r["gate_language_in_user_docs"] == []


def test_adopter_sdk():
    r = evaluate_adopter_sdk()
    assert r["ok"] and r["token"] == TOKEN_ADOPTER_SDK_PASS


def test_recreation_reprove():
    r = reprove_recreation()
    assert r["ok"] and r["token"] == TOKEN_RECREATION_REPROVE_PASS
    assert r["gaps"] == []


def test_release_readiness_scorecard_and_firewall():
    fw = scan_false_ready_claims()
    assert fw["ok"] is True
    r = evaluate_release_readiness(write=True)
    assert r["ok"] and r["token"] == TOKEN_RELEASE_SCORECARD_PASS
    assert r["physical_execution_freeze"] is True
    assert r["blockers"]["PHYSICAL"]
    assert Path("results/cont_viii/release_readiness_scorecard.json").exists()


def test_schema_nodes_closed_on_tree():
    """CG-QUALITY-001/007/008 + RING-RELIAB-016 must have product code + tests."""
    root = Path(__file__).resolve().parents[1]
    mapping = {
        "CG-QUALITY-001": (
            "gunnchos_device_os/clean_installation.py",
            "tests/test_product_quality_clean_installation.py",
        ),
        "CG-QUALITY-007": (
            "gunnchos_device_os/localization.py",
            "tests/test_product_quality_localization.py",
        ),
        "CG-QUALITY-008": (
            "gunnchos_device_os/repair_documentation.py",
            "tests/test_product_quality_repair_documentation.py",
        ),
        "RING-RELIAB-016": (
            "gunnchos_device_os/silent_destructive_uncertain_gestures.py",
            "tests/test_silent_destructive_uncertain_gestures.py",
        ),
    }
    for req_id, (mod, test) in mapping.items():
        assert (root / mod).exists(), f"missing impl for {req_id}"
        assert (root / test).exists(), f"missing test for {req_id}"
        text = (root / mod).read_text(encoding="utf-8")
        assert req_id in text
        assert "SCHEMA_ONLY" not in text
