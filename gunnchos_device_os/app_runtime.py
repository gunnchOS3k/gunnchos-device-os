"""First-party app runtime — package metadata + sandbox/permissions launch.

Not an app store. Runs representative apps through the real permissions and
sandbox policy engines. STUB_AS_PRODUCT is forbidden.
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
    "app store, not signed distribution."
)

TOKEN_APP_RUNTIME_PASS = "GUNNCHOS_APP_RUNTIME_DIGITAL_PASS"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


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
    stub_content: bool = False


RUNTIME_CATALOG: tuple[RuntimeApp, ...] = (
    RuntimeApp(
        id="waike",
        category=CATEGORY_WAIKE,
        version="0.3.0-cont-vii",
        entry="apps/waike_learning/index.html",
        permissions=("files_read", "network", "identity_read"),
        source_tree="apps/waike_learning",
        # Companion seed only — full LMS SoR is Platform Tauri Learning OS.
        stub_content=False,
    ),
    RuntimeApp(
        id="creator_studio",
        category=CATEGORY_CODING,
        version="0.2.0-cont-vii",
        entry="apps/creator_studio/index.html",
        permissions=("files_read", "files_write", "network"),
        source_tree="apps/creator_studio",
    ),
    RuntimeApp(
        id="device_dashboard",
        category=CATEGORY_MGMT,
        version="0.2.0-cont-vii",
        entry="apps/device_management/index.html",
        permissions=("files_read", "network", "identity_read"),
        source_tree="apps/device_management",
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
        version="0.2.0-digital-rc",
        entry="games/beatlink-party-web/index.html",
        permissions=("files_read", "network", "microphone"),
        app_class="game",
        source_tree="games/beatlink-party-web",
        stub_content=False,
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
            stub_forbidden = app.stub_content is True
            rows.append({**asdict(app), "source_ok": source_ok, "stub_as_product_forbidden": True, "stub_violation": stub_forbidden})
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
            "stub_as_product": False,
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
        if app.stub_content:
            rec = LaunchRecord(
                app_id=app.id, ok=False, pid_token="", sandbox_profile={},
                permission_grants=[], started_at=time.time(), entry=app.entry,
                category=app.category, stub_content=True, reason="STUB_AS_PRODUCT_FORBIDDEN",
            )
            self.launches.append(rec)
            return {**rec.to_dict(), "stub_as_product_forbidden": True}

        if app.source_tree and not (self.root / app.source_tree).exists():
            rec = LaunchRecord(
                app_id=app.id, ok=False, pid_token="", sandbox_profile={},
                permission_grants=[], started_at=time.time(), entry=app.entry,
                category=app.category, stub_content=False, reason="missing_source",
            )
            self.launches.append(rec)
            return rec.to_dict()

        grants: list[dict[str, Any]] = []
        if deny_permission:
            result = self._permissions.request(
                app.id, Permission(deny_permission), explicit_user_grant=False
            )
            grants.append(result)
            if result.get("decision") == "allow":
                grants.append(self._permissions.revoke(app.id, Permission(deny_permission)))
            rec = LaunchRecord(
                app_id=app.id, ok=False, pid_token="", sandbox_profile={},
                permission_grants=grants, started_at=time.time(), entry=app.entry,
                category=app.category, stub_content=False,
                reason=f"permission_denied:{deny_permission}",
            )
            self.launches.append(rec)
            return {**rec.to_dict(), "permission_rejected": True}

        for perm_name in app.permissions:
            # microphone may be optional on student role — request with grant
            grant = self._permissions.request(
                app.id, Permission(perm_name), explicit_user_grant=explicit_user_grant
            )
            grants.append(grant)
            if grant.get("decision") != "allow":
                # Cont VII: beatlink needs mic; if role blocks, still record denial
                if perm_name == "microphone":
                    continue
                rec = LaunchRecord(
                    app_id=app.id, ok=False, pid_token="", sandbox_profile={},
                    permission_grants=grants, started_at=time.time(), entry=app.entry,
                    category=app.category, stub_content=False,
                    reason=f"permission_denied:{perm_name}",
                )
                self.launches.append(rec)
                return {**rec.to_dict(), "permission_rejected": True}

        profile = self._sandbox.create_profile(app.id, app_class=app.app_class)
        fs_check = self._sandbox.check_capability(app.id, "fs_home_read")
        net_check = self._sandbox.check_capability(app.id, "net_connect")
        isolated = self._sandbox.isolate_process(app.id, f"{app.id}.main")

        payload: dict[str, Any] = {"launched": True}
        if app.category == CATEGORY_WAIKE:
            from gunnchos_device_os.first_party_apps.waike_app import run_waike_app
            payload["waike"] = run_waike_app(role="learner")
        elif app.category == CATEGORY_CODING:
            from gunnchos_device_os.first_party_apps.creator_studio import run_creator_studio
            payload["workspace"] = run_creator_studio()
        elif app.category == CATEGORY_MGMT:
            from gunnchos_device_os.first_party_apps.device_management import run_device_management
            payload["diagnostics_surface"] = run_device_management(role=self.role)
        elif app.category == CATEGORY_GAME:
            entry_path = self.root / app.entry
            manifest = self.root / app.source_tree / "PACKAGE_MANIFEST.json" if app.source_tree else None
            man = {}
            if manifest and manifest.exists():
                man = json.loads(manifest.read_text(encoding="utf-8"))
            stub_markers = False
            if entry_path.exists():
                text = entry_path.read_text(encoding="utf-8", errors="ignore")
                stub_markers = "GUNNCHOS_GAME_STUB_CONTENT=true" in text or "DEV stub" in text
            payload["game"] = {
                "entry_exists": entry_path.exists(),
                "controller_first": True,
                "stub_content": False,
                "stub_markers_detected": stub_markers,
                "package_manifest": {
                    "present": bool(man),
                    "accepted_sha": man.get("accepted_sha"),
                    "artifact_tree_sha256": man.get("artifact_tree_sha256"),
                    "source_repo": man.get("source_repo"),
                },
            }
            if stub_markers:
                rec = LaunchRecord(
                    app_id=app.id, ok=False, pid_token="", sandbox_profile={},
                    permission_grants=grants, started_at=time.time(), entry=app.entry,
                    category=app.category, stub_content=True, reason="STUB_AS_PRODUCT_FORBIDDEN",
                )
                self.launches.append(rec)
                return {**rec.to_dict(), "payload": payload, "stub_as_product_forbidden": True}

        pid_token = f"dev-{app.id}-{int(time.time() * 1000) % 10_000_000}"
        rec = LaunchRecord(
            app_id=app.id, ok=True, pid_token=pid_token,
            sandbox_profile={**profile.to_dict(), "fs_check": fs_check, "net_check": net_check, "isolated": isolated},
            permission_grants=grants, started_at=time.time(), entry=app.entry,
            category=app.category, stub_content=False,
        )
        self.launches.append(rec)
        from gunnchos_device_os.platform_digital import evaluate_platform_digital_complete
        plat = evaluate_platform_digital_complete(root=self.root, quick=True)
        return {
            **rec.to_dict(),
            "payload": payload,
            "claim_boundary": CLAIM_BOUNDARY,
            "mock": False,
            "full_gunnchos_platform_digital_complete": bool(plat.get("earned")),
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
        stub_free = all(not a.stub_content for a in RUNTIME_CATALOG)
        from gunnchos_device_os.platform_digital import evaluate_platform_digital_complete
        plat = evaluate_platform_digital_complete(root=self.root, quick=True)
        return {
            "ok": ok and stub_free,
            "results": results,
            "game_count": len(games),
            "token": TOKEN_APP_RUNTIME_PASS if ok and stub_free else None,
            "claim_boundary": CLAIM_BOUNDARY,
            "full_gunnchos_platform_digital_complete": bool(plat.get("earned")),
            "stub_as_product": False,
            "mock": False,
        }

    def export_overlay_runtime(self, out_dir: Path | None = None) -> dict[str, Any]:
        out = out_dir or (
            self.root / "os_build/bootable_reference/overlay/opt/gunnchos/apps"
        )
        out.mkdir(parents=True, exist_ok=True)
        meta = self.package_metadata()
        path = out / "runtime_catalog.json"
        path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        PackageManifestBuilder(root=self.root).export()
        return {"ok": True, "path": str(path), "metadata": meta}


def ensure_beatlink_package(root: Path | None = None) -> Path:
    """Ensure Beat Link package is real accepted content (never recreate DEV stub)."""
    root = root or _repo_root()
    game_dir = root / "games" / "beatlink-party-web"
    index = game_dir / "index.html"
    manifest = game_dir / "PACKAGE_MANIFEST.json"
    if not index.exists() or not manifest.exists():
        raise FileNotFoundError(
            "Beat Link accepted package missing; run scripts/import_first_party_packages.py"
        )
    text = index.read_text(encoding="utf-8", errors="ignore")
    if "GUNNCHOS_GAME_STUB_CONTENT=true" in text or "DEV stub" in text:
        raise RuntimeError("STUB_AS_PRODUCT_FORBIDDEN: beatlink stub content detected")
    return index


# Back-compat alias used by Cont VI tests — now enforces real package.
def ensure_beatlink_stub(root: Path | None = None) -> Path:
    return ensure_beatlink_package(root)
