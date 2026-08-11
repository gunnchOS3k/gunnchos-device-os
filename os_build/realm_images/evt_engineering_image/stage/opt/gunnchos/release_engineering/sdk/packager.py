"""`.gunnchpkg` package format: build + sign an app directory into a real
zip archive (manifest + payload + package manifest + DEV/TEST signature)."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys
from gunnchos_device_os.release_engineering.sdk.manifest import MANIFEST_SCHEMA, validate_manifest

PACKAGE_SCHEMA = "gunnchos.sdk.gunnchpkg.v1"
PACKAGE_EXT = ".gunnchpkg"

_IGNORE_DIRS = {"__pycache__", ".pytest_cache", ".git"}


def _iter_payload_files(app_dir: Path) -> list[Path]:
    files = []
    for p in sorted(app_dir.rglob("*")):
        if p.is_dir():
            continue
        if any(part in _IGNORE_DIRS for part in p.parts):
            continue
        if p.name == "manifest.json":
            continue
        files.append(p)
    return files


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageError(RuntimeError):
    pass


class PackageBuilder:
    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root)

    def build(self, app_dir: Path, out_dir: Path, *, sign: bool = True) -> dict[str, Any]:
        app_dir = Path(app_dir)
        manifest_path = app_dir / "manifest.json"
        if not manifest_path.exists():
            raise PackageError(f"manifest_missing:{manifest_path}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        failures = validate_manifest(manifest)
        if failures:
            raise PackageError(f"manifest_invalid:{failures}")

        payload_files = _iter_payload_files(app_dir)
        if not payload_files:
            raise PackageError("no_payload_files")

        file_entries = []
        for f in payload_files:
            rel = str(f.relative_to(app_dir))
            data = f.read_bytes()
            file_entries.append({"path": rel, "sha256": _sha256_bytes(data), "size_bytes": len(data)})

        digest_source = "".join(f"{e['path']}:{e['sha256']}" for e in sorted(file_entries, key=lambda e: e["path"]))
        package_digest = _sha256_bytes(digest_source.encode("utf-8"))

        package_manifest = {
            "schema": PACKAGE_SCHEMA,
            "app_id": manifest["app_id"],
            "version": manifest["version"],
            "files": file_entries,
            "package_digest": package_digest,
        }

        signature: dict[str, Any] | None = None
        if sign:
            sig_hex = dev_keys.sign_bytes(self.repo_root, package_digest.encode("utf-8"))
            signature = {
                "algorithm": "Ed25519",
                "signature_hex": sig_hex,
                "public_key_fingerprint": dev_keys.dev_public_key_fingerprint(self.repo_root),
                "signing_tier": "DEV_TEST",
                "claim_boundary": dev_keys.CLAIM_BOUNDARY,
            }

        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        pkg_path = out_dir / f"{manifest['app_id']}-{manifest['version']}{PACKAGE_EXT}"
        if pkg_path.exists():
            pkg_path.unlink()

        with zipfile.ZipFile(pkg_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
            zf.writestr("PACKAGE_MANIFEST.json", json.dumps(package_manifest, indent=2, sort_keys=True))
            zf.writestr("SIGNATURE.json", json.dumps(signature, indent=2, sort_keys=True))
            for f in payload_files:
                rel = str(f.relative_to(app_dir))
                zf.write(f, arcname=f"payload/{rel}")

        return {
            "ok": True,
            "package_path": str(pkg_path),
            "app_id": manifest["app_id"],
            "version": manifest["version"],
            "package_digest": package_digest,
            "signed": sign,
            "file_count": len(file_entries),
            "schema": MANIFEST_SCHEMA,
        }
