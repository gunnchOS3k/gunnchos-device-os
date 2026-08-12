#!/usr/bin/env python3
"""Emit artifacts/handheld_image_fit/IMAGE_FIT_MANIFEST.json from measured realm images."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from gunnchos_device_os.release_engineering.handheld_image_fit import (  # noqa: E402
    write_handheld_image_fit_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output path (default: artifacts/handheld_image_fit/IMAGE_FIT_MANIFEST.json)",
    )
    args = parser.parse_args()
    manifest = write_handheld_image_fit_manifest(REPO_ROOT, out_path=args.out)
    print(json.dumps(
        {
            "ok": True,
            "written_to": manifest.get("_written_to"),
            "device_os_tip": manifest.get("device_os_tip"),
            "PRODUCTION_RELEASE_CLAIMED": manifest.get("PRODUCTION_RELEASE_CLAIMED"),
            "npi_recommended_status": (manifest.get("npi") or {}).get("recommended_status"),
            "closure_gate_met": (manifest.get("npi") or {}).get("closure_gate_met"),
            "sizes_summary_gib": manifest.get("sizes_summary_gib"),
            "production_image_fit_verdict": (manifest.get("fit_assessment") or {}).get(
                "production_image_fit_verdict"
            ),
        },
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
