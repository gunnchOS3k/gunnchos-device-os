#!/usr/bin/env python3
"""Physical boot evidence capture helper (always PENDING)."""
from gunnchos_device_os.boot.cli import main

if __name__ == "__main__":
    raise SystemExit(main(["--physical-capture", "--out", "physical_evidence/gate1/physical_boot_capture.json"]))
