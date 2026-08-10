#!/usr/bin/env python3
"""Prove Phase XIV OS digital frontier work — DIGITALLY_VALIDATED where tests pass.

PHYSICAL_EXECUTION_FREEZE=ACTIVE. Never claims GUNNCHOS_FRONTIER_OS_PARITY=true.
auto_merge_request remains null.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "phase_xiv"
sys.path.insert(0, str(ROOT))

DIGITALLY_VALIDATED = "DIGITALLY_VALIDATED"
INCOMPLETE_DIGITAL = "INCOMPLETE_DIGITAL"
PHYSICAL_PENDING = "PHYSICAL_PENDING"


def run_pytest(nodeid: str) -> dict:
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", nodeid],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": f"{ROOT}:src"},
    )
    return {
        "nodeid": nodeid,
        "rc": r.returncode,
        "out": (r.stdout or "")[-2000:],
        "err": (r.stderr or "")[-2000:],
    }


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    gates: dict[str, str] = {}
    tokens: dict[str, bool] = {}
    details: dict[str, object] = {}

    # --- A. Stage 2 reproof ---
    stage2 = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "prove_stage2_os.py")],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": f"{ROOT}:src"},
    )
    stage2_report_path = ROOT / "artifacts" / "stage2" / "OS_PROVE_REPORT.json"
    stage2_ok = stage2.returncode == 0 and stage2_report_path.exists()
    stage2_payload = {}
    if stage2_report_path.exists():
        stage2_payload = json.loads(stage2_report_path.read_text(encoding="utf-8"))
        stage2_ok = stage2_ok and bool(stage2_payload.get("digitally_validated_gates"))
        stage2_ok = stage2_ok and stage2_payload.get("GUNNCHOS_FRONTIER_OS_PARITY") is False
    reproof = {
        "schema": "gunnchos.phase_xiv.stage2_reproof.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accepted_main": "a2d3a2aec6d3089cdcda29212bc2b839931ad61b",
        "ok": stage2_ok,
        "prove_rc": stage2.returncode,
        "digitally_validated_gates": stage2_payload.get("digitally_validated_gates", []),
        "tokens": stage2_payload.get("tokens", {}),
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "physical_execution_freeze": True,
        "auto_merge_request": None,
    }
    (ART / "STAGE2_REPROOF.json").write_text(json.dumps(reproof, indent=2) + "\n", encoding="utf-8")
    gates["stage2-reproof"] = DIGITALLY_VALIDATED if stage2_ok else INCOMPLETE_DIGITAL
    tokens["STAGE2_REPROOF_PASS"] = stage2_ok
    details["stage2_reproof"] = {
        "ok": stage2_ok,
        "gates": stage2_payload.get("digitally_validated_gates", []),
    }

    # --- B/C module digital proofs ---
    from gunnchos_device_os.phase_xiv.ai_system import OsAiSystemApi
    from gunnchos_device_os.phase_xiv.callers import CrossProductCallers
    from gunnchos_device_os.phase_xiv.compositor import run_form_factor_e2e
    from gunnchos_device_os.phase_xiv.continuity import ContinuityMesh
    from gunnchos_device_os.phase_xiv.fabric import GunnchFabric
    from gunnchos_device_os.phase_xiv.local_ai import LocalAiRuntime, ModelRegistry
    from gunnchos_device_os.phase_xiv.mdm import EducationMdm
    from gunnchos_device_os.phase_xiv.packages import PackageManager
    from gunnchos_device_os.phase_xiv.play import GunnchPlay
    from gunnchos_device_os.phase_xiv.sdk import DeveloperSdk
    from gunnchos_device_os.phase_xiv.spatial import SpatialInputService

    comp = run_form_factor_e2e()
    gates["graphics-compositor"] = DIGITALLY_VALIDATED if comp.get("ok") else INCOMPLETE_DIGITAL
    tokens["GRAPHICS_COMPOSITOR_DIGITAL_PASS"] = bool(comp.get("ok"))
    details["compositor"] = {"ok": comp.get("ok"), "stack": "weston+wlroots"}

    reg = ModelRegistry(ART / "prove_registry")
    rt = LocalAiRuntime(reg, timeout_s=15)
    # Digital prove uses the always-on micro local tier (registry+hash+fallback).
    # Optional llama/GGUF is covered by pytest::test_local_ai_llama_tier_if_available.
    models = rt.ensure_default_models(ROOT, include_llama=False)
    rt.preferred = "micro-deterministic-v1"
    local_out = rt.run_capability("tutor", "Explain OFDM briefly for a student.")
    local_ok = (
        bool(local_out.get("ok"))
        and "micro-deterministic-v1" in models
        and local_out.get("runtime") == "deterministic_micro"
        and bool(reg.models["micro-deterministic-v1"].sha256)
    )
    api = OsAiSystemApi(local_runtime=rt)
    caps_ok = len(api.list_capabilities()) == 8
    from gunnchos_device_os.phase_xiv.ai_system import AiRequest

    inv_ok = all(api.invoke(AiRequest(c, c)).ok for c in api.list_capabilities())
    ai_ok = caps_ok and inv_ok and local_ok
    gates["ai-system-api"] = DIGITALLY_VALIDATED if ai_ok else INCOMPLETE_DIGITAL
    tokens["AI_SYSTEM_API_DIGITAL_PASS"] = ai_ok
    gates["local-ai"] = DIGITALLY_VALIDATED if local_ok else INCOMPLETE_DIGITAL
    tokens["LOCAL_AI_DIGITAL_PASS"] = local_ok
    details["local_ai"] = {
        "models": models,
        "preferred_used": local_out.get("route", {}).get("model_id"),
        "runtime": local_out.get("runtime"),
        "tier": local_out.get("tier"),
        "ok": local_ok,
        "http_stub_sole_proof": False,
    }

    callers = CrossProductCallers(api).run_all_smoke()
    gates["cross-product-callers"] = DIGITALLY_VALIDATED if callers.get("ok") else INCOMPLETE_DIGITAL
    tokens["CROSS_PRODUCT_CALLERS_DIGITAL_PASS"] = bool(callers.get("ok"))
    details["callers"] = {"ok": callers.get("ok"), "products": callers.get("products")}

    cont = ContinuityMesh(ART / "prove_cont").e2e_handheld_student_dsxl()
    gates["gunnch-continuity"] = DIGITALLY_VALIDATED if cont.get("ok") else INCOMPLETE_DIGITAL
    tokens["CONTINUITY_DIGITAL_PASS"] = bool(cont.get("ok"))

    play = GunnchPlay(ART / "prove_play").e2e(ROOT)
    gates["gunnch-play"] = DIGITALLY_VALIDATED if play.get("ok") else INCOMPLETE_DIGITAL
    tokens["GUNNCHPLAY_DIGITAL_PASS"] = bool(play.get("ok"))

    fabric = GunnchFabric().e2e()
    gates["gunnch-fabric"] = DIGITALLY_VALIDATED if fabric.get("ok") else INCOMPLETE_DIGITAL
    tokens["GUNNCHFABRIC_DIGITAL_PASS"] = bool(fabric.get("ok"))

    spatial = SpatialInputService().e2e_edge_to_apps()
    gates["spatial-input"] = DIGITALLY_VALIDATED if spatial.get("ok") else INCOMPLETE_DIGITAL
    tokens["SPATIAL_INPUT_DIGITAL_PASS"] = bool(spatial.get("ok"))

    pkg = PackageManager(ART / "prove_pkg").e2e()
    gates["package-management"] = DIGITALLY_VALIDATED if pkg.get("ok") else INCOMPLETE_DIGITAL
    tokens["PACKAGE_MANAGEMENT_DIGITAL_PASS"] = bool(pkg.get("ok"))

    sdk = DeveloperSdk(ART / "prove_sdk").e2e(ROOT / "os_build" / "phase_xiv" / "sdk_templates")
    gates["developer-sdk"] = DIGITALLY_VALIDATED if sdk.get("ok") else INCOMPLETE_DIGITAL
    tokens["DEVELOPER_SDK_DIGITAL_PASS"] = bool(sdk.get("ok"))

    mdm = EducationMdm(ART / "prove_mdm").e2e_ten_device_fleet(ROOT)
    gates["mdm-education"] = DIGITALLY_VALIDATED if mdm.get("ok") else INCOMPLETE_DIGITAL
    tokens["MDM_EDUCATION_DIGITAL_PASS"] = bool(mdm.get("ok"))

    # Physical accuracy remains pending for all hardware-touching surfaces
    gates["physical-accuracy"] = PHYSICAL_PENDING
    tokens["PHYSICAL_ACCURACY_CLAIMED"] = False

    pytest_jobs = {
        "graphics-compositor": "tests/phase_xiv/test_phase_xiv.py::test_compositor_form_factor_e2e",
        "ai-system-api": "tests/phase_xiv/test_phase_xiv.py::test_ai_system_api_no_model_paths",
        "local-ai": "tests/phase_xiv/test_phase_xiv.py::test_local_ai_registry_hash_fallback",
        "cross-product-callers": "tests/phase_xiv/test_phase_xiv.py::test_cross_product_callers",
        "gunnch-continuity": "tests/phase_xiv/test_phase_xiv.py::test_continuity_handheld_student_dsxl",
        "gunnch-play": "tests/phase_xiv/test_phase_xiv.py::test_gunnchplay_first_party",
        "gunnch-fabric": "tests/phase_xiv/test_phase_xiv.py::test_fabric_camera_npu_fallback",
        "spatial-input": "tests/phase_xiv/test_phase_xiv.py::test_spatial_edge_to_apps",
        "package-management": "tests/phase_xiv/test_phase_xiv.py::test_package_channels_sign_rollback_revoke",
        "developer-sdk": "tests/phase_xiv/test_phase_xiv.py::test_sdk_templates",
        "mdm-education": "tests/phase_xiv/test_phase_xiv.py::test_mdm_ten_device_fleet",
    }
    pytest_results = {}
    for gate, node in pytest_jobs.items():
        pr = run_pytest(node)
        pytest_results[gate] = {"rc": pr["rc"]}
        if pr["rc"] != 0:
            gates[gate] = INCOMPLETE_DIGITAL
            for tok, gname in (
                ("GRAPHICS_COMPOSITOR_DIGITAL_PASS", "graphics-compositor"),
                ("AI_SYSTEM_API_DIGITAL_PASS", "ai-system-api"),
                ("LOCAL_AI_DIGITAL_PASS", "local-ai"),
                ("CROSS_PRODUCT_CALLERS_DIGITAL_PASS", "cross-product-callers"),
                ("CONTINUITY_DIGITAL_PASS", "gunnch-continuity"),
                ("GUNNCHPLAY_DIGITAL_PASS", "gunnch-play"),
                ("GUNNCHFABRIC_DIGITAL_PASS", "gunnch-fabric"),
                ("SPATIAL_INPUT_DIGITAL_PASS", "spatial-input"),
                ("PACKAGE_MANAGEMENT_DIGITAL_PASS", "package-management"),
                ("DEVELOPER_SDK_DIGITAL_PASS", "developer-sdk"),
                ("MDM_EDUCATION_DIGITAL_PASS", "mdm-education"),
            ):
                if gname == gate:
                    tokens[tok] = False

    report = {
        "schema": "gunnchos.phase_xiv.os_prove_report.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "accepted_main_base": "a2d3a2aec6d3089cdcda29212bc2b839931ad61b",
        "physical_execution_freeze": True,
        "auto_merge_request": None,
        "frontier_os_parity_claimed": False,
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "gates": gates,
        "tokens": tokens,
        "digitally_validated_gates": sorted(g for g, s in gates.items() if s == DIGITALLY_VALIDATED),
        "incomplete_gates": sorted(g for g, s in gates.items() if s == INCOMPLETE_DIGITAL),
        "physical_pending_gates": sorted(g for g, s in gates.items() if s == PHYSICAL_PENDING),
        "pytest": pytest_results,
        "details": details,
        "artifacts": {
            "stage2_reproof": "artifacts/phase_xiv/STAGE2_REPROOF.json",
            "os_prove_report": "artifacts/phase_xiv/OS_PROVE_REPORT.json",
        },
    }

    def _scrub(obj):
        if isinstance(obj, dict):
            return {k: _scrub(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [_scrub(x) for x in obj]
        if isinstance(obj, str) and ("/Users/" in obj or obj.startswith("/home/")):
            return "artifacts/phase_xiv/(scrubbed)"
        return obj

    report = _scrub(report)
    out = ART / "OS_PROVE_REPORT.json"
    text = json.dumps(report, indent=2) + "\n"
    if "/Users/" in text:
        raise SystemExit("host path leaked into prove report")
    out.write_text(text, encoding="utf-8")
    summary = {
        "ok": not report["incomplete_gates"],
        "report": str(out.relative_to(ROOT)),
        "digitally_validated_gates": report["digitally_validated_gates"],
        "incomplete_gates": report["incomplete_gates"],
        "physical_pending_gates": report["physical_pending_gates"],
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "auto_merge_request": None,
    }
    print(json.dumps(summary, indent=2))
    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
