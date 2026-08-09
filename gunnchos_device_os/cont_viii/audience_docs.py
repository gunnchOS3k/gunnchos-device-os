"""Audience documentation presence checks (Lane I)."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import re

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_AUDIENCE_DOCS_PASS

GUIDES = (
    "MANUFACTURER_GUIDE.md",
    "INTEGRATOR_GUIDE.md",
    "ADOPTER_GUIDE.md",
    "FACTORY_GUIDE.md",
    "IT_ADMIN_GUIDE.md",
    "ACCESSIBILITY_GUIDE.md",
    "OFFLINE_GUIDE.md",
    "NETWORKING_GUIDE.md",
    "SECURITY_GUIDE.md",
)

USER_DOCS = (
    "STUDENT_QUICK_START.md",
    "OFFICE_QUICK_START.md",
    "CREATOR_QUICK_START.md",
)

INTERNAL_GATE_RE = re.compile(
    r"\b(P0 blocker|beta_ready|SCHEMA_ONLY|gate[- ]?[0-9]|INTERNAL ONLY|do not ship)\b",
    re.I,
)


def evaluate_audience_docs(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    audience = root / "docs/audience"
    user = audience / "user"
    present = {}
    for name in GUIDES:
        p = audience / name
        present[name] = p.exists() and p.stat().st_size > 100
    for name in USER_DOCS:
        p = user / name
        present[f"user/{name}"] = p.exists() and p.stat().st_size > 80

    gate_leaks = []
    for name in USER_DOCS:
        p = user / name
        if not p.exists():
            continue
        text = p.read_text(encoding="utf-8")
        for m in INTERNAL_GATE_RE.finditer(text):
            gate_leaks.append({"doc": f"user/{name}", "match": m.group(0)})

    ok = all(present.values()) and len(gate_leaks) == 0
    return {
        "schema": "gunnchos.audience_docs.v1",
        "ok": ok,
        "token": TOKEN_AUDIENCE_DOCS_PASS if ok else None,
        "present": present,
        "gate_language_in_user_docs": gate_leaks,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
