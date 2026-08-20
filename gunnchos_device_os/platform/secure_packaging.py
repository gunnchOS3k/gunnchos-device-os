"""Signed application package pipeline — DEV trust root only."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.app_packaging import PackageManifestBuilder, build_and_validate_packaging
from gunnchos_device_os.release_engineering import dev_keys

CLAIM_BOUNDARY = (
    "DEV Ed25519 trust root (WP-013 dev_keys). Not production signing, "
    "not app-store notarization, not Play Protect attestation."
)


def sign_manifest(repo_root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    signed = dict(manifest)
    signed["signing_key_fingerprint"] = dev_keys.dev_public_key_fingerprint(repo_root)
    signed["trust_root"] = "local_dev"
    signed["production_keys_used"] = False
    signed["claim_boundary"] = CLAIM_BOUNDARY
    payload = json.dumps(signed, sort_keys=True).encode("utf-8")
    signed["signature_hex"] = dev_keys.sign_bytes(repo_root, payload)
    return signed


def verify_signed_manifest(repo_root: Path, signed: dict[str, Any]) -> bool:
    unsigned = {k: v for k, v in signed.items() if k != "signature_hex"}
    payload = json.dumps(unsigned, sort_keys=True).encode("utf-8")
    return dev_keys.verify_bytes(repo_root, payload, signed.get("signature_hex", ""))


def build_signed_app_package(repo_root: Path) -> dict[str, Any]:
    report = build_and_validate_packaging()
    builder = PackageManifestBuilder(root=repo_root)
    app_manifest = builder.build_app_manifest()
    game_manifest = builder.build_game_manifest()
    signed_apps = sign_manifest(repo_root, app_manifest)
    signed_games = sign_manifest(repo_root, game_manifest)
    apps_ok = verify_signed_manifest(repo_root, signed_apps)
    games_ok = verify_signed_manifest(repo_root, signed_games)
    return {
        "ok": report["ok"] and apps_ok and games_ok,
        "packaging_report": report,
        "signed_apps": signed_apps,
        "signed_games": signed_games,
        "apps_signature_valid": apps_ok,
        "games_signature_valid": games_ok,
        "trust_root": "local_dev",
        "production_keys_used": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
