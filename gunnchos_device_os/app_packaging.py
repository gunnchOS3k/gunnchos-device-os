"""First-party app + game package manifests for coherent platform packaging.

Builds deterministic package manifests for first-party apps and web games,
suitable for inclusion in the bootable reference image and digital validation.
Not an app store, not production signed.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import hashlib
import json


CLAIM_BOUNDARY = (
    "Digital first-party app/game package manifests only. Not an app store, "
    "not Steam/certification, no production signing keys."
)

TOKEN_APP_PACKAGING_PASS = "GUNNCHOS_APP_PACKAGING_DIGITAL_PASS"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True)
class AppPackage:
    id: str
    kind: str
    version: str
    entry: str
    offline: bool = True
    controller_first: bool = False
    source_tree: str | None = None


FIRST_PARTY_APPS: tuple[AppPackage, ...] = (
    AppPackage(
        id="launcher",
        kind="first_party",
        version="0.2.0-alpha",
        entry="apps/launcher_mock",
        source_tree="apps/launcher_mock",
    ),
    AppPackage(
        id="device_dashboard",
        kind="first_party",
        version="0.1.0-dev",
        entry="apps/device_dashboard_mock",
        source_tree="apps/device_dashboard_mock",
    ),
    AppPackage(
        id="gunnchai_tutor",
        kind="first_party",
        version="0.1.0-dev",
        entry="opt/gunnchos/runtime/ai_stub",
        offline=True,
    ),
)

FIRST_PARTY_GAMES: tuple[AppPackage, ...] = (
    AppPackage(
        id="anime-aggressors-web",
        kind="first_party_web_game",
        version="0.1.0-dev",
        entry="games/anime-aggressors-web/index.html",
        controller_first=True,
        source_tree="games/anime-aggressors-web",
    ),
    AppPackage(
        id="earth-species-web",
        kind="first_party_web_game",
        version="0.1.0-dev",
        entry="games/earth-species-web/index.html",
        controller_first=True,
        source_tree="games/earth-species-web",
    ),
    AppPackage(
        id="foot-racing-web",
        kind="first_party_web_game",
        version="0.1.0-dev",
        entry="games/foot-racing-web/index.html",
        controller_first=True,
        source_tree="games/foot-racing-web",
    ),
    AppPackage(
        id="beatlink-party-web",
        kind="first_party_web_game",
        version="0.1.0-dev",
        entry="games/beatlink-party-web/index.html",
        controller_first=True,
        source_tree="games/beatlink-party-web",
    ),
)


@dataclass
class PackageManifestBuilder:
    root: Path = field(default_factory=_repo_root)

    def _validate_sources(self, packages: tuple[AppPackage, ...]) -> list[dict[str, Any]]:
        rows = []
        for pkg in packages:
            source_ok = True
            detail = "no_source_tree_required"
            if pkg.source_tree:
                path = self.root / pkg.source_tree
                source_ok = path.exists()
                detail = str(path.relative_to(self.root)) if source_ok else f"missing:{pkg.source_tree}"
            rows.append(
                {
                    "id": pkg.id,
                    "kind": pkg.kind,
                    "version": pkg.version,
                    "entry": pkg.entry,
                    "offline": pkg.offline,
                    "controller_first": pkg.controller_first,
                    "source_ok": source_ok,
                    "source_detail": detail,
                }
            )
        return rows

    def build_app_manifest(self) -> dict[str, Any]:
        apps = [asdict(a) for a in FIRST_PARTY_APPS]
        body = {
            "schema": "gunnchos.app_packaging.apps.v1",
            "realm": "DEV",
            "apps": apps,
            "count": len(apps),
            "production_keys_used": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        digest = _sha256_bytes(_canonical_json(body))
        return {**body, "digest_sha256": digest}

    def build_game_manifest(self) -> dict[str, Any]:
        games = [asdict(g) for g in FIRST_PARTY_GAMES]
        body = {
            "schema": "gunnchos.app_packaging.games.v1",
            "realm": "DEV",
            "games": games,
            "count": len(games),
            "production_keys_used": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        digest = _sha256_bytes(_canonical_json(body))
        return {**body, "digest_sha256": digest}

    def validate(self) -> dict[str, Any]:
        app_rows = self._validate_sources(FIRST_PARTY_APPS)
        game_rows = self._validate_sources(FIRST_PARTY_GAMES)
        apps_ok = all(r["source_ok"] for r in app_rows if r["id"] != "gunnchai_tutor")
        # gunnchai_tutor is a stub entry — allowed without source tree
        games_ok = all(r["source_ok"] for r in game_rows)
        ok = apps_ok and games_ok and len(app_rows) >= 2 and len(game_rows) >= 4
        return {
            "schema": "gunnchos.app_packaging.validation.v1",
            "ok": ok,
            "apps": app_rows,
            "games": game_rows,
            "app_manifest": self.build_app_manifest(),
            "game_manifest": self.build_game_manifest(),
            "token": TOKEN_APP_PACKAGING_PASS if ok else None,
            "claim_boundary": CLAIM_BOUNDARY,
            "production_keys_used": False,
            "full_operational_product_claimed": False,
        }

    def export(self, out_dir: Path | None = None) -> dict[str, Any]:
        out = out_dir or (
            self.root / "os_build" / "bootable_reference" / "artifacts" / "packaging"
        )
        out.mkdir(parents=True, exist_ok=True)
        report = self.validate()
        (out / "apps_manifest.json").write_bytes(_canonical_json(report["app_manifest"]) + b"\n")
        (out / "games_manifest.json").write_bytes(_canonical_json(report["game_manifest"]) + b"\n")
        (out / "validation.json").write_bytes(_canonical_json(report) + b"\n")
        # Keep bootable overlay manifests in sync with builder output.
        overlay_apps = (
            self.root
            / "os_build"
            / "bootable_reference"
            / "overlay"
            / "opt"
            / "gunnchos"
            / "apps"
            / "manifest.json"
        )
        overlay_games = (
            self.root
            / "os_build"
            / "bootable_reference"
            / "overlay"
            / "opt"
            / "gunnchos"
            / "games"
            / "manifest.json"
        )
        if overlay_apps.parent.exists():
            overlay_apps.write_bytes(_canonical_json(report["app_manifest"]) + b"\n")
        if overlay_games.parent.exists():
            overlay_games.write_bytes(_canonical_json(report["game_manifest"]) + b"\n")
        report["exported_to"] = str(out)
        return report


def build_and_validate_packaging() -> dict[str, Any]:
    return PackageManifestBuilder().export()
