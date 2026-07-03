#!/usr/bin/env python3
"""Verify a signed release manifest (development keys only)."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PUB = ROOT / "security" / "secure_boot" / "dev_keys" / "image_signing_dev.pub.pem"


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def verify_manifest(signed_path: Path, pub_path: Path) -> None:
    signed = json.loads(signed_path.read_text(encoding="utf-8"))
    signing = signed.get("signing")
    if not signing:
        raise ValueError("Missing signing block")

    manifest = {k: v for k, v in signed.items() if k != "signing"}
    digest = hashlib.sha256(canonical_json(manifest)).digest()
    if digest.hex() != signing.get("manifest_sha256"):
        raise ValueError("Manifest digest mismatch — file tampered after signing")

    signature = base64.b64decode(signing["signature_b64"])
    digest_file = signed_path.with_suffix(".verify.digest.bin")
    sig_file = signed_path.with_suffix(".verify.sig")
    digest_file.write_bytes(digest)
    sig_file.write_bytes(signature)
    try:
        result = subprocess.run(
            [
                "openssl",
                "pkeyutl",
                "-verify",
                "-pubin",
                "-inkey",
                str(pub_path),
                "-in",
                str(digest_file),
                "-sigfile",
                str(sig_file),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            raise ValueError("Invalid signature")
    finally:
        digest_file.unlink(missing_ok=True)
        sig_file.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify signed release manifest")
    parser.add_argument("signed_manifest", type=Path)
    parser.add_argument("--pub", type=Path, default=DEFAULT_PUB)
    args = parser.parse_args()

    signed_path = args.signed_manifest if args.signed_manifest.is_absolute() else ROOT / args.signed_manifest
    pub_path = args.pub if args.pub.is_absolute() else ROOT / args.pub
    if not pub_path.exists():
        print(f"Missing public key {pub_path}", file=sys.stderr)
        return 1

    try:
        verify_manifest(signed_path, pub_path)
    except ValueError as exc:
        print(f"VERIFY FAILED: {exc}", file=sys.stderr)
        return 1

    print("Manifest signature valid (dev key).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
