#!/usr/bin/env python3
"""Start PLATFORM-001 companion bridge (HTML shells ↔ gunnchSDK sandbox I/O)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.first_party_apps.companion_bridge import start_bridge  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument(
        "--data-dir",
        default=str(ROOT / ".gunnchos_companion_sandbox"),
        help="Sandbox data dir shared with first_party run_* paths",
    )
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCHOS_SANDBOX_DATA_DIR"] = str(data_dir)
    os.environ.setdefault(
        "GUNNCHOS_APP_PERMISSIONS",
        "storage_read,storage_write,ai_interface",
    )
    server, base = start_bridge(ROOT, data_dir, host=args.host, port=args.port)
    print(
        f"companion_bridge listening at {base}\n"
        f"  creator:   {base}/apps/creator_studio/\n"
        f"  waike:     {base}/apps/waike_learning/\n"
        f"  gunnchai:  {base}/apps/gunnchai_tutor/\n"
        f"  health:    {base}/api/health\n"
        f"  sandbox:   {data_dir}",
        flush=True,
    )
    try:
        # start_bridge already serves in a daemon thread; park the main thread.
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\nshutting down companion_bridge", flush=True)
    finally:
        server.shutdown()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
