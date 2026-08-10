"""Scorecard load/validate helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from gunnchos_device_os.golden_journeys.constants import CLAIM_BOUNDARY, SCHEMA_SCORECARD

_EVIDENCE_RANK = {"E0": 0, "E1": 1, "E2": 2, "E3": 3, "E4": 4, "E5": 5, "E6": 6, "E7": 7}


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


def validate_competitor_matrix_consistency(
    root: Path | None = None,
) -> dict[str, Any]:
    """Fail on narrative vs structured E/D/IV contradictions in the competitor matrix.

    Does not claim Independent PASS. Implementer/CI integrity guard only.
    """
    root = root or _root()
    path = root / "quality/golden_journeys/COMPETITOR_READINESS_GAP_MATRIX.json"
    errors: list[str] = []
    if not path.exists():
        return {"ok": False, "errors": ["missing_competitor_matrix"], "contradiction_count": 1}

    m = json.loads(path.read_text(encoding="utf-8"))
    for cap in m.get("capabilities", []):
        cid = cap.get("capability_id") or "unknown"
        depth = cap.get("current_depth_level")
        evid = cap.get("current_evidence_level")
        iv = cap.get("independent_verification")
        blob = json.dumps(cap)
        digital = str(cap.get("digital_gap") or "")

        # Narrative claims of earned D6 PASS vs structured depth != D6
        # Do NOT flag "needs independent D6 verification" / pending language.
        claims_d6_pass = bool(
            re.search(
                r"Independent\s+(?:E4/)?D6\s+(?:PASS|earned)|Independent\s+D6\s+PASS|\bD6\s+PASS\b",
                blob,
                re.I,
            )
        ) and not re.search(
            r"needs independent D6|pending independent D6|D6 verification pending|not yet .*D6",
            blob,
            re.I,
        )
        if claims_d6_pass and depth != "D6":
            errors.append(f"matrix_narrative_d6_vs_depth:{cid}:{depth}")

        # Narrative E4 earned/PASS vs structured evidence < E4
        if re.search(
            r"Independent E4/D6 earned|Independent E4\b|Independent digital .* PASS|"
            r"Independent PASS on tip|Independent digital dock lifecycle PASS",
            digital,
            re.I,
        ):
            if _EVIDENCE_RANK.get(str(evid), -1) < _EVIDENCE_RANK["E4"]:
                if not re.search(r"\bnot yet\b|\bneeds\b|\bpending\b", digital, re.I):
                    errors.append(f"matrix_narrative_e4_vs_evidence:{cid}:{evid}")

        if iv in {"PASS", "PASS_WITH_LIMITATIONS"} and not cap.get("evidence_refs"):
            errors.append(f"matrix_iv_pass_without_evidence_refs:{cid}")

        if cap.get("competitor_score") is not None:
            if not cap.get("benchmark_reference") or "No competitor" in str(
                cap.get("external_benchmarking_gap") or ""
            ):
                errors.append(f"matrix_competitor_score_without_benchmark:{cid}")

        # Physical claims from VF1-3 / digital-only paths are invalid
        phys = str(cap.get("physical_gap") or "")
        if re.search(r"\bPHYSICAL_(?:PASS|VALIDATED|COMPLETE)\b", phys, re.I):
            if _EVIDENCE_RANK.get(str(evid), -1) < _EVIDENCE_RANK["E5"]:
                errors.append(f"matrix_physical_from_digital_only:{cid}")

        # Human preference without E6
        human = str(cap.get("human_gap") or "")
        if re.search(r"human (?:PASS|validated|complete)|preference measured", human, re.I):
            if _EVIDENCE_RANK.get(str(evid), -1) < _EVIDENCE_RANK["E6"]:
                errors.append(f"matrix_human_preference_without_e6:{cid}")

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "contradiction_count": len(errors),
        "COMPETITOR_MATRIX_CONTRADICTIONS": len(errors),
    }


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
        matrix_report = validate_competitor_matrix_consistency(root=root)
        errors.extend(matrix_report["errors"])

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "scorecard_count": len(cards),
        "independent_verification_claimed": False,
        "COMPETITOR_MATRIX_CONTRADICTIONS": sum(
            1 for e in errors if e.startswith("matrix_")
        ),
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
