#!/usr/bin/env python3
"""Generate persona matrix markdown from config."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.persona_engine import get_persona, list_personas


def main() -> int:
    lines = [
        "# Generated Persona Matrix",
        "",
        "| Persona | Primary need | Default mode | Apps/tools | Customization level | Safety/privacy needs | Offline needs | Success moment |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for pid in sorted(list_personas()):
        p = get_persona(pid)
        name = pid.replace("_", " ").title()
        lines.append(
            f"| {name} | {p.get('primary_need', '')} | {p.get('default_journey_preset', '')} | "
            f"{', '.join(p.get('default_apps', [])[:3])} | {p.get('customization_level', '')} | "
            f"{p.get('privacy_level', '')} | {p.get('offline_needs', '')} | {p.get('success_moment', '')} |"
        )
    out = ROOT / "results/generated_persona_matrix.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
