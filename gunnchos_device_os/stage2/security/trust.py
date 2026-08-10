"""Verified image, signed update metadata, anti-rollback, app signatures."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.stage2.crypto_dev import (
    sha256_bytes,
    sha256_file,
    sign_payload,
    verify_signature,
)


class TrustChain:
    def __init__(self, state_dir: Path | str):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.sv_path = self.state_dir / "security_version.json"
        if not self.sv_path.exists():
            self.sv_path.write_text(json.dumps({"security_version": 1}) + "\n")

    def security_version(self) -> int:
        return int(json.loads(self.sv_path.read_text())["security_version"])

    def set_security_version(self, sv: int) -> None:
        self.sv_path.write_text(json.dumps({"security_version": int(sv)}) + "\n")

    def verify_image_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        ok = verify_signature(manifest)
        return {"ok": ok, "kind": "image_manifest"}

    def verify_update_metadata(self, meta: dict[str, Any]) -> dict[str, Any]:
        if not verify_signature(meta):
            return {"ok": False, "reason": "bad_signature"}
        pkg_sv = int(meta.get("security_version", 0))
        cur = self.security_version()
        if pkg_sv < cur:
            return {
                "ok": False,
                "reason": "anti_rollback",
                "package_sv": pkg_sv,
                "device_sv": cur,
            }
        return {"ok": True, "security_version": pkg_sv}

    def verify_app_signature(self, app_bytes: bytes, signature_doc: dict[str, Any]) -> dict[str, Any]:
        digest = sha256_bytes(app_bytes)
        if signature_doc.get("artifact_sha256") != digest:
            return {"ok": False, "reason": "hash_mismatch"}
        if not verify_signature(signature_doc):
            return {"ok": False, "reason": "bad_signature"}
        return {"ok": True, "artifact_sha256": digest}

    def sign_app(self, app_bytes: bytes, app_id: str) -> dict[str, Any]:
        doc = {
            "schema": "gunnchos.stage2.app_signature.v1",
            "app_id": app_id,
            "artifact_sha256": sha256_bytes(app_bytes),
            "realm": "gunnchos-stage2-dev-signing-v1",
            "security_version": self.security_version(),
        }
        doc["signature"] = sign_payload(doc)
        return doc

    def verify_image_file(self, path: Path, expected_sha256: str) -> dict[str, Any]:
        digest = sha256_file(Path(path))
        return {"ok": digest == expected_sha256, "sha256": digest}
