#!/usr/bin/env python3
"""CLI entrypoint: guest-native Debian cloud-init provisioner for the
gunnchOS Device Lab Interactive Development Guest.

Thin wrapper around
`gunnchos_device_os.device_lab.debian_cloud_provisioner`. See that module's
docstring for the Alpine-vs-Debian evaluation and the honesty contract.

Usage:
    python3 scripts/provision_interactive_guest_debian_cloud.py [--dry-run-download-only]

Exit codes:
    0  provisioning succeeded (packages installed, guest reported readiness, clean poweroff)
    1  honest failure — see INTERACTIVE_GUEST_PROVISION_EVIDENCE.json for the reason
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from gunnchos_device_os.device_lab.debian_cloud_provisioner import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
