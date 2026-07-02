#!/usr/bin/env python3
"""Validate installable OS image prototype artifacts and honesty boundaries."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ARTIFACT = ROOT / "os_build" / "installable_image" / "artifact"
REQUIRED_MANIFEST_KEYS = (
    "artifact_type",
    "version",
    "build_id",
    "platform",
    "bootable_os_claim",
    "iso_built",
    "hardware_validated",
    "bundle_archive",
)
FORBIDDEN_TRUE_WHEN_NO_BOOT_EVIDENCE = ("bootable_os_claim", "hardware_validated", "iso_built")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT,
        help="Directory containing MANIFEST.json and bundle",
    )
    parser.add_argument(
        "--skip-bundle-check",
        action="store_true",
        help="Skip tarball/checksum validation (used mid-build)",
    )
    return parser.parse_args()


def validate(artifact_dir: Path, *, skip_bundle_check: bool = False) -> list[str]:
    errors: list[str] = []
    manifest_path = artifact_dir / "MANIFEST.json"

    if not manifest_path.exists():
        return [f"Missing manifest: {manifest_path}"]

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return [f"Invalid MANIFEST.json: {exc}"]

    for key in REQUIRED_MANIFEST_KEYS:
        if key not in manifest:
            errors.append(f"MANIFEST.json missing key: {key}")

    if manifest.get("artifact_type") != "installable_os_image_prototype":
        errors.append(
            f"artifact_type must be installable_os_image_prototype, got {manifest.get('artifact_type')!r}"
        )

    for key in FORBIDDEN_TRUE_WHEN_NO_BOOT_EVIDENCE:
        if manifest.get(key) is True:
            errors.append(f"{key} cannot be true without boot validation evidence")

    launcher_index = artifact_dir / "launcher" / "dist" / "index.html"
    if not launcher_index.exists():
        errors.append(f"Missing launcher dist: {launcher_index}")

    install_stub = artifact_dir / "install" / "install_stub.sh"
    if not install_stub.exists():
        errors.append(f"Missing install stub: {install_stub}")

    if skip_bundle_check:
        return errors

    bundle_name = manifest.get("bundle_archive", "gunnchos-installable-image-prototype.tar.gz")
    bundle_path = artifact_dir / str(bundle_name)
    if not bundle_path.exists():
        errors.append(f"Missing bundle archive: {bundle_path}")

    checksums = artifact_dir / "CHECKSUMS.sha256"
    if checksums.exists():
        text = checksums.read_text(encoding="utf-8")
        if bundle_name not in text:
            errors.append(f"CHECKSUMS.sha256 does not include {bundle_name}")
        if "MANIFEST.json" not in text:
            errors.append("CHECKSUMS.sha256 does not include MANIFEST.json")

    return errors


def main() -> int:
    args = parse_args()
    errors = validate(args.artifact_dir, skip_bundle_check=args.skip_bundle_check)
    if errors:
        for err in errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print("installable image artifacts valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
