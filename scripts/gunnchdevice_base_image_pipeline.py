#!/usr/bin/env python3
"""CLI for GUNNCHDEVICE_BASE_IMAGE_PIPELINE.

Examples:
  python3 scripts/gunnchdevice_base_image_pipeline.py status
  python3 scripts/gunnchdevice_base_image_pipeline.py seal
  python3 scripts/gunnchdevice_base_image_pipeline.py overlay --persona G11
  python3 scripts/gunnchdevice_base_image_pipeline.py discard-overlay --persona G11
  python3 scripts/gunnchdevice_base_image_pipeline.py safe-halt --reason leaving_now
  python3 scripts/gunnchdevice_base_image_pipeline.py safe-resume

Operator leave-now: prefer `make safe-halt-guest` (see docs).
Never: hard-kill QEMU, delete sealed base, force-push, reset --hard.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.base_image_pipeline import (  # noqa: E402
    create_cow_overlay,
    discard_overlay,
    pipeline_status,
    resolve_boot_disk,
    safe_halt,
    safe_resume,
    seal_base_image,
)


def _print(doc: dict) -> int:
    print(json.dumps(doc, indent=2, default=str))
    if doc.get("ok") is False or doc.get("blocked"):
        return 1
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="GUNNCHDEVICE_BASE_IMAGE_PIPELINE")
    p.add_argument("--arch", default="aarch64")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show pipeline / seal / overlay status")
    sub.add_parser("seal", help="Seal base image after sentinel PASS (immutable)")
    ov = sub.add_parser("overlay", help="Create/reuse regenerable COW overlay")
    ov.add_argument("--persona", default="session")
    ov.add_argument("--force", action="store_true")
    disc = sub.add_parser("discard-overlay", help="Discard REGENERABLE overlay only")
    disc.add_argument("--persona", required=True)
    halt = sub.add_parser("safe-halt", help="Operator leave-now halt (no SIGKILL)")
    halt.add_argument("--reason", default="operator_leaving")
    halt.add_argument("--qemu-pid", type=int, default=None)
    sub.add_parser("safe-resume", help="Compute SAFE_RESUME decision")
    sub.add_parser("resolve-boot-disk", help="Resolve COW overlay path for QEMU boot")

    args = p.parse_args(argv)
    if args.cmd == "status":
        return _print(pipeline_status(ROOT, arch=args.arch))
    if args.cmd == "seal":
        return _print(seal_base_image(ROOT, arch=args.arch))
    if args.cmd == "overlay":
        return _print(create_cow_overlay(ROOT, persona=args.persona, arch=args.arch, force=args.force))
    if args.cmd == "discard-overlay":
        return _print(discard_overlay(ROOT, persona=args.persona, arch=args.arch))
    if args.cmd == "safe-halt":
        return _print(safe_halt(ROOT, reason=args.reason, qemu_pid=args.qemu_pid))
    if args.cmd == "safe-resume":
        return _print(safe_resume(ROOT))
    if args.cmd == "resolve-boot-disk":
        return _print(resolve_boot_disk(ROOT, arch=args.arch))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
