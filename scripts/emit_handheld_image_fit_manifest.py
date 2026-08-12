#!/usr/bin/env python3
"""Emit artifacts/handheld_image_fit/IMAGE_FIT_MANIFEST.json from measured realm images."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from gunnchos_device_os.release_engineering.handheld_image_fit import (  # noqa: E402
    write_handheld_image_fit_manifest,
)

MAIN_TIP_DEFAULT = "3858e760295ad35828ff141919681f2bb8685cf0"


def _git_head() -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        return out.stdout.strip() or None
    except Exception:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Optional output path (default: artifacts/handheld_image_fit/IMAGE_FIT_MANIFEST.json)",
    )
    parser.add_argument(
        "--measured-against-main-tip",
        default=MAIN_TIP_DEFAULT,
        help="Accepted main tip this DRAFT measures against",
    )
    args = parser.parse_args()
    manifest = write_handheld_image_fit_manifest(REPO_ROOT, out_path=args.out)
    out = Path(
        args.out or (REPO_ROOT / "artifacts" / "handheld_image_fit" / "IMAGE_FIT_MANIFEST.json")
    )
    # Re-read and stamp non-volatile evidence metadata used by hardware remodel.
    data = json.loads(out.read_text(encoding="utf-8"))
    data["measured_against_main_tip"] = args.measured_against_main_tip
    data["device_os_tip"] = _git_head()
    data["evidence_note"] = (
        "Production-intent digital rootfs rebuilt from Alpine minirootfs + gunnchOS "
        "userspace on DRAFT #107. A/B slots measured from unsigned "
        "PRODUCTION_SHIPPING_IMAGE_DEFINITION; recovery from RECOVERY_IMAGE. "
        "SHIPPING_IMAGE=false; PRODUCTION_RELEASE_CLAIMED=false."
    )
    out.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": True,
                "written_to": str(out.relative_to(REPO_ROOT)),
                "device_os_tip": data.get("device_os_tip"),
                "measured_against_main_tip": data.get("measured_against_main_tip"),
                "PRODUCTION_RELEASE_CLAIMED": data.get("PRODUCTION_RELEASE_CLAIMED"),
                "SHIPPING_IMAGE": data.get("SHIPPING_IMAGE"),
                "npi_recommended_status": (data.get("npi") or {}).get("recommended_status"),
                "closure_gate_met": (data.get("npi") or {}).get("closure_gate_met"),
                "sizes_summary_gib": data.get("sizes_summary_gib"),
                "production_image_fit_verdict": (data.get("fit_assessment") or {}).get(
                    "production_image_fit_verdict"
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
