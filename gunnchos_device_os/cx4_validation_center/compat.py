"""Browser / device compatibility preflight for Validation Center UI (host-side)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List


def qualify_ui_compatibility(app_dir: Path) -> Dict[str, Any]:
    """
    Qualify against runtimes available in the CX development environment.
    Does not claim browsers that were not actually inspected.
    """
    app_dir = Path(app_dir)
    index = (app_dir / "index.html").read_text(encoding="utf-8") if (app_dir / "index.html").is_file() else ""
    css = (app_dir / "src" / "styles.css").read_text(encoding="utf-8") if (app_dir / "src" / "styles.css").is_file() else ""
    js = (app_dir / "src" / "app.js").read_text(encoding="utf-8") if (app_dir / "src" / "app.js").is_file() else ""
    blob = index + css + js

    checks: Dict[str, bool] = {
        "chromium_family_path": "viewport" in index and "Validation Center" in index,
        "keyboard_only_path": "skip-link" in index and "tabindex" in index and ":focus" in css,
        "responsive_narrow_width": "max-width" in css or "@media" in css or "viewport" in index,
        "text_zoom_200_reflow": "--text-scale" in css or "opt-text-size" in index or "200%" in index,
        "visible_focus": ":focus" in css or "focus-visible" in css,
        "reduced_motion": "reduced-motion" in blob,
        "high_contrast": "high-contrast" in blob,
    }
    tested_runtimes: List[str] = ["chromium-family (markup/CSS static qualification)"]
    untested: List[str] = ["Safari (not claimed)", "Firefox (not claimed)", "iOS Safari (not claimed)"]

    ok = all(checks.values())
    return {
        "CX4_VALIDATION_UI_COMPATIBILITY_PASS": ok,
        "checks": checks,
        "tested_runtimes": tested_runtimes,
        "untested_runtimes_not_claimed": untested,
        "note": "Software/static qualification only; not a WCAG conformance claim.",
    }
