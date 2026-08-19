#!/usr/bin/env python3
"""Optional sibling verification for gunnchAI ACCEPTED_MAIN contract pin."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.cross_repo_gunnchai.contract import (  # noqa: E402
    load_contract,
    validate_contract,
    verify_owner_artifacts,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--device-os-root", type=Path, default=ROOT)
    parser.add_argument("--gunnchai-repo", type=Path, default=None)
    parser.add_argument(
        "--write-evidence",
        type=Path,
        default=ROOT / "artifacts/gunnchai_compat/ACCEPTED_MAIN_EVIDENCE.json",
    )
    args = parser.parse_args()

    validate_contract()
    contract = load_contract()
    result = verify_owner_artifacts(args.device_os_root, args.gunnchai_repo)
    result["device_os_sha"] = contract["device_os"]["accepted_main_sha"]
    result["contract_version"] = contract["contract_version"]

    args.write_evidence.parent.mkdir(parents=True, exist_ok=True)
    args.write_evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")

    print(json.dumps(result, indent=2))
    if args.gunnchai_repo and not result.get("ok"):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
