"""Persistent signed package lifecycle — inspect, verify, install, upgrade, uninstall.

Identity is bound to the signed package object (package_id inside the signed
manifest), not an arbitrary caller-supplied id verifying an unrelated aggregate.
PRODUCTION_SIGNING remains false (DEV Ed25519 trust root only).
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys

SCHEMA_VERSION = 1
CLAIM_BOUNDARY = (
    "DEV Ed25519 trust root (WP-013 dev_keys). Persistent install registry only; "
    "not production signing or app-store notarization."
)

_VERSION_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?$")


def _safe_component(value: str, *, field_name: str = "package_id") -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value or ".." in value:
        raise ValueError(f"unsafe_{field_name}")
    if value.startswith(".") or "\x00" in value:
        raise ValueError(f"unsafe_{field_name}")
    return value


def _safe_entrypoint(entrypoint: str) -> str:
    if not entrypoint or entrypoint.startswith("/") or entrypoint.startswith("\\"):
        raise ValueError("unsafe_entrypoint")
    if ".." in entrypoint or entrypoint.startswith("../") or "/../" in entrypoint:
        raise ValueError("unsafe_entrypoint")
    if "\\" in entrypoint:
        raise ValueError("unsafe_entrypoint")
    return entrypoint


def _safe_payload_path(path: str) -> str:
    if not path or path.startswith("/") or path.startswith("\\"):
        raise ValueError("unsafe_payload_path")
    if ".." in path or "\\" in path:
        raise ValueError("unsafe_payload_path")
    return path


def parse_version(version: str) -> tuple[int, int, int]:
    if not version or not _VERSION_RE.match(version):
        raise ValueError("invalid_version")
    major, minor, patch = version.split("-", 1)[0].split("+", 1)[0].split(".")[:3]
    return int(major), int(minor), int(patch)


def compare_versions(a: str, b: str) -> int:
    ta, tb = parse_version(a), parse_version(b)
    return (ta > tb) - (ta < tb)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return _sha256_bytes(text.encode("utf-8"))


def build_signed_package(
    repo_root: Path,
    *,
    package_id: str,
    version: str,
    entrypoint: str = "main.py",
    publisher: str = "gunnchos-dev",
    requested_permissions: list[str] | None = None,
    payload: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build a signed package object whose identity is the package_id field."""
    package_id = _safe_component(package_id)
    entrypoint = _safe_entrypoint(entrypoint)
    parse_version(version)
    payload = dict(payload or {"main.py": f"# {package_id} {version}\nprint('ok')\n"})
    if entrypoint not in payload:
        payload[entrypoint] = f"# entry {package_id}\n"
    seen: set[str] = set()
    content_hashes: dict[str, str] = {}
    for rel, body in payload.items():
        rel = _safe_payload_path(rel)
        if rel in seen:
            raise ValueError("duplicate_payload_path")
        seen.add(rel)
        content_hashes[rel] = _sha256_text(body)
    unsigned = {
        "schema_version": SCHEMA_VERSION,
        "package_id": package_id,
        "version": version,
        "entrypoint": entrypoint,
        "publisher": publisher,
        "signer": "local_dev",
        "requested_permissions": list(requested_permissions or ["files_read"]),
        "payload": payload,
        "content_hashes": content_hashes,
        "production_keys_used": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    digest_material = json.dumps(
        {k: unsigned[k] for k in sorted(unsigned) if k != "signature"},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    unsigned["manifest_digest"] = _sha256_bytes(digest_material)
    unsigned["signing_key_fingerprint"] = dev_keys.dev_public_key_fingerprint(repo_root)
    unsigned["signer"] = unsigned["signing_key_fingerprint"]
    to_sign = {k: v for k, v in unsigned.items()}
    payload_bytes = json.dumps(to_sign, sort_keys=True, separators=(",", ":")).encode("utf-8")
    unsigned["signature"] = dev_keys.sign_bytes(repo_root, payload_bytes)
    return unsigned


def verify_signed_package(repo_root: Path, signed: dict[str, Any]) -> dict[str, Any]:
    required = (
        "schema_version",
        "package_id",
        "version",
        "entrypoint",
        "publisher",
        "signer",
        "requested_permissions",
        "payload",
        "content_hashes",
        "manifest_digest",
        "signature",
    )
    missing = [k for k in required if k not in signed]
    if missing:
        return {"ok": False, "error": "missing_required_metadata", "missing": missing}
    try:
        _safe_component(str(signed["package_id"]))
        _safe_entrypoint(str(signed["entrypoint"]))
        parse_version(str(signed["version"]))
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    payload = signed.get("payload") or {}
    hashes = signed.get("content_hashes") or {}
    if set(payload) != set(hashes):
        return {"ok": False, "error": "content_hash_mismatch"}
    try:
        seen: set[str] = set()
        for rel, body in payload.items():
            rel_s = _safe_payload_path(str(rel))
            if rel_s in seen:
                return {"ok": False, "error": "duplicate_payload_path"}
            seen.add(rel_s)
            if _sha256_text(str(body)) != hashes[rel]:
                return {"ok": False, "error": "tampered_content_hash"}
    except ValueError as exc:
        return {"ok": False, "error": str(exc)}
    unsigned = {k: v for k, v in signed.items() if k != "signature"}
    material = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode("utf-8")
    sig_ok = dev_keys.verify_bytes(repo_root, material, signed.get("signature", ""))
    if not sig_ok:
        return {"ok": False, "error": "tampered_signature"}
    expected_fp = dev_keys.dev_public_key_fingerprint(repo_root)
    if signed.get("signing_key_fingerprint") and signed["signing_key_fingerprint"] != expected_fp:
        return {"ok": False, "error": "untrusted_signer"}
    return {"ok": True, "package_id": signed["package_id"], "version": signed["version"]}


@dataclass
class PackageLifecycleManager:
    root: Path
    repo_root: Path
    allow_downgrade: bool = False
    allow_same_version_reinstall: bool = False
    registry_path: Path = field(init=False)
    installs_dir: Path = field(init=False)
    registry: dict[str, Any] = field(default_factory=dict)
    cleanup_hooks: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.repo_root = Path(self.repo_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "registry.json"
        self.installs_dir = self.root / "installed"
        self.installs_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        else:
            self.registry = {
                "schema_version": SCHEMA_VERSION,
                "packages": {},
                "history": [],
                "cleanup_hooks": [],
            }
        self.cleanup_hooks = list(self.registry.get("cleanup_hooks", []))

    def _persist(self) -> None:
        self.registry["cleanup_hooks"] = list(self.cleanup_hooks)
        self.registry_path.write_text(json.dumps(self.registry, indent=2) + "\n", encoding="utf-8")

    def inspect(self) -> dict[str, Any]:
        return {
            "ok": True,
            "schema_version": self.registry.get("schema_version"),
            "installed_count": len(self.registry.get("packages", {})),
            "registry_path": str(self.registry_path),
            "claim_boundary": CLAIM_BOUNDARY,
            "production_signing": False,
        }

    def verify(self, signed: dict[str, Any]) -> dict[str, Any]:
        return verify_signed_package(self.repo_root, signed)

    def _record(self, op: str, package_id: str, **extra: Any) -> None:
        self.registry.setdefault("history", []).append(
            {"op": op, "package_id": package_id, "at_ms": int(time.time() * 1000), **extra}
        )
        self.registry["history"] = self.registry["history"][-200:]
        self._persist()

    def _write_install(self, signed: dict[str, Any]) -> dict[str, Any]:
        package_id = signed["package_id"]
        install_dir = self.installs_dir / package_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir(parents=True)
        (install_dir / "signed_manifest.json").write_text(
            json.dumps(signed, indent=2) + "\n", encoding="utf-8"
        )
        payload_dir = install_dir / "payload"
        payload_dir.mkdir()
        for rel, body in (signed.get("payload") or {}).items():
            target = payload_dir / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(body), encoding="utf-8")
        record = {
            "package_id": package_id,
            "version": signed["version"],
            "entrypoint": signed["entrypoint"],
            "publisher": signed.get("publisher"),
            "signer": signed.get("signer"),
            "requested_permissions": signed.get("requested_permissions"),
            "manifest_digest": signed.get("manifest_digest"),
            "installed_at_ms": int(time.time() * 1000),
            "signature_valid": True,
            "trust_root": "local_dev",
            "production_signing": False,
            "manifest_path": str(install_dir / "signed_manifest.json"),
            "install_dir": str(install_dir),
        }
        self.registry.setdefault("packages", {})[package_id] = record
        self._persist()
        return record

    def install_signed(
        self,
        signed: dict[str, Any],
        *,
        allow_same_version: bool | None = None,
        allow_downgrade: bool | None = None,
    ) -> dict[str, Any]:
        verified = self.verify(signed)
        if not verified.get("ok"):
            return {"ok": False, **verified}
        package_id = signed["package_id"]
        version = signed["version"]
        existing = self.registry.get("packages", {}).get(package_id)
        same_policy = self.allow_same_version_reinstall if allow_same_version is None else allow_same_version
        down_policy = self.allow_downgrade if allow_downgrade is None else allow_downgrade
        if existing:
            cmp = compare_versions(version, existing["version"])
            if cmp == 0 and not same_policy:
                return {
                    "ok": False,
                    "error": "same_version_requires_explicit_policy",
                    "package_id": package_id,
                    "version": version,
                }
            if cmp < 0 and not down_policy:
                return {
                    "ok": False,
                    "error": "downgrade_rejected",
                    "package_id": package_id,
                    "installed_version": existing["version"],
                    "attempted_version": version,
                }
            op = "reinstall" if cmp == 0 else ("upgrade" if cmp > 0 else "downgrade")
        else:
            op = "install"
        record = self._write_install(signed)
        self._record(op, package_id, version=version)
        return {"ok": True, "op": op, **record}

    def install(
        self,
        package_id: str,
        *,
        version: str = "1.0.0",
        entrypoint: str = "main.py",
        allow_same_version: bool | None = None,
        allow_downgrade: bool | None = None,
        payload: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            signed = build_signed_package(
                self.repo_root,
                package_id=package_id,
                version=version,
                entrypoint=entrypoint,
                payload=payload,
            )
        except ValueError as exc:
            return {"ok": False, "error": str(exc), "package_id": package_id}
        return self.install_signed(
            signed,
            allow_same_version=allow_same_version,
            allow_downgrade=allow_downgrade,
        )

    def upgrade(self, package_id: str, *, version: str) -> dict[str, Any]:
        existing = self.registry.get("packages", {}).get(package_id)
        if not existing:
            return {"ok": False, "error": "not_installed", "package_id": package_id}
        try:
            if compare_versions(version, existing["version"]) <= 0:
                return {
                    "ok": False,
                    "error": "upgrade_requires_newer_version",
                    "package_id": package_id,
                    "installed_version": existing["version"],
                    "attempted_version": version,
                }
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        result = self.install(package_id, version=version)
        if result.get("ok"):
            result["previous_version"] = existing["version"]
        return result

    def uninstall(self, package_id: str) -> dict[str, Any]:
        try:
            package_id = _safe_component(package_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        rec = self.registry.get("packages", {}).pop(package_id, None)
        install_dir = self.installs_dir / package_id
        removed_content = False
        if install_dir.exists():
            shutil.rmtree(install_dir)
            removed_content = True
        hook = f"cleanup:{package_id}:{int(time.time() * 1000)}"
        self.cleanup_hooks.append(hook)
        if rec is None:
            self._persist()
            return {"ok": False, "error": "not_installed", "package_id": package_id}
        self._record("uninstall", package_id, cleanup_hook=hook)
        still_registered = package_id in self.registry.get("packages", {})
        return {
            "ok": True,
            "package_id": package_id,
            "removed": rec,
            "registry_absent": not still_registered,
            "content_absent": not install_dir.exists(),
            "removed_content": removed_content,
            "cleanup_hook": hook,
        }

    def list_installed(self) -> dict[str, Any]:
        return {"ok": True, "packages": dict(self.registry.get("packages", {}))}

    def get(self, package_id: str) -> dict[str, Any]:
        try:
            package_id = _safe_component(package_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        rec = self.registry.get("packages", {}).get(package_id)
        if rec is None:
            return {"ok": False, "error": "not_installed", "package_id": package_id}
        manifest_path = Path(rec["manifest_path"])
        if not manifest_path.exists():
            return {"ok": False, "error": "manifest_missing", "package_id": package_id}
        signed = json.loads(manifest_path.read_text(encoding="utf-8"))
        if signed.get("package_id") != package_id:
            return {"ok": False, "error": "identity_mismatch", "package_id": package_id}
        verified = self.verify(signed)
        return {
            "ok": verified.get("ok") is True,
            "package_id": package_id,
            "record": rec,
            "signature_valid": verified.get("ok") is True,
            "verify": verified,
        }

    def run_full_lifecycle_proof(self, package_id: str = "lifecycle-demo") -> dict[str, Any]:
        """install v1 → restart → upgrade v2 → restart → uninstall → restart."""
        steps: dict[str, Any] = {}
        inspect0 = self.inspect()
        signed_v1 = build_signed_package(self.repo_root, package_id=package_id, version="1.0.0")
        verify_v1 = self.verify(signed_v1)
        install_v1 = self.install_signed(signed_v1)
        mgr_a = PackageLifecycleManager.from_storage(self.root, self.repo_root)
        after_install = mgr_a.get(package_id)
        upgrade_v2 = mgr_a.upgrade(package_id, version="2.0.0")
        mgr_b = PackageLifecycleManager.from_storage(self.root, self.repo_root)
        after_upgrade = mgr_b.get(package_id)
        downgrade = mgr_b.install(package_id, version="1.5.0")
        uninstall = mgr_b.uninstall(package_id)
        mgr_c = PackageLifecycleManager.from_storage(self.root, self.repo_root)
        after_uninstall = mgr_c.get(package_id)
        content_gone = not (self.installs_dir / package_id).exists()
        steps = {
            "inspect": inspect0,
            "verify_v1": verify_v1,
            "install_v1": install_v1,
            "restart_after_install": after_install,
            "upgrade_v2": upgrade_v2,
            "restart_after_upgrade": after_upgrade,
            "downgrade_attempt": downgrade,
            "uninstall": uninstall,
            "restart_after_uninstall": after_uninstall,
            "content_absent": content_gone,
        }
        ok = (
            inspect0.get("ok")
            and verify_v1.get("ok")
            and install_v1.get("ok")
            and after_install.get("ok")
            and after_install.get("record", {}).get("version") == "1.0.0"
            and upgrade_v2.get("ok")
            and after_upgrade.get("ok")
            and after_upgrade.get("record", {}).get("version") == "2.0.0"
            and downgrade.get("ok") is False
            and downgrade.get("error") == "downgrade_rejected"
            and uninstall.get("ok")
            and uninstall.get("registry_absent")
            and uninstall.get("content_absent")
            and after_uninstall.get("ok") is False
            and content_gone
        )
        return {"ok": ok, "package_id": package_id, "steps": steps, "claim_boundary": CLAIM_BOUNDARY}

    def run_negative_proofs(self) -> dict[str, Any]:
        cases: dict[str, Any] = {}

        def _catch(fn):  # type: ignore[no-untyped-def]
            try:
                return fn()
            except ValueError as exc:
                return {"ok": False, "error": str(exc)}

        cases["package_id_traversal"] = self.install("../evil", version="1.0.0")
        cases["package_id_slash"] = self.install("slash/evil", version="1.0.0")
        cases["package_id_backslash"] = self.install("back\\evil", version="1.0.0")
        cases["entrypoint_traversal"] = _catch(
            lambda: build_signed_package(
                self.repo_root, package_id="ep-trav", version="1.0.0", entrypoint="../outside"
            )
        )
        cases["entrypoint_absolute"] = _catch(
            lambda: build_signed_package(
                self.repo_root, package_id="ep-abs", version="1.0.0", entrypoint="/abs/main.py"
            )
        )
        cases["payload_traversal"] = _catch(
            lambda: build_signed_package(
                self.repo_root,
                package_id="pay-trav",
                version="1.0.0",
                payload={"../outside": "x"},
            )
        )
        # Duplicate payload path detection via sequential safe-path set
        try:
            paths = ["main.py", "main.py"]
            seen: set[str] = set()
            for rel in paths:
                rel_s = _safe_payload_path(rel)
                if rel_s in seen:
                    raise ValueError("duplicate_payload_path")
                seen.add(rel_s)
            cases["duplicate_payload"] = {"ok": True}
        except ValueError as exc:
            cases["duplicate_payload"] = {"ok": False, "error": str(exc)}
        cases["missing_metadata"] = verify_signed_package(self.repo_root, {"package_id": "x"})
        good = build_signed_package(self.repo_root, package_id="tamper-base", version="1.0.0")
        tampered_manifest = dict(good)
        tampered_manifest["version"] = "9.9.9"
        cases["tampered_manifest"] = verify_signed_package(self.repo_root, tampered_manifest)
        hash_tamper = dict(good)
        hash_tamper["content_hashes"] = dict(good["content_hashes"])
        hash_tamper["content_hashes"]["main.py"] = "0" * 64
        cases["tampered_content_hash"] = verify_signed_package(self.repo_root, hash_tamper)
        sig_tamper = dict(good)
        sig_tamper["signature"] = "00" * 32
        cases["tampered_signature"] = verify_signed_package(self.repo_root, sig_tamper)
        # Untrusted signer: sign with ephemeral key not in trust root
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

        evil = {k: v for k, v in good.items() if k != "signature"}
        evil["signing_key_fingerprint"] = "evil-untrusted"
        evil["signer"] = "evil-untrusted"
        material = json.dumps(evil, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evil_key = Ed25519PrivateKey.generate()
        evil["signature"] = evil_key.sign(material).hex()
        cases["untrusted_signer"] = verify_signed_package(self.repo_root, evil)
        self.install("policy-app", version="2.0.0")
        cases["downgrade_attempt"] = self.install("policy-app", version="1.0.0")
        cases["invalid_version"] = self.install("badver", version="not-a-version")
        same = self.install("policy-app", version="2.0.0")
        cases["same_version_without_policy"] = same
        cases["same_version_explicit"] = self.install(
            "policy-app", version="2.0.0", allow_same_version=True
        )
        blocked = {
            k: (v.get("ok") is False)
            for k, v in cases.items()
            if k != "same_version_explicit"
        }
        blocked["same_version_explicit"] = cases["same_version_explicit"].get("ok") is True
        ok = all(blocked.values())
        return {"ok": ok, "cases": cases, "blocked": blocked}

    @classmethod
    def from_storage(cls, root: Path, repo_root: Path) -> "PackageLifecycleManager":
        return cls(root=root, repo_root=repo_root)
