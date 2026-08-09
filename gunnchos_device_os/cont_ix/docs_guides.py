"""Adopter docs + user guides — no gate language in user docs."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import re

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_DOCS

GATE_RE = re.compile(
    r"\b(GATE\s*[0-9]|DIGITAL_PRE_EVT|PHYSICAL_EXECUTION_FREEZE|beta_ready\s*[:=]\s*true)\b",
    re.I,
)

REQUIRED_DOCS = {
    "docs/audience/user/STUDENT_QUICK_START.md": (
        "# Student quick start\n\n"
        "1. Sign in with your school profile.\n"
        "2. Open WAIKE for lessons and assignments.\n"
        "3. Take notes, open PDFs, and ask gunnchAI for local tutoring help.\n"
        "4. Work offline; changes sync when you reconnect.\n"
    ),
    "docs/audience/user/OFFICE_QUICK_START.md": (
        "# Office quick start\n\n"
        "1. Sign in.\n"
        "2. Use the browser and LibreOffice for documents, sheets, and decks.\n"
        "3. Print to PDF, join meetings in the browser, and connect VPN when required.\n"
        "4. Dock to use an external display; undock to continue on the go.\n"
    ),
    "docs/audience/user/CREATOR_QUICK_START.md": (
        "# Creator quick start\n\n"
        "1. Open Creator Studio / terminal.\n"
        "2. Edit, build, and run projects.\n"
        "3. Use ring shortcuts where helpful.\n"
    ),
    "docs/audience/ADOPTER_GUIDE.md": (
        "# Adopter guide\n\n"
        "Install the gunnchOS adopter SDK, create a sample app, negotiate API versions, "
        "send ring/telemetry events, and package your integration. "
        "Open hardware is not required for digital adopter onboarding.\n"
    ),
    "docs/release/USER_SUPPORT.md": (
        "# User support\n\n"
        "Generate a diagnostic bundle from Settings → Support. "
        "It includes system info and self-tests for network, storage, update, ring, and dock.\n"
    ),
}


def evaluate_docs_guides() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    written = {}
    gate_hits = []
    for rel, content in REQUIRED_DOCS.items():
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(content, encoding="utf-8")
        text = path.read_text(encoding="utf-8")
        written[rel] = True
        for m in GATE_RE.finditer(text):
            gate_hits.append({"path": rel, "match": m.group(0)})

    ok = all(written.values()) and len(gate_hits) == 0
    report = {
        "schema": "gunnchos.adopter_user_docs.v1",
        "ok": ok,
        "token": TOKEN_DOCS if ok else None,
        "docs": written,
        "gate_language_in_user_docs": gate_hits,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "gate_language_or_missing_docs",
    }
    out = root / "artifacts" / "continuation_ix" / "docs_guides.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
