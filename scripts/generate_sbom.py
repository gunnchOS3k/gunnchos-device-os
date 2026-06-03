#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from security.sbom import generate_spdx  # noqa: E402


def main() -> None:
    out = ROOT / "results/sbom"
    out.mkdir(parents=True, exist_ok=True)
    generate_spdx(out / "gunnchos_device_os.spdx.json")
    cyclone = {"bomFormat": "CycloneDX", "specVersion": "1.4", "components": []}
    (out / "gunnchos_device_os.cyclonedx.json").write_text(
        json.dumps(cyclone, indent=2) + "\n", encoding="utf-8"
    )
    (out / "sbom_report.md").write_text(
        "# SBOM report\n\nGenerated SPDX/CycloneDX stubs. Vulnerability review placeholder.\n",
        encoding="utf-8",
    )
    print("Generated SBOM")


if __name__ == "__main__":
    main()
