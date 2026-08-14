#!/usr/bin/env python3
"""Import accepted WAIKE #43 owner ingest into a signed device-os package store.

Does not re-author curriculum. Owner remains waike-research-ops.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from gunnchos_device_os.product_use.waike_owner_package import WaikeOwnerPackageStore


def _git_head(path: Path) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--owner-root",
        type=Path,
        default=ROOT.parent / "waike-research-ops",
        help="Path to waike-research-ops checkout (accepted main / #43)",
    )
    ap.add_argument("--version", default=None, help="Optional package version label")
    args = ap.parse_args()
    store = WaikeOwnerPackageStore(ROOT)
    result = store.import_owner(
        args.owner_root,
        owner_commit=_git_head(args.owner_root),
        package_version=args.version,
    )
    # Smoke: learner must not see teacher keys; teacher must.
    learner = store.view("learner")
    teacher = store.view("teacher")
    result["learner_view_ok"] = bool(learner.get("ok"))
    result["teacher_view_ok"] = bool(teacher.get("ok"))
    result["teacher_has_answer_keys"] = "answer_keys" in json.dumps(teacher.get("doc") or {})
    result["learner_has_answer_keys"] = "answer_keys" in json.dumps(learner.get("doc") or {})
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("ok") and result["learner_view_ok"] and not result["learner_has_answer_keys"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
