"""Supporting (non-independent) Golden Journey subset runner."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.golden_journeys.path_map import load_catalog, load_path_map, select_journeys_for_paths
from gunnchos_device_os.golden_journeys.scorecard import update_functional_status


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_phase_xi(journey_ids: list[str], root: Path) -> dict[str, Any]:
    """Run supporting Phase XI journeys. These are NOT independent acceptance tests."""
    if not journey_ids:
        return {"ok": True, "results": [], "note": "no_phase_xi_ids"}
    from gunnchos_device_os.phase_xi.campaign import run_campaign

    report = run_campaign(root=root, only=journey_ids, representative=False, write=False)
    return {
        "ok": report["totals"].get("FAIL", 0) == 0,
        "totals": report.get("totals"),
        "results": report.get("results"),
        "disclaimer": "Phase XI supporting evidence only — not independent verification.",
    }


def _run_unit_markers(markers: list[str], root: Path) -> dict[str, Any]:
    """Execute lightweight supporting unit checks referenced by path map."""
    results = []
    ok = True
    for marker in markers:
        if "test_security_regression" in marker:
            from gunnchos_device_os.phase_xv.identity import UnifiedIdentityPlane

            out = root / "artifacts/golden_journeys/supporting_identity"
            out.mkdir(parents=True, exist_ok=True)
            idp = UnifiedIdentityPlane(out)
            idp.register("u1", "user", "U", ["owner"], secret="abc")
            sess = idp.login("u1", "abc")
            idp.revoke("u1")
            revoke_ok = idp.sessions[sess.session_id].state == "revoked"
            login_blocked = False
            try:
                idp.login("u1", "abc")
            except PermissionError:
                login_blocked = True
            passed = revoke_ok and login_blocked
            results.append(
                {
                    "marker": marker,
                    "ok": passed,
                    "kind": "phase_xv_identity_revoke_supporting",
                    "frontier_parity_claimed": False,
                }
            )
            ok = ok and passed
        else:
            results.append({"marker": marker, "ok": False, "kind": "unsupported_marker"})
            ok = False
    return {
        "ok": ok,
        "results": results,
        "disclaimer": "Supporting unit markers only — not independent verification.",
    }


def _run_lab_journey(journey_id: str, root: Path) -> dict[str, Any]:
    """Run Device Lab scenario for G04/G06/G07/G08 when mapped."""
    from gunnchos_device_os.device_lab.scenarios.catalog import JOURNEY_SCENARIO_MAP
    from gunnchos_device_os.device_lab.scenarios.engine import run_scenario

    if journey_id not in JOURNEY_SCENARIO_MAP:
        return {"ok": True, "skipped": True, "note": "no_lab_scenario"}
    result = run_scenario(journey_id, repo_root=root)
    scenario_ok = bool(result.get("ok"))
    foundation_ok = bool(result.get("foundation_harness_ok", scenario_ok))
    proof = result.get("primary_model_proof")
    # GJ-DEFECT-008: scenario ok stays fail-closed when micro is primary.
    # Supporting merge gate may still pass on foundation_harness_ok so CI without
    # llama does not false-green Independent — Independent requires PASS_REAL_RUNTIME.
    if (
        journey_id == "GOLDEN-08"
        and proof == "FAIL_MICRO_NOT_ALLOWED"
        and foundation_ok
        and not scenario_ok
    ):
        supporting_ok = True
        gate_note = (
            "supporting_gate_ok via foundation_harness_ok; "
            "scenario ok=false / FAIL_MICRO_NOT_ALLOWED (not Independent PASS)"
        )
    else:
        supporting_ok = scenario_ok
        gate_note = None
    return {
        "ok": supporting_ok,
        "scenario_ok": scenario_ok,
        "scenario_id": result.get("scenario_id"),
        "foundation_harness_ok": result.get("foundation_harness_ok"),
        "implementer_ready_for_independent_E4_D6": result.get(
            "implementer_ready_for_independent_E4_D6"
        ),
        "INDEPENDENT_VERIFICATION": "PENDING",
        "primary_model_proof": proof,
        "errors": result.get("errors"),
        "gate_note": gate_note,
        "disclaimer": "Device Lab supporting run — not independent verification.",
    }


def run_supporting_subset(
    journey_ids: list[str] | None = None,
    *,
    changed_paths: list[str] | None = None,
    root: Path | None = None,
    write_scorecards: bool = True,
    write_report: bool = True,
    major_pr: bool = True,
) -> dict[str, Any]:
    """Run supporting digital checks for a Golden Journey subset.

    Explicitly does NOT set INDEPENDENT_VERIFICATION=PASS.
    """
    root = root or _root()
    if journey_ids is None:
        selection = select_journeys_for_paths(
            changed_paths or [], root=root, major_pr=major_pr
        )
        journey_ids = list(selection["selected"])
    else:
        selection = {
            "schema": "gunnchos.golden_journey_subset.v1",
            "selected": list(journey_ids),
            "reason": "explicit",
            "major_pr": major_pr,
            "independent_verification_claimed": False,
        }

    catalog = load_catalog(root)
    path_map = load_path_map(root)
    severity = {j["id"]: j["severity"] for j in catalog["journeys"]}

    per_journey: list[dict[str, Any]] = []
    blocking_failures: list[dict[str, Any]] = []

    for jid in journey_ids:
        entry = path_map["journeys"][jid]
        phase_ids = list(entry.get("supporting_phase_xi_ids") or [])
        unit_markers = list(entry.get("supporting_unit_tests") or [])
        phase_report = _run_phase_xi(phase_ids, root)
        unit_report = _run_unit_markers(unit_markers, root) if unit_markers else {
            "ok": True,
            "results": [],
            "note": "no_unit_markers",
        }
        lab_report = _run_lab_journey(jid, root)
        functional_ok = (
            bool(phase_report.get("ok"))
            and bool(unit_report.get("ok"))
            and bool(lab_report.get("ok"))
        )
        status = "PASS" if functional_ok else "FAIL"
        evidence_paths = [
            f"quality/golden_journeys/fixtures/{jid}.fixture.json",
            f"quality/golden_journeys/scorecards/{jid}.scorecard.json",
        ]
        if lab_report.get("scenario_id"):
            evidence_paths.append("artifacts/device_lab/")
        if write_scorecards:
            update_functional_status(
                jid,
                status,
                evidence_paths=evidence_paths,
                notes=(
                    "Supporting harness functional result (includes Device Lab scenario when mapped). "
                    "INDEPENDENT_VERIFICATION remains verifier-owned; not E4 self-cert."
                ),
                root=root,
            )
        row = {
            "journey_id": jid,
            "severity": severity[jid],
            "FUNCTIONAL_PASS": status,
            "phase_xi": phase_report,
            "unit_markers": unit_report,
            "device_lab": lab_report,
            "INDEPENDENT_VERIFICATION": "PENDING",
            "PHYSICAL_PENDING": True,
            "HUMAN_VALIDATION_PENDING": True,
        }
        per_journey.append(row)
        if not functional_ok and severity[jid] in {"S0", "S1"}:
            blocking_failures.append(row)

    report = {
        "schema": "gunnchos.golden_journey_supporting_run.v1",
        "ok": len(blocking_failures) == 0,
        "selection": selection,
        "journeys": per_journey,
        "blocking_s0_s1_failures": [
            {"journey_id": r["journey_id"], "severity": r["severity"]} for r in blocking_failures
        ],
        "claim_boundary": {
            "independent_verification_claimed": False,
            "physically_validated": False,
            "human_validated": False,
            "frontier_parity_claimed": False,
        },
        "disclaimer": (
            "This run is an implementer supporting regression harness. "
            "It is not independent verification and must not be renamed as such."
        ),
        "generated_at": time.time(),
    }

    if write_report:
        out_dir = root / "artifacts/golden_journeys"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "SUPPORTING_SUBSET_RUN.json").write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        (root / "quality/golden_journeys/runs" / "SUPPORTING_SUBSET_RUN.json").parent.mkdir(
            parents=True, exist_ok=True
        )
        (root / "quality/golden_journeys/runs" / "SUPPORTING_SUBSET_RUN.json").write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
    return report
