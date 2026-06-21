#!/usr/bin/env python3
"""Mode policy demo output."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.consent_policy import set_consent
from gunnchos_device_os.mode_manager import get_mode_policy, list_modes
from gunnchos_device_os.mode_policy import can_transition, research_mode_policy


def main() -> int:
    out = {
        "modes": list(list_modes()),
        "school": get_mode_policy("School"),
        "developer": get_mode_policy("Developer"),
        "research": get_mode_policy("Research Measurement"),
        "transitions": {
            "child_to_developer_blocked": can_transition("School", "Developer", profile_type="child"),
            "child_to_developer_approved": can_transition("School", "Developer", profile_type="child", guardian_approved=True),
            "school_to_admin_blocked": can_transition("School", "Admin", consent_given=False),
            "research_consent": can_transition("School", "Research Measurement", consent_given=False),
        },
        "research_policy": research_mode_policy(),
        "consent": set_consent("demo-user", "opt_in_research", "research"),
        "claim_boundary": "Prototype mode manager — not shipping OS",
        "mock": True,
    }
    dest = ROOT / "results/mode_policy_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
