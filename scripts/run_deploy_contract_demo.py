#!/usr/bin/env python3
"""Deploy contract demo."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.deploy_contract import deploy_package, get_transport_policy, list_deploy_targets


def main() -> int:
    out = {
        "targets": list_deploy_targets(),
        "success_wifi": deploy_package("ds_xl_coder", "student_14_5", "python_project", "local_wifi", user_consent=True, guardian_approved=True),
        "blocked_no_consent": deploy_package("ds_xl_coder", "handheld_hybrid", "game_project", "local_wifi"),
        "blocked_package": deploy_package("ds_xl_coder", "classroom_library_shared", "game_project", "local_wifi", user_consent=True, guardian_approved=True),
        "usb_c_policy": get_transport_policy("usb_c"),
        "claim_boundary": "Deploy contract alpha — not production fleet deploy",
        "mock": True,
    }
    dest = ROOT / "results/ds_xl_deploy_demo_output.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
