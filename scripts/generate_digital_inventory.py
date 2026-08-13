#!/usr/bin/env python3
"""Generate SBOM/HBOM/AI-BOM digital inventory. Unknown provenance is blocking."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.digital_inventory.bom import write_inventory  # noqa: E402


def main() -> int:
    dest = ROOT / "results" / "digital_inventory"
    inventory = write_inventory(ROOT, dest)
    print(
        json.dumps(
            {
                "ok": True,
                "UNKNOWN_RELEASE_BLOCKING": inventory["UNKNOWN_RELEASE_BLOCKING"],
                "counts": inventory["counts"],
                "legal_approval": inventory["legal_approval"],
                "dest": str(dest),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
