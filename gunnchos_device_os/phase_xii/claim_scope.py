"""Rescope Phase XI tokens: behavioral harness vs real-app proven."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REAL_DAY_TOKENS = (
    "GUNNCHOS_REAL_STUDENT_DAY_DIGITAL_PASS",
    "GUNNCHOS_REAL_OFFICE_DAY_DIGITAL_PASS",
    "GUNNCHOS_REAL_CREATOR_DAY_DIGITAL_PASS",
    "GUNNCHOS_REAL_RECREATION_DAY_DIGITAL_PASS",
    "GUNNCHOS_REAL_EDUCATOR_DAY_DIGITAL_PASS",
    "GUNNCHOS_REAL_ADMIN_DAY_DIGITAL_PASS",
)


def write_claim_scope(root: Path) -> dict[str, Any]:
    xi_tokens_path = root / "artifacts" / "phase_xi" / "JOURNEY_TOKENS.json"
    xi = json.loads(xi_tokens_path.read_text(encoding="utf-8")) if xi_tokens_path.exists() else {}
    ledger_path = root / "artifacts" / "phase_xii" / "REALITY_DEPTH_LEDGER.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8")) if ledger_path.exists() else {}
    rj_path = root / "artifacts" / "phase_xii" / "rj" / "RJ_CAMPAIGN_REPORT.json"
    rj = json.loads(rj_path.read_text(encoding="utf-8")) if rj_path.exists() else {}

    tokens: dict[str, Any] = {}
    for tok in xi.get("earned") or list((xi.get("status") or {}).keys()):
        tokens[tok] = {
            "historical_phase_xi_value": (xi.get("status") or {}).get(tok, True),
            "VALID_AS_BEHAVIORAL_HARNESS": True,
            "NOT_YET_REAL_APP_PROVEN": tok in REAL_DAY_TOKENS or tok.endswith("_DAY_DIGITAL_PASS"),
            "phase_xii_real_app_value": bool(rj.get(tok)) if tok in REAL_DAY_TOKENS else None,
            "requires_min_depth": "L4_REAL_APPLICATION_PROCESS",
        }

    # Firewall rules
    firewall = {
        "reject_REAL_DAY_DIGITAL_PASS_below_L4_L5": True,
        "allow_BEHAVIORAL_JOURNEY_HARNESS_PASS": True,
        "forbidden_proofs": [
            "GENERIC_OK_HANDLER_AS_E2E",
            "FIXTURE_JSON_AS_GAME_LAUNCH",
            "AI_STUB_AS_GUNNCHAI_PROOF",
            "HTTP_FAKE_AS_PROTOCOL_PROOF",
        ],
        "PHASE_XI_BEHAVIORAL_JOURNEY_HARNESS_PASS": True,
        "PHASE_XI_REAL_APPLICATION_DAY_PROOF": "NOT_YET_PROVEN",
    }

    scope = {
        "schema": "gunnchos.phase_xii.claim_scope.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "phase_xi_tokens_preserved": True,
        "tokens": tokens,
        "firewall": firewall,
        "ledger_journeys_not_yet_real": ledger.get("journeys_not_yet_real_app_proven"),
        "rj_summary": {
            "pass_count": rj.get("pass_count"),
            "fail_count": rj.get("fail_count"),
            "REAL_APP_X0_OPEN": rj.get("REAL_APP_X0_OPEN"),
            "REAL_APP_X1_OPEN": rj.get("REAL_APP_X1_OPEN"),
            "REAL_APP_X2_OPEN": rj.get("REAL_APP_X2_OPEN"),
        },
        "claim_boundary": (
            "Phase XI earned tokens remain VALID_AS_BEHAVIORAL_HARNESS. "
            "REAL_*_DAY_DIGITAL_PASS for product readiness requires Phase XII L4/L5+ "
            "actual application execution on the RJ acceptance set."
        ),
    }
    out = root / "artifacts" / "phase_xii" / "PHASE_XI_CLAIM_RESCOPE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(scope, indent=2) + "\n", encoding="utf-8")
    # Update JOURNEY_TOKENS with scope metadata (do not erase historical earned list)
    scoped_tokens = {
        "schema": "gunnchos.phase_xii_tokens.v1",
        "phase_xi_historical": xi,
        "phase_xii_scope": scope,
        "earned_behavioral_harness": xi.get("earned") or [],
        "earned_real_app": [t for t in REAL_DAY_TOKENS if rj.get(t) is True],
        "digital_release_lock_complete_behavioral": True,
        "digital_release_lock_complete_real_app": all(rj.get(t) is True for t in REAL_DAY_TOKENS[:4]) if rj else False,
        "claim_boundary": scope["claim_boundary"],
    }
    (root / "artifacts" / "phase_xii" / "JOURNEY_TOKENS.json").write_text(json.dumps(scoped_tokens, indent=2) + "\n", encoding="utf-8")
    return scope
