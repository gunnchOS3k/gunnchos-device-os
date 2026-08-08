#!/usr/bin/env python3
"""Build + optionally boot the gunnchOS bootable reference image."""
from __future__ import annotations

import argparse
import json
import sys

from gunnchos_device_os.bootable_image import BootableReferenceBuilder, QemuBootHarness, build_and_boot


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-only", action="store_true", help="Assemble artifacts without QEMU boot")
    parser.add_argument("--boot-only", action="store_true", help="Boot existing artifacts only")
    parser.add_argument("--no-fetch", action="store_true", help="Do not download Alpine cache")
    parser.add_argument("--timeout", type=float, default=180.0, help="QEMU boot timeout seconds")
    args = parser.parse_args()

    if args.boot_only:
        evidence = QemuBootHarness().boot(timeout_sec=args.timeout)
        print(json.dumps(evidence, indent=2, sort_keys=True))
        return 0 if evidence.get("ok") else 1

    if args.build_only:
        result = BootableReferenceBuilder().build(fetch=not args.no_fetch)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok") else 1

    result = build_and_boot(fetch=not args.no_fetch, timeout_sec=args.timeout)
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
