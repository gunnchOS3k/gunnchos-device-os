#!/usr/bin/env python3
"""Generate CycloneDX SBOM + provenance for the cloud DEV plane."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.cloud_dev_plane.provenance import write_artifacts  # noqa: E402


def main() -> None:
    out = ROOT / "results" / "cloud_dev_plane"
    paths = write_artifacts(out)
    print(json.dumps(paths, indent=2))


if __name__ == "__main__":
    main()
