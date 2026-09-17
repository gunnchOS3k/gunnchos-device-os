"""Automated accessibility audit — does not claim human a11y completion."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List


SURFACES = [
    "WalletSurface.tsx",
    "PortfolioSurface.tsx",
    "CareerProfileSurface.tsx",
    "VerifierSurface.tsx",
    "EducationTimelineSurface.tsx",
    "SkillEvidenceGraphSurface.tsx",
]


def _check_surface(path: Path) -> Dict[str, Any]:
    if not path.is_file():
        return {"ok": False, "missing": True, "path": str(path)}
    text = path.read_text(errors="ignore")
    checks = {
        "has_main_or_role": bool(re.search(r'role=["\']main["\']|aria-label=|<main\b', text)),
        "has_accessible_name_pattern": bool(
            re.search(r"aria-label=|aria-labelledby=|<h1\b|htmlFor=", text)
        ),
        "keyboard_hint": bool(re.search(r"onKeyDown|tabIndex|button|href=", text, re.I)),
        "focus_order_landmark": bool(re.search(r"<nav\b|<main\b|<header\b|role=", text)),
        "no_positive_human_claim": "HUMAN_VALIDATION_PENDING" in text or "human validation" in text.lower() or True,
    }
    # Must not claim human a11y complete
    if re.search(r"accessibility.?complete|WCAG.?AAA.?pass|human.?a11y.?pass", text, re.I):
        checks["no_positive_human_claim"] = False
    ok = all(checks.values()) and checks["no_positive_human_claim"]
    return {"ok": ok, "checks": checks, "path": str(path.name)}


def run_automated_a11y(repo: Path) -> Dict[str, Any]:
    surf_dir = repo / "apps" / "gunnch_shell" / "src" / "surfaces"
    results: List[Dict[str, Any]] = []
    for name in SURFACES:
        results.append(_check_surface(surf_dir / name))

    # Also require export/share surfaces covered via Career/Verifier
    export_covered = any(r["path"] == "CareerProfileSurface.tsx" and r.get("ok") for r in results)
    verifier_covered = any(r["path"] == "VerifierSurface.tsx" and r.get("ok") for r in results)

    all_ok = all(r.get("ok") for r in results) and export_covered and verifier_covered
    return {
        "schema": "gunnchos.cx3_3.automated_a11y.v1",
        "CX3_AUTOMATED_A11Y_PASS": all_ok,
        "J6_CLASS": "HUMAN_VALIDATION_PENDING",
        "human_validation_pending": True,
        "surfaces": results,
        "scope": [
            "keyboard_navigation",
            "focus_order",
            "accessible_names",
            "Wallet",
            "Portfolio",
            "Career Profile",
            "share/export",
            "verifier",
            "education timeline",
            "skill evidence graph",
        ],
        "certification_claimed": False,
        "notes": "Automated structural checks only — human accessibility study remains pending.",
    }
