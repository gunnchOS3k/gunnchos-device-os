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
        functional_ok = bool(phase_report.get("ok")) and bool(unit_report.get("ok"))
        status = "PASS" if functional_ok else "FAIL"
        evidence_paths = [
            f"quality/golden_journeys/fixtures/{jid}.fixture.json",
            f"quality/golden_journeys/scorecards/{jid}.scorecard.json",
        ]
        if write_scorecards:
            update_functional_status(
                jid,
                status,
                evidence_paths=evidence_paths,
                notes=(
                    "Supporting harness functional result. "
                    "INDEPENDENT_VERIFICATION remains PENDING; not E4."
                ),
                root=root,
            )
        row = {
            "journey_id": jid,
            "severity": severity[jid],
            "FUNCTIONAL_PASS": status,
            "phase_xi": phase_report,
            "unit_markers": unit_report,
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
