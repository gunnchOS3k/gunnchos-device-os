#!/usr/bin/env python3
"""Build REALITY_DEPTH_LEDGER.json for all 79 Phase XI journeys."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.phase_xii.depth import classify_action, journey_min_depth, depth_rank  # noqa: E402


def main() -> int:
    journeys_dir = ROOT / "user_journeys" / "journeys"
    entries = []
    for path in sorted(journeys_dir.glob("J-*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        steps = data.get("steps") or []
        step_depths = [
            {
                "id": s.get("id"),
                "action": s.get("action"),
                "phase_xi_depth": classify_action(s.get("action", ""), phase="xi"),
                "phase_xii_target_depth": classify_action(s.get("action", ""), phase="xii"),
            }
            for s in steps
        ]
        xi_min = journey_min_depth(steps, phase="xi")
        xii_min = journey_min_depth(steps, phase="xii")
        key_below_l4 = [
            sd for sd in step_depths
            if sd["action"] in {
                "browser", "lms_open", "doc_edit", "docx_edit", "email", "message_send",
                "game_launch", "ai_tutor", "webrtc_call", "waike_open", "beatlink_launch",
            }
            and depth_rank(sd["phase_xi_depth"]) < 4
        ]
        entries.append(
            {
                "journey_id": data.get("id") or path.stem,
                "class": data.get("class"),
                "goal": data.get("goal"),
                "step_count": len(steps),
                "phase_xi_min_key_depth": xi_min,
                "phase_xii_target_min_key_depth": xii_min,
                "phase_xi_key_steps_below_l4": len(key_below_l4),
                "VALID_AS_BEHAVIORAL_HARNESS": True,
                "NOT_YET_REAL_APP_PROVEN": len(key_below_l4) > 0 or depth_rank(xi_min) < 4,
                "steps": step_depths,
            }
        )
    counts_xi = Counter(e["phase_xi_min_key_depth"] for e in entries)
    counts_xii = Counter(e["phase_xii_target_min_key_depth"] for e in entries)
    ledger = {
        "schema": "gunnchos.reality_depth_ledger.v1",
        "phase": "XII",
        "journey_count": len(entries),
        "phase_xi_depth_histogram": dict(counts_xi),
        "phase_xii_target_depth_histogram": dict(counts_xii),
        "journeys_not_yet_real_app_proven": sum(1 for e in entries if e["NOT_YET_REAL_APP_PROVEN"]),
        "journeys": entries,
        "claim_correction": {
            "PHASE_XI_BEHAVIORAL_JOURNEY_HARNESS_PASS": True,
            "PHASE_XI_REAL_APPLICATION_DAY_PROOF": "NOT_YET_PROVEN",
        },
    }
    out = ROOT / "artifacts" / "phase_xii" / "REALITY_DEPTH_LEDGER.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    # also field-kit copy path hint
    print(json.dumps({"wrote": str(out), "journeys": len(entries), "not_yet_real": ledger["journeys_not_yet_real_app_proven"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
