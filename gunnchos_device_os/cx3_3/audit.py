"""CX3.3 next-gate picker."""

from __future__ import annotations

from typing import Any, Dict


def pick_next_gate(tokens_dict: Dict[str, Any]) -> str:
    digital_ok = bool(tokens_dict.get("CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS"))
    waike_ok = bool(tokens_dict.get("CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"))
    if digital_ok and waike_ok:
        return "CX4_COMPLETE_EXPERIENCE_HUMAN_PHYSICAL_EXTERNAL_PLAN"
    if digital_ok and not waike_ok:
        return "CX3_WAIKE_RELEASE_DEPENDENCY_WAIT"
    blocker = tokens_dict.get("lab_blocker") or "DIGITAL_CLOSURE_INCOMPLETE"
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in str(blocker).upper())[:48]
    return f"CX3_3B_{safe}"
