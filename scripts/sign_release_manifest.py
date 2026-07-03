#!/usr/bin/env python3
"""Sign a release version manifest with development RSA key (prototype only)."""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KEY = ROOT / "security" / "secure_boot" / "dev_keys" / "image_signing_dev.pem"


def canonical_json(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_manifest(manifest_path: Path, key_path: Path, output_path: Path | None) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a JSON object")

    digest = hashlib.sha256(canonical_json(manifest)).digest()
    digest_file = manifest_path.with_suffix(".digest.bin")
    digest_file.write_bytes(digest)
    sig_file = manifest_path.with_suffix(".sig")
    try:
        subprocess.run(
            ["openssl", "pkeyutl", "-sign", "-inkey", str(key_path), "-in", str(digest_file), "-out", str(sig_file)],
            check=True,
            capture_output=True,
        )
        signature = sig_file.read_bytes()
    finally:
        digest_file.unlink(missing_ok=True)
        sig_file.unlink(missing_ok=True)

    signed = {
        **manifest,
        "signing": {
            "algorithm": "RSA-SHA256-digest-sign",
            "key_role": "image_manifest_dev",
            "signed_at": datetime.now(timezone.utc).isoformat(),
            "manifest_sha256": digest.hex(),
            "signature_b64": base64.b64encode(signature).decode("ascii"),
            "claim": "development signing only — not production secure boot",
        },
    }

    out = output_path or manifest_path.with_suffix(".signed.json")
    out.write_text(json.dumps(signed, indent=2) + "\n", encoding="utf-8")
    return signed


def main() -> int:
    parser = argparse.ArgumentParser(description="Sign release manifest (dev keys)")
    parser.add_argument("manifest", type=Path, help="Path to version_manifest.json")
    parser.add_argument("--key", type=Path, default=DEFAULT_KEY)
    parser.add_argument("-o", "--output", type=Path, default=None)
    args = parser.parse_args()

    manifest_path = args.manifest if args.manifest.is_absolute() else ROOT / args.manifest
    key_path = args.key if args.key.is_absolute() else ROOT / args.key
    if not key_path.exists():
        print(f"Missing dev key {key_path}. Run scripts/generate_dev_signing_keys.sh", file=sys.stderr)
        return 1

    signed = sign_manifest(manifest_path, key_path, args.output)
    out = args.output or manifest_path.with_suffix(".signed.json")
    print(f"Signed manifest written to {out}")
    print(f"manifest_sha256={signed['signing']['manifest_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
