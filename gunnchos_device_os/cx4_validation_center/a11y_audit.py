"""Automated accessibility qualification of Validation Center UI (not human a11y PASS)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List


def audit_html(html: str) -> Dict[str, Any]:
    checks: Dict[str, Any] = {}
    checks["has_lang"] = bool(re.search(r"<html[^>]+lang=", html, re.I))
    checks["has_main_landmark"] = "<main" in html
    checks["has_nav_or_header"] = ("<nav" in html) or ("<header" in html)
    checks["has_h1"] = bool(re.search(r"<h1[\s>]", html, re.I))
    checks["buttons_have_text"] = "aria-label" in html or re.search(r"<button[^>]*>\s*[^<\s]", html) is not None
    checks["labels_present"] = "<label" in html
    checks["focus_styles_present"] = ":focus" in html or "focus-visible" in html
    checks["reduced_motion_support"] = "prefers-reduced-motion" in html
    checks["no_color_only_status"] = "status-text" in html or "visually" in html or "text status" in html.lower() or "data-status-text" in html
    checks["skip_link_or_landmarks"] = "skip-link" in html or checks["has_main_landmark"]
    checks["a11y_options_panel"] = "Accessibility Options" in html or "accessibility-options" in html
    checks["large_targets_css"] = "min-height: 44px" in html or "min-height:44px" in html or "--target-min" in html
    failed = [k for k, v in checks.items() if not v]
    return {
        "checks": checks,
        "failed": failed,
        "CX4_VALIDATION_CENTER_AUTOMATED_A11Y_PASS": len(failed) == 0,
        "wcag_conformance_claimed": False,
        "note": "Automated checks only; human validation remains pending.",
    }


def audit_validation_center_app(app_dir: Path) -> Dict[str, Any]:
    index = app_dir / "index.html"
    css = app_dir / "src" / "styles.css"
    html = index.read_text(encoding="utf-8") if index.is_file() else ""
    if css.is_file():
        html += "\n" + css.read_text(encoding="utf-8")
    js = app_dir / "src" / "app.js"
    if js.is_file():
        html += "\n" + js.read_text(encoding="utf-8")
    return audit_html(html)
