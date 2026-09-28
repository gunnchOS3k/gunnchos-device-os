#!/usr/bin/env python3
"""Write honest convergence artifacts from the continuity module."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_launcher.mlv_continuity import (
    INTENT_VERSION,
    build_journey_matrix,
    convergence_gates,
)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "integration"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    matrix = build_journey_matrix()
    gates = {
        "kind": "mlv_waike_7gc_airan_convergence_gates",
        "intent_version": INTENT_VERSION,
        "base": "integration/3k-mlv-world-workspace-v1",
        "base_head": "64ce5930024b246f0ac49d7d704c82560fec7f31",
        "claim_boundary": (
            "Local gunnchOS shell/intent/return-continuity tests only. "
            "Not hosted journey, not Pixel, not physical RIC, not merge."
        ),
        "gates": convergence_gates(),
    }
    (OUT / "MLV_WAIKE_7GC_AIRAN_JOURNEY_MATRIX.json").write_text(
        json.dumps(matrix, indent=2) + "\n",
        encoding="utf-8",
    )
    (OUT / "MLV_WAIKE_7GC_AIRAN_CONVERGENCE_GATES.json").write_text(
        json.dumps(gates, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
