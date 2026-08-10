#!/usr/bin/env python3
"""Run supporting Golden Journey subset for changed paths or explicit IDs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.golden_journeys.harness import run_supporting_subset  # noqa: E402
from gunnchos_device_os.golden_journeys.path_map import select_journeys_for_paths  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--paths-file", help="File with one changed path per line")
    p.add_argument("--path", action="append", default=[], help="Changed path (repeatable)")
    p.add_argument("--journey", action="append", default=[], help="Explicit GOLDEN-XX id")
    p.add_argument("--all", action="store_true", help="Run all ten Golden Journeys")
    p.add_argument("--json", action="store_true", help="Print full JSON report")
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
        sel = select_journeys_for_paths([], force_all=True)
        journey_ids = sel["selected"]

    report = run_supporting_subset(
        journey_ids,
        changed_paths=paths,
        write_scorecards=True,
        write_report=True,
        major_pr=True,
    )
    if args.json:
        print(json.dumps(report, indent=2, default=str))
    else:
        print(
            json.dumps(
                {
                    "ok": report["ok"],
                    "selected": report["selection"]["selected"],
                    "blocking_s0_s1_failures": report["blocking_s0_s1_failures"],
                    "independent_verification_claimed": False,
                },
                indent=2,
            )
        )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
