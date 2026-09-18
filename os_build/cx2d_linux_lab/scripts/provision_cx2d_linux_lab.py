#!/usr/bin/env python3
"""CX2D Linux lab provisioner — isolated from Device Lab #134 evidence."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from gunnchos_device_os.cx2d.lab import (  # noqa: E402
    attempt_lab_status,
    build_provenance,
    prepare_cx2d_overlay,
    write_cloud_init_payload,
    ensure_lab_tree,
)


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--prepare-only", action="store_true", help="Overlay+cloud-init only; no long QEMU provision")
    p.add_argument("--repo", type=Path, default=_REPO)
    args = p.parse_args(argv)
    lab = ensure_lab_tree(args.repo)
    write_cloud_init_payload(lab)
    overlay = prepare_cx2d_overlay(args.repo)
    status = attempt_lab_status(args.repo)
    prov = build_provenance(args.repo, status)
    print("overlay_ok=", overlay.get("ok"), "blocker=", status.get("blocker"))
    print("provenance=", prov.get("image_base_sha256"))
    if args.prepare_only:
        return 0 if overlay.get("ok") or status.get("blocker") else 1
    # Full QEMU cloud-init provision intentionally not auto-run in agent CI:
    # long-running and host-dependent. Scaffolding + prepare-only is the
    # reproducible entry; CX2E completes guest GUI proof.
    print("FULL_PROVISION_NOT_RUN: use prepare-only; see CX2D_LINUX_LAB_STATUS.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
