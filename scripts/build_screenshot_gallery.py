#!/usr/bin/env python3
"""Assemble Phase XII screenshot gallery index from evidence (real windows only)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "phase_xii"
GALLERY = ART / "gallery"


def main() -> int:
    GALLERY.mkdir(parents=True, exist_ok=True)
    shots = sorted(ART.rglob("*.png"))
    # copy/index only; do not generate concept art
    index = []
    for s in shots:
        rel = str(s.relative_to(ART))
        index.append({"path": rel, "bytes": s.stat().st_size, "source": "real_capture"})
    meta = {
        "schema": "gunnchos.phase_xii.screenshot_gallery.v1",
        "count": len(index),
        "items": index,
        "concept_art_forbidden": True,
        "note": "Gallery indexes only files produced by Weston/Playwright/app captures",
    }
    (GALLERY / "INDEX.json").write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    (GALLERY / "README.md").write_text(
        "# Phase XII Screenshot Gallery\\n\\nReal captures only. No generated concept art.\\n",
        encoding="utf-8",
    )
    print(json.dumps({"screenshots": len(index)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
