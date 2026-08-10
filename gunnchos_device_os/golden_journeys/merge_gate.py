"""Merge recommendation gate for Golden Journey S0/S1 failures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.golden_journeys.harness import run_supporting_subset
from gunnchos_device_os.golden_journeys.path_map import load_catalog, select_journeys_for_paths
from gunnchos_device_os.golden_journeys.scorecard import load_scorecard, validate_scorecards


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


def recommend_merge(
    *,
    changed_paths: list[str] | None = None,
    journey_ids: list[str] | None = None,
    root: Path | None = None,
    run_harness: bool = True,
    major_pr: bool = True,
) -> dict[str, Any]:
    """Recommend merge only when supporting S0/S1 functional checks pass.

    Never asserts independent verification, physical, or human validation.
    """
    root = root or _root()
    schema_check = validate_scorecards(root=root)
    selection = select_journeys_for_paths(
        changed_paths or [],
        root=root,
        force_all=False,
        major_pr=major_pr,
    )
    if journey_ids is not None:
        selection["selected"] = list(journey_ids)
        selection["reason"] = "explicit"

    run = None
    if run_harness:
        run = run_supporting_subset(
            selection["selected"],
            root=root,
            write_scorecards=True,
            write_report=True,
            major_pr=major_pr,
        )

    catalog = load_catalog(root)
    severity = {j["id"]: j["severity"] for j in catalog["journeys"]}
    blockers: list[dict[str, Any]] = []

    for jid in selection["selected"]:
        card = load_scorecard(jid, root)
        sev = severity[jid]
        functional = (card.get("FUNCTIONAL_PASS") or {}).get("status")
        if sev in {"S0", "S1"} and functional == "FAIL":
            blockers.append(
                {
                    "journey_id": jid,
                    "severity": sev,
                    "reason": "FUNCTIONAL_PASS_FAIL",
                    "blocks_merge_recommendation": True,
                }
            )
        if sev in {"S0", "S1"} and functional in {"NOT_RUN", "BLOCKED"} and run_harness:
            blockers.append(
                {
                    "journey_id": jid,
                    "severity": sev,
                    "reason": f"FUNCTIONAL_PASS_{functional}",
                    "blocks_merge_recommendation": True,
                }
            )
        # Independent verification absence does NOT block merge recommendation for Cycle 1 infra,
        # but must remain non-PASS from implementer.
        indep = (card.get("INDEPENDENT_VERIFICATION") or {}).get("status")
        if indep == "PASS" and (card.get("updated_by") or "").startswith("implementer"):
            blockers.append(
                {
                    "journey_id": jid,
                    "severity": sev,
                    "reason": "implementer_claimed_independent_pass",
                    "blocks_merge_recommendation": True,
                }
            )

    if not schema_check["ok"]:
        blockers.append(
            {
                "journey_id": None,
                "severity": "S1",
                "reason": "scorecard_schema_invalid",
                "errors": schema_check["errors"],
                "blocks_merge_recommendation": True,
            }
        )

    merge_recommended = len(blockers) == 0
    report = {
        "schema": "gunnchos.golden_journey_merge_recommendation.v1",
        "merge_recommended": merge_recommended,
        "auto_merge": False,
        "draft_only": True,
        "selection": selection,
        "schema_check": schema_check,
        "supporting_run_ok": None if run is None else run.get("ok"),
        "blockers": blockers,
        "claim_boundary": {
            "independent_verification_claimed": False,
            "physically_validated": False,
            "human_validated": False,
            "frontier_parity_claimed": False,
            "note": "Merge recommendation is based on supporting functional gates only.",
        },
    }
    out = root / "artifacts/golden_journeys/MERGE_RECOMMENDATION.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    return report
