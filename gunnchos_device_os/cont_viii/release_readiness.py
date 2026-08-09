"""Release-readiness scorecard + false-claim firewall (Lane I)."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import re
import time

from gunnchos_device_os.cont_viii import (
    CLAIM_BOUNDARY,
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

READY_TOKEN_RE = re.compile(r"(?P<name>[A-Za-z0-9_]+_ready)\s*[:=]\s*true", re.I)


def _collect() -> dict[str, dict[str, Any]]:
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

    runners: list[tuple[str, str, Callable[[], dict[str, Any]]]] = [
        ("productivity_stack", TOKEN_PRODUCTIVITY_STACK_PASS, build_productivity_stack),
        ("student_e2e", TOKEN_STUDENT_E2E_PASS, run_student_e2e),
        ("office_e2e", TOKEN_OFFICE_E2E_PASS, run_office_e2e),
        ("office_file_compat", TOKEN_OFFICE_FILE_COMPAT_PASS, run_office_file_compat),
        ("adopter_sdk", TOKEN_ADOPTER_SDK_PASS, evaluate_adopter_sdk),
        ("api_abi", TOKEN_API_ABI_PASS, evaluate_api_abi_policy),
        ("reproducibility", TOKEN_REPRO_PASS, evaluate_reproducibility),
        ("factory_station", TOKEN_FACTORY_PASS, run_factory_station),
        ("device_management", TOKEN_DEVICE_MGMT_PASS, run_device_management_plane),
        ("baselines", TOKEN_BASELINES_PASS, evaluate_baselines),
        ("media", TOKEN_MEDIA_PASS, evaluate_media_baseline),
        ("dock_daily", TOKEN_DOCK_DAILY_PASS, run_dock_daily_workflow),
        ("performance_models", TOKEN_PERF_MODELS_PASS, evaluate_performance_models),
        ("audience_docs", TOKEN_AUDIENCE_DOCS_PASS, evaluate_audience_docs),
        ("recreation_reprove", TOKEN_RECREATION_REPROVE_PASS, reprove_recreation),
    ]
    lanes = {}
    for key, expected_token, fn in runners:
        report = fn()
        earned = bool(report.get("ok")) and report.get("token") == expected_token
        lanes[key] = {
            "ok": bool(report.get("ok")),
            "token": report.get("token"),
            "expected_token": expected_token,
            "earned": earned,
            "report_schema": report.get("schema"),
        }
    return lanes


def scan_false_ready_claims(root: Path | None = None) -> dict[str, Any]:
    """Reject false *_ready=true claims without adjacent evidence tokens."""
    root = root or Path(__file__).resolve().parents[2]
    violations = []
    allow_paths = {
        "beta_gate/beta_gate_status.yaml",  # explicitly false
    }
    # Only scan claim-ish docs / yaml / json under controlled dirs
    scan_roots = [
        root / "beta_gate",
        root / "release_artifacts",
        root / "results/cont_viii",
        root / "docs/full_product",
    ]
    for base in scan_roots:
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if path.suffix.lower() not in {".yaml", ".yml", ".json", ".md"}:
                continue
            rel = str(path.relative_to(root))
            if rel in allow_paths:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            for m in READY_TOKEN_RE.finditer(text):
                name = m.group("name")
                # Evidence required: nearby token_earned or explicit evidence field
                window = text[max(0, m.start() - 200) : m.end() + 200]
                has_evidence = (
                    "token_earned" in window
                    or "evidence" in window.lower()
                    or "DIGITAL_PASS" in window
                    or name.lower() in {"schema_ready"}  # non-product
                )
                # beta_ready true is never allowed without full gate
                if name.lower() == "beta_ready":
                    violations.append({"path": rel, "claim": name, "reason": "beta_ready_true_forbidden_without_gate"})
                    continue
                if not has_evidence:
                    violations.append({"path": rel, "claim": name, "reason": "ready_true_without_evidence_window"})
    return {"ok": len(violations) == 0, "violations": violations}


def evaluate_release_readiness(*, write: bool = True) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    lanes = _collect()
    firewall = scan_false_ready_claims(root)
    earned = {k: v for k, v in lanes.items() if v["earned"]}
    missing = {k: v for k, v in lanes.items() if not v["earned"]}
    digital_blockers = sorted(missing.keys())
    physical_blockers = [
        "PHYSICAL_EXECUTION_FREEZE",
        "physical_boot_on_EVT_hardware",
        "physical_printer_CUPS",
        "physical_BT_audio_lab",
        "physical_dock_display_lab",
        "battery_lab_measurements",
    ]
    external_blockers = [
        "MS_Office_perfect_fidelity_not_claimed",
        "carrier_certification",
        "store_submission_HSM_signing",
        "production_cloud_credentials",
    ]
    ok = len(missing) == 0 and firewall["ok"]
    report = {
        "schema": "gunnchos.release_readiness_scorecard.v1",
        "ok": ok,
        "token": TOKEN_RELEASE_SCORECARD_PASS if ok else None,
        "lanes": lanes,
        "earned_tokens": sorted({v["token"] for v in earned.values() if v["token"]}),
        "missing_lanes": digital_blockers,
        "firewall": firewall,
        "blockers": {
            "DIGITAL": digital_blockers,
            "PHYSICAL": physical_blockers,
            "EXTERNAL": external_blockers,
        },
        "generated_at": time.time(),
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "physical_execution_freeze": True,
        "merge_forbidden": True,
    }
    if write:
        out = root / "results/cont_viii"
        out.mkdir(parents=True, exist_ok=True)
        (out / "release_readiness_scorecard.json").write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
    return report
