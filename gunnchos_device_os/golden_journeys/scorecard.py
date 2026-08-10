"""Scorecard load/validate helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.golden_journeys.constants import CLAIM_BOUNDARY, SCHEMA_SCORECARD


def _root() -> Path:
    return Path(__file__).resolve().parents[2]


QUALITY_DIMS = [
    "correctness",
    "reliability",
    "latency_perceived_performance",
    "visual_quality",
    "interaction_quality",
    "discoverability",
    "consistency",
    "accessibility",
    "error_recovery",
    "user_preference",
]


def scorecard_path(journey_id: str, root: Path | None = None) -> Path:
    root = root or _root()
    return root / "quality/golden_journeys/scorecards" / f"{journey_id}.scorecard.json"


def load_scorecard(journey_id: str, root: Path | None = None) -> dict[str, Any]:
    return json.loads(scorecard_path(journey_id, root).read_text(encoding="utf-8"))


def validate_scorecards(root: Path | None = None) -> dict[str, Any]:
    """Structural validation of all Golden Journey scorecards.

    Does not claim independent verification. Rejects forbidden claim flags.
    """
    root = root or _root()
    catalog = json.loads(
        (root / "quality/golden_journeys/GOLDEN_JOURNEYS.json").read_text(encoding="utf-8")
    )
    errors: list[str] = []
    cards: list[dict[str, Any]] = []

    for j in catalog["journeys"]:
        jid = j["id"]
        path = scorecard_path(jid, root)
        if not path.exists():
            errors.append(f"missing_scorecard:{jid}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        cards.append(data)
        if data.get("schema") != SCHEMA_SCORECARD:
            errors.append(f"bad_schema:{jid}")
        if data.get("journey_id") != jid:
            errors.append(f"journey_id_mismatch:{jid}")
        for key in (
            "FUNCTIONAL_PASS",
            "PRODUCT_QUALITY_SCORE",
            "INDEPENDENT_VERIFICATION",
            "PHYSICAL_PENDING",
            "HUMAN_VALIDATION_PENDING",
            "claim_boundary",
        ):
            if key not in data:
                errors.append(f"missing_key:{jid}:{key}")

        boundary = data.get("claim_boundary") or {}
        for k, v in CLAIM_BOUNDARY.items():
            if boundary.get(k) is not v:
                errors.append(f"claim_boundary_violation:{jid}:{k}")

        indep = data.get("INDEPENDENT_VERIFICATION") or {}
        if indep.get("status") == "PASS" and data.get("updated_by", "").startswith("implementer"):
            errors.append(f"implementer_must_not_claim_independent_pass:{jid}")

        phys = data.get("PHYSICAL_PENDING") or {}
        if phys.get("pending") is not True or phys.get("target_evidence_level") != "E5":
            errors.append(f"physical_pending_invalid:{jid}")

        human = data.get("HUMAN_VALIDATION_PENDING") or {}
        if human.get("pending") is not True or human.get("target_evidence_level") != "E6":
            errors.append(f"human_pending_invalid:{jid}")

        dims = ((data.get("PRODUCT_QUALITY_SCORE") or {}).get("dimensions") or {})
        for d in QUALITY_DIMS:
            if d not in dims:
                errors.append(f"missing_dimension:{jid}:{d}")
        pref = dims.get("user_preference") or {}
        if pref.get("value") not in ("NOT_MEASURED", None) and human.get("pending") is True:
            # Allow only NOT_MEASURED while human validation pending
            if pref.get("value") != "NOT_MEASURED":
                errors.append(f"user_preference_scored_without_humans:{jid}")

        fixture = root / "quality/golden_journeys/fixtures" / f"{jid}.fixture.json"
        if not fixture.exists():
            errors.append(f"missing_fixture:{jid}")

    plan = root / "quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_PLAN.md"
    if not plan.exists():
        errors.append("missing_verifier_plan_stub")

    matrix = root / "quality/golden_journeys/COMPETITOR_READINESS_GAP_MATRIX.json"
    if not matrix.exists():
        errors.append("missing_competitor_matrix")
    else:
        m = json.loads(matrix.read_text(encoding="utf-8"))
        if m.get("doctrine", {}).get("frontier_parity_claimed") is True:
            errors.append("competitor_matrix_frontier_parity_claimed")
        for cap in m.get("capabilities", []):
            if cap.get("competitor_score") is not None:
                # Explicitly forbid fabricated scores in this implementer packet
                errors.append(f"fabricated_or_unexpected_competitor_score:{cap.get('capability_id')}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "scorecard_count": len(cards),
        "independent_verification_claimed": False,
    }


def update_functional_status(
    journey_id: str,
    status: str,
    *,
    evidence_paths: list[str] | None = None,
    notes: str = "",
    root: Path | None = None,
) -> dict[str, Any]:
    """Update FUNCTIONAL_PASS from supporting harness only.

    Never downgrades independent-verifier INDEPENDENT_VERIFICATION or hijacks
    updated_by when a verifier already recorded PASS/PARTIAL/FAIL.
    """
    root = root or _root()
    data = load_scorecard(journey_id, root)
    prior_iv = dict(data.get("INDEPENDENT_VERIFICATION") or {})
    prior_by = data.get("updated_by") or ""
    verifier_owned = prior_by.startswith("independent-verifier") or prior_iv.get("status") in {
        "PASS",
        "PARTIAL",
        "FAIL",
    }

    data["FUNCTIONAL_PASS"] = {
        "status": status,
        "authority": "implementer_supporting_harness",
        "evidence_paths": evidence_paths or [],
        "notes": notes
        or "Supporting harness result only — not independent verification.",
    }
    # Preserve verifier ownership metadata; never flip independent claim
    data["INDEPENDENT_VERIFICATION"] = prior_iv or {
        "status": "PENDING",
        "evidence_level_claimed": None,
        "depth_level_claimed": None,
        "verifier_plan_path": "quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_PLAN.md",
        "verifier_result_path": None,
        "notes": "Verifier owns plan and results. Implementer must not set PASS.",
    }
    if verifier_owned:
        data["updated_by"] = prior_by
    else:
        data["updated_by"] = "implementer-supporting-harness"
    data["claim_boundary"] = dict(CLAIM_BOUNDARY)
    scorecard_path(journey_id, root).write_text(
        json.dumps(data, indent=2) + "\n", encoding="utf-8"
    )
    return data
