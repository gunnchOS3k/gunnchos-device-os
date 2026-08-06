#!/usr/bin/env python3
"""Physical dock evidence capture helper (always PENDING)."""
from gunnchos_device_os.dock.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["--physical-template", "--out", "physical_evidence/gate1/physical_dock_capture.json"]))
