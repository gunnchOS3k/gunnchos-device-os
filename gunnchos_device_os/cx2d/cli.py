"""CX2D CLI — generate lab status + fail-closed evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from gunnchos_device_os.cx2d.evidence import write_evidence
from gunnchos_device_os.cx2d.lab import repo_root_from_here


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2d")
    parser.add_argument("--repo", type=Path, default=None)
    args = parser.parse_args(argv)
    repo = args.repo or repo_root_from_here()
    report = write_evidence(repo)
    print(report["NEXT_CX_GATE"])
    print("FULL_COMPLETE_EXPERIENCE_COMPLETE=", report["FULL_COMPLETE_EXPERIENCE_COMPLETE"])
    print("blocker=", report["linux_lab"].get("blocker", "")[:200])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
