#!/usr/bin/env python3
"""Emit merge recommendation for Golden Journey S0/S1 supporting gates.

Auto-merge is always false. Independent verification is never claimed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.golden_journeys.merge_gate import recommend_merge  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--paths-file", help="Changed paths file")
    p.add_argument("--path", action="append", default=[])
    p.add_argument("--journey", action="append", default=[])
    p.add_argument("--all", action="store_true")
    p.add_argument("--skip-harness", action="store_true")
    args = p.parse_args()

    paths = list(args.path)
    if args.paths_file:
        paths.extend(
            line.strip()
            for line in Path(args.paths_file).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
    journey_ids = list(args.journey) or None
    if args.all:
        journey_ids = [f"GOLDEN-{i:02d}" for i in range(1, 11)]

    report = recommend_merge(
        changed_paths=paths,
        journey_ids=journey_ids,
        run_harness=not args.skip_harness,
        major_pr=True,
    )
    print(json.dumps(report, indent=2, default=str))
    # Exit 1 blocks merge recommendation signal for CI
    return 0 if report["merge_recommended"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
