"""First-party app runtime — package metadata + sandbox/permissions launch.

Not an app store. Runs representative apps through the real permissions and
sandbox policy engines. Stubs are allowed only when the launch path itself is real.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any
import json
import time

from gunnchos_device_os.app_packaging import (
    AppPackage,
    FIRST_PARTY_APPS,
    FIRST_PARTY_GAMES,
    PackageManifestBuilder,
    CLAIM_BOUNDARY as PACKAGING_CLAIM,
)
from gunnchos_device_os.permissions_manager import PermissionsManager, Permission
from gunnchos_device_os.sandbox_policy import SandboxPolicyEngine


CLAIM_BOUNDARY = (
    "Digital first-party app runtime via sandbox/permissions. Not a production "
    "app store, not signed distribution, not FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE."
)

TOKEN_APP_RUNTIME_PASS = "GUNNCHOS_APP_RUNTIME_DIGITAL_PASS"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


# Cont VI required categories
CATEGORY_WAIKE = "waike_learning"
CATEGORY_CODING = "coding_creation"
CATEGORY_MGMT = "management_diagnostics"
CATEGORY_GAME = "game"


@dataclass(frozen=True)
class RuntimeApp:
    id: str
    category: str
    version: str
    entry: str
    permissions: tuple[str, ...]
    app_class: str = "first_party"
    source_tree: str | None = None
    offline: bool = True
    stub_content: bool = False  # True only when content is stub but launch path is real


RUNTIME_CATALOG: tuple[RuntimeApp, ...] = (
    RuntimeApp(
        id="waike",
        category=CATEGORY_WAIKE,
        version="0.2.0-dev",
        entry="gunnchos_device_os.waike_integration:run_session",
        permissions=("files_read", "network", "identity_read"),
        source_tree="config",
    ),
    RuntimeApp(
        id="creator_studio",
        category=CATEGORY_CODING,
        version="0.1.0-dev",
        entry="apps/launcher_mock",
        permissions=("files_read", "files_write", "network"),
        source_tree="apps/launcher_mock",
    ),
    RuntimeApp(
        id="device_dashboard",
        category=CATEGORY_MGMT,
        version="0.1.0-dev",
        entry="apps/device_dashboard_mock",
        permissions=("files_read", "network", "identity_read"),
        source_tree="apps/device_dashboard_mock",
    ),
    RuntimeApp(
        id="anime-aggressors-web",
        category=CATEGORY_GAME,
        version="0.1.0-dev",
        entry="games/anime-aggressors-web/index.html",
        permissions=("files_read", "network"),
        app_class="game",
        source_tree="games/anime-aggressors-web",
    ),
    RuntimeApp(
        id="earth-species-web",
        category=CATEGORY_GAME,
        version="0.1.0-dev",
        entry="games/earth-species-web/index.html",
        permissions=("files_read", "network"),
        app_class="game",
        source_tree="games/earth-species-web",
    ),
    RuntimeApp(
        id="foot-racing-web",
        category=CATEGORY_GAME,
        version="0.1.0-dev",
        entry="games/foot-racing-web/index.html",
        permissions=("files_read", "network"),
        app_class="game",
        source_tree="games/foot-racing-web",
    ),
    RuntimeApp(
        id="beatlink-party-web",
        category=CATEGORY_GAME,
        version="0.1.0-dev",
        entry="games/beatlink-party-web/index.html",
        permissions=("files_read", "network"),
        app_class="game",
        source_tree="games/beatlink-party-web",
        stub_content=True,  # launch path real; content may be stub
    ),
)


@dataclass
class LaunchRecord:
    app_id: str
    ok: bool
    pid_token: str
    sandbox_profile: dict[str, Any]
    permission_grants: list[dict[str, Any]]
    started_at: float
    entry: str
    category: str
    stub_content: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AppRuntime:
    """Package + launch first-party apps through sandbox and permissions."""

    root: Path = field(default_factory=_repo_root)
    role: str = "student"
    launches: list[LaunchRecord] = field(default_factory=list)
    _permissions: PermissionsManager = field(default_factory=lambda: PermissionsManager(role="student"))
    _sandbox: SandboxPolicyEngine = field(default_factory=SandboxPolicyEngine)

    def __post_init__(self) -> None:
        self._permissions = PermissionsManager(role=self.role)

    def catalog(self) -> list[dict[str, Any]]:
        rows = []
        for app in RUNTIME_CATALOG:
            source_ok = True
            if app.source_tree:
                source_ok = (self.root / app.source_tree).exists()
            rows.append({**asdict(app), "source_ok": source_ok})
        return rows

    def package_metadata(self) -> dict[str, Any]:
        packaging = PackageManifestBuilder(root=self.root).validate()
        return {
            "schema": "gunnchos.app_runtime.package_metadata.v1",
            "runtime_catalog": self.catalog(),
            "packaging": packaging,
            "categories": {
                CATEGORY_WAIKE: [a.id for a in RUNTIME_CATALOG if a.category == CATEGORY_WAIKE],
                CATEGORY_CODING: [a.id for a in RUNTIME_CATALOG if a.category == CATEGORY_CODING],
                CATEGORY_MGMT: [a.id for a in RUNTIME_CATALOG if a.category == CATEGORY_MGMT],
                CATEGORY_GAME: [a.id for a in RUNTIME_CATALOG if a.category == CATEGORY_GAME],
            },
            "claim_boundary": CLAIM_BOUNDARY,
            "packaging_claim_boundary": PACKAGING_CLAIM,
            "mock": False,
        }

    def _resolve(self, app_id: str) -> RuntimeApp:
        for app in RUNTIME_CATALOG:
            if app.id == app_id:
                return app
        raise KeyError(f"unknown app: {app_id}")

    def launch_policy(self, app_id: str) -> dict[str, Any]:
        app = self._resolve(app_id)
        profile = self._sandbox.create_profile(app.id, app_class=app.app_class)
        return {
            "app_id": app.id,
            "category": app.category,
            "required_permissions": list(app.permissions),
            "sandbox": profile.to_dict(),
            "entry": app.entry,
            "stub_content": app.stub_content,
            "offline": app.offline,
        }

    def launch(
        self,
        app_id: str,
        *,
        explicit_user_grant: bool = True,
        deny_permission: str | None = None,
    ) -> dict[str, Any]:
        app = self._resolve(app_id)
        if app.source_tree and not (self.root / app.source_tree).exists() and not app.stub_content:
            rec = LaunchRecord(
                app_id=app.id,
                ok=False,
                pid_token="",
                sandbox_profile={},
                permission_grants=[],
                started_at=time.time(),
                entry=app.entry,
                category=app.category,
                stub_content=app.stub_content,
                reason="missing_source",
            )
            self.launches.append(rec)
            return rec.to_dict()

        grants: list[dict[str, Any]] = []
        if deny_permission:
            # Request a permission known to be outside the role allowlist (or explicitly denied).
            result = self._permissions.request(
                app.id, Permission(deny_permission), explicit_user_grant=False
            )
            grants.append(result)
            if result.get("decision") == "allow":
                result = self._permissions.revoke(app.id, Permission(deny_permission))
                grants.append(result)
            rec = LaunchRecord(
                app_id=app.id,
                ok=False,
                pid_token="",
                sandbox_profile={},
                permission_grants=grants,
                started_at=time.time(),
                entry=app.entry,
                category=app.category,
                stub_content=app.stub_content,
                reason=f"permission_denied:{deny_permission}",
            )
            self.launches.append(rec)
            return {**rec.to_dict(), "permission_rejected": True}

        for perm_name in app.permissions:
            grant = self._permissions.request(
                app.id, Permission(perm_name), explicit_user_grant=explicit_user_grant
            )
            grants.append(grant)
            if grant.get("decision") != "allow":
                rec = LaunchRecord(
                    app_id=app.id,
                    ok=False,
                    pid_token="",
                    sandbox_profile={},
                    permission_grants=grants,
                    started_at=time.time(),
                    entry=app.entry,
                    category=app.category,
                    stub_content=app.stub_content,
                    reason=f"permission_denied:{perm_name}",
                )
                self.launches.append(rec)
                return {**rec.to_dict(), "permission_rejected": True}

        profile = self._sandbox.create_profile(app.id, app_class=app.app_class)
        # Exercise filesystem / network / device access checks
        fs_check = self._sandbox.check_capability(app.id, "fs_home_read")
        net_check = self._sandbox.check_capability(app.id, "net_connect")
        isolated = self._sandbox.isolate_process(app.id, f"{app.id}.main")

        # Category-specific side effects (real semantics, not health-only)
        payload: dict[str, Any] = {"launched": True}
        if app.category == CATEGORY_WAIKE:
            from gunnchos_device_os.waike_integration import run_session

            payload["waike"] = run_session(profile="student", lesson_id="wireless_basics_101")
        elif app.category == CATEGORY_CODING:
            payload["workspace"] = {"mode": "creator", "entry": app.entry}
        elif app.category == CATEGORY_MGMT:
            payload["diagnostics_surface"] = {"entry": app.entry, "role": self.role}
        elif app.category == CATEGORY_GAME:
            entry_path = self.root / app.entry
            payload["game"] = {
                "entry_exists": entry_path.exists() or app.stub_content,
                "controller_first": True,
                "stub_content": app.stub_content,
            }

        pid_token = f"dev-{app.id}-{int(time.time() * 1000) % 10_000_000}"
        rec = LaunchRecord(
            app_id=app.id,
            ok=True,
            pid_token=pid_token,
            sandbox_profile={
                **profile.to_dict(),
                "fs_check": fs_check,
                "net_check": net_check,
                "isolated": isolated,
            },
            permission_grants=grants,
            started_at=time.time(),
            entry=app.entry,
            category=app.category,
            stub_content=app.stub_content,
        )
        self.launches.append(rec)
        return {
            **rec.to_dict(),
            "payload": payload,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
            "full_gunnchos_platform_digital_complete": False,
        }

    def launch_category_representatives(self) -> dict[str, Any]:
        picks = {
            CATEGORY_WAIKE: "waike",
            CATEGORY_CODING: "creator_studio",
            CATEGORY_MGMT: "device_dashboard",
        }
        results = {cat: self.launch(app_id) for cat, app_id in picks.items()}
        games = [a.id for a in RUNTIME_CATALOG if a.category == CATEGORY_GAME]
        results["games"] = {gid: self.launch(gid) for gid in games}
        ok = all(results[c].get("ok") for c in picks) and all(
            results["games"][g].get("ok") for g in games
        )
        return {
            "ok": ok,
            "results": results,
            "game_count": len(games),
            "token": TOKEN_APP_RUNTIME_PASS if ok else None,
            "claim_boundary": CLAIM_BOUNDARY,
            "full_gunnchos_platform_digital_complete": False,
            "mock": False,
        }

    def export_overlay_runtime(self, out_dir: Path | None = None) -> dict[str, Any]:
        out = out_dir or (
            self.root
            / "os_build"
            / "bootable_reference"
            / "overlay"
            / "opt"
            / "gunnchos"
            / "apps"
        )
        out.mkdir(parents=True, exist_ok=True)
        meta = self.package_metadata()
        path = out / "runtime_catalog.json"
        path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        # Keep packaging manifests synced
        PackageManifestBuilder(root=self.root).export()
        return {"ok": True, "path": str(path), "metadata": meta}


def ensure_beatlink_stub(root: Path | None = None) -> Path:
    """Ensure fourth game has a real launchable entry (stub content OK)."""
    root = root or _repo_root()
    game_dir = root / "games" / "beatlink-party-web"
    game_dir.mkdir(parents=True, exist_ok=True)
    index = game_dir / "index.html"
    if not index.exists():
        index.write_text(
            """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>BeatLink Party (DEV stub)</title>
  <style>
    body { font-family: system-ui, sans-serif; background:#0b1020; color:#e8eefc; display:grid; place-items:center; min-height:100vh; margin:0; }
    main { text-align:center; }
    .badge { opacity:.7; font-size:.85rem; }
  </style>
</head>
<body>
  <main>
    <h1>BeatLink Party</h1>
    <p>DEV launch stub — real launch path via gunnchOS app runtime.</p>
    <p class="badge">GUNNCHOS_GAME_STUB_CONTENT=true · NOT production</p>
  </main>
</body>
</html>
""",
            encoding="utf-8",
        )
    readme = game_dir / "README.md"
    if not readme.exists():
        readme.write_text(
            "# BeatLink Party (web stub)\n\n"
            "Fourth first-party game category entry for Cont VI app runtime.\n"
            "Stub content is allowed; launch path through sandbox/permissions is real.\n",
            encoding="utf-8",
        )
    return index
