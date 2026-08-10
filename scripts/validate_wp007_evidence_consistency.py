#!/usr/bin/env python3
"""Fail CI on WP-007 evidence contradictions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.security.wp007.evidence_consistency import (  # noqa: E402
    evaluate_evidence_consistency,
)


def main() -> int:
    report = evaluate_evidence_consistency(ROOT)
    out = ROOT / "artifacts/wp007/EVIDENCE_CONSISTENCY.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
