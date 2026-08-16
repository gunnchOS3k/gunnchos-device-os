#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

from research_pipeline import run_experiment


def main() -> int:
    root = Path(__file__).resolve().parent
    mutate = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_experiment(root, root / "out", mutate=mutate)
    print(json.dumps({"ok": result.get("ok"), "sha": result.get("artifact_sha256"), "build_system": result.get("build_system")}))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
