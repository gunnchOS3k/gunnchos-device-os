#!/usr/bin/env python3
"""Privacy/security demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.consent_policy import research_requires_consent, set_consent
from gunnchos_device_os.privacy_security_model import get_profile_defaults, get_telemetry_policy, request_delete, request_export
from gunnchos_device_os.security_event_log import clear_events, log_event


def main() -> int:
    clear_events()
    out = {
        "child_defaults": get_profile_defaults("child"),
        "child_telemetry": get_telemetry_policy("child", "not_asked"),
        "school_telemetry": get_telemetry_policy("school", "local_only"),
        "research_consent_required": research_requires_consent("research", "not_asked"),
        "consent_opt_in": set_consent("demo", "opt_in_aggregate", "adult"),
        "export": request_export("demo"),
        "delete": request_delete("demo"),
        "event_log": log_event("admin_action", {"action": "mode_change", "message_content": "secret"}),
        "claim_boundary": "Privacy/security model alpha — not certified compliance",
        "legal_approval": "HUMAN/EXTERNAL",
        "mock": False,
    }
    dest = ROOT / "results/privacy_security_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
