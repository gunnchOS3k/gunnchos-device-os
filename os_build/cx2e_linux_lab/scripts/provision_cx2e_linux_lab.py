#!/usr/bin/env python3
"""CX2E Linux lab provisioner entrypoint."""
from __future__ import annotations
import sys
from pathlib import Path
_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))
from gunnchos_device_os.cx2e.cli import main
if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:] or ["--full-lifecycle"]))
