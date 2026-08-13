"""Ingest accepted WAIKE owner packages without re-authoring curriculum.

Source of truth: waike-research-ops (accepted #43 / main). Device-os stores a
signed, versioned import of owner ingest artifacts, projects learner vs teacher
views, offline-caches them, and supports migration/rollback. Instructor keys
must never appear in the learner projection.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys

SCHEMA = "gunnchos.product_use.waike_owner_package.v1"
STORE_REL = Path("artifacts/product_use/waike_store")
LEARNER_FORBIDDEN_KEYS = frozenset(
    {
        "answer_index",
        "answer_keys",
        "instructor_keys",
        "solution_key",
        "explanation",
        "correct",
        "instructor_notes",
        "rubrics",
    }
)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _strip_learner_secrets(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {
            k: _strip_learner_secrets(v)
            for k, v in obj.items()
            if k not in LEARNER_FORBIDDEN_KEYS
        }
    if isinstance(obj, list):
        return [_strip_learner_secrets(x) for x in obj]
    return obj


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class OwnerIngestPaths:
    owner_root: Path
    learner_ingest: Path
    teacher_ingest: Path

    @classmethod
    def from_owner_root(cls, owner_root: Path) -> "OwnerIngestPaths":
        root = Path(owner_root).resolve()
        learner = root / "ingest" / "learner" / "waike_learner_ingest.v1.json"
        teacher = root / "ingest" / "teacher" / "waike_teacher_ingest.v1.json"
        if not learner.is_file():
            raise FileNotFoundError(f"owner_learner_ingest_missing:{learner}")
        if not teacher.is_file():
            raise FileNotFoundError(f"owner_teacher_ingest_missing:{teacher}")
        return cls(owner_root=root, learner_ingest=learner, teacher_ingest=teacher)


class WaikeOwnerPackageStore:
    """Versioned signed import store under artifacts/product_use/waike_store."""

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.root = self.repo_root / STORE_REL
        self.root.mkdir(parents=True, exist_ok=True)
        self.index_path = self.root / "INDEX.json"

    def _load_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {
                "schema": "gunnchos.product_use.waike_store_index.v1",
                "active_version": None,
                "versions": [],
                "claim_boundary": (
                    "Imported from waike-research-ops owner ingest only. "
                    "Not re-authored in device-os. DEV_TEST Ed25519 signatures."
                ),
            }
        return _read_json(self.index_path)

    def _save_index(self, index: dict[str, Any]) -> None:
        self.index_path.write_text(json.dumps(index, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def import_owner(
        self,
        owner_root: Path,
        *,
        owner_commit: str | None = None,
        package_version: str | None = None,
    ) -> dict[str, Any]:
        paths = OwnerIngestPaths.from_owner_root(owner_root)
        learner_raw = paths.learner_ingest.read_bytes()
        teacher_raw = paths.teacher_ingest.read_bytes()
        learner_doc = json.loads(learner_raw.decode("utf-8"))
        teacher_doc = json.loads(teacher_raw.decode("utf-8"))

        if learner_doc.get("schema") != "waike.learner_ingest.v1":
            raise ValueError(f"unexpected_learner_schema:{learner_doc.get('schema')}")
        if teacher_doc.get("schema") != "waike.teacher_ingest.v1":
            raise ValueError(f"unexpected_teacher_schema:{teacher_doc.get('schema')}")

        # Defense in depth: never trust owner learner file without stripping.
        learner_view = _strip_learner_secrets(learner_doc)
        teacher_view = teacher_doc  # teacher keeps keys; role-gated at read time

        learner_leak = self._forbidden_present(learner_view)
        if learner_leak:
            raise ValueError(f"learner_key_leak:{sorted(learner_leak)}")

        content_digest = _sha256_bytes(
            _canonical(
                {
                    "learner_sha256": _sha256_bytes(learner_raw),
                    "teacher_sha256": _sha256_bytes(teacher_raw),
                    "learner_schema": learner_doc.get("schema"),
                    "teacher_schema": teacher_doc.get("schema"),
                    "course_ids": [c.get("course_id") for c in learner_doc.get("courses", [])],
                }
            )
        )
        version = package_version or f"owner-{content_digest[:12]}"
        dest = self.root / "versions" / version
        if dest.exists():
            shutil.rmtree(dest)
        dest.mkdir(parents=True, exist_ok=True)

        (dest / "learner_ingest.json").write_text(
            json.dumps(learner_view, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        (dest / "teacher_ingest.json").write_text(
            json.dumps(teacher_view, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        # Offline cache mirror (same bytes; versioned directory is the cache).
        cache = dest / "offline_cache"
        cache.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dest / "learner_ingest.json", cache / "learner_ingest.json")
        shutil.copy2(dest / "teacher_ingest.json", cache / "teacher_ingest.json")

        provenance = {
            "owner_root": str(paths.owner_root),
            "owner_commit": owner_commit,
            "owner_learner_path": str(paths.learner_ingest.relative_to(paths.owner_root)),
            "owner_teacher_path": str(paths.teacher_ingest.relative_to(paths.owner_root)),
            "owner_learner_sha256": _sha256_bytes(learner_raw),
            "owner_teacher_sha256": _sha256_bytes(teacher_raw),
            "imported_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "reauthored_in_device_os": False,
        }
        package = {
            "schema": SCHEMA,
            "package_version": version,
            "content_digest": content_digest,
            "course_ids": [c.get("course_id") for c in learner_view.get("courses", [])],
            "course_count": len(learner_view.get("courses") or []),
            "roles": ["learner", "teacher"],
            "provenance": provenance,
            "signing_tier": "DEV_TEST",
            "claim_boundary": (
                "Signed DEV_TEST import of waike-research-ops owner ingest. "
                "Not production trust root. Curriculum owner remains waike-research-ops."
            ),
        }
        package_digest = _sha256_bytes(_canonical({k: v for k, v in package.items() if k != "signature"}))
        package["package_digest"] = package_digest
        package["signature"] = {
            "algorithm": "Ed25519",
            "signature_hex": dev_keys.sign_bytes(self.repo_root, package_digest.encode("utf-8")),
            "public_key_fingerprint": dev_keys.dev_public_key_fingerprint(self.repo_root),
            "signing_tier": "DEV_TEST",
            "claim_boundary": dev_keys.CLAIM_BOUNDARY,
        }
        (dest / "PACKAGE.json").write_text(json.dumps(package, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        index = self._load_index()
        versions = [v for v in index.get("versions", []) if v.get("package_version") != version]
        versions.append(
            {
                "package_version": version,
                "content_digest": content_digest,
                "package_digest": package_digest,
                "course_ids": package["course_ids"],
                "imported_utc": provenance["imported_utc"],
                "owner_commit": owner_commit,
                "path": str(dest.relative_to(self.repo_root)),
            }
        )
        index["versions"] = versions
        index["active_version"] = version
        self._save_index(index)

        return {
            "ok": True,
            "package_version": version,
            "content_digest": content_digest,
            "package_digest": package_digest,
            "course_ids": package["course_ids"],
            "path": str(dest.relative_to(self.repo_root)),
            "signature_ok": self.verify_version(version),
            "learner_key_leak": False,
            "reauthored_in_device_os": False,
        }

    def verify_version(self, version: str | None = None) -> bool:
        index = self._load_index()
        version = version or index.get("active_version")
        if not version:
            return False
        pkg_path = self.root / "versions" / version / "PACKAGE.json"
        if not pkg_path.exists():
            return False
        package = _read_json(pkg_path)
        sig = package.get("signature") or {}
        digest = package.get("package_digest")
        if not digest or not sig.get("signature_hex"):
            return False
        return bool(dev_keys.verify_bytes(self.repo_root, digest.encode("utf-8"), sig["signature_hex"]))

    def activate(self, version: str) -> dict[str, Any]:
        index = self._load_index()
        known = {v.get("package_version") for v in index.get("versions", [])}
        if version not in known:
            return {"ok": False, "error": "version_unknown", "version": version}
        if not self.verify_version(version):
            return {"ok": False, "error": "signature_invalid", "version": version}
        previous = index.get("active_version")
        index["active_version"] = version
        index["last_migration"] = {
            "from": previous,
            "to": version,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "kind": "activate",
        }
        self._save_index(index)
        return {"ok": True, "active_version": version, "previous": previous}

    def rollback(self, to_version: str) -> dict[str, Any]:
        result = self.activate(to_version)
        if result.get("ok"):
            index = self._load_index()
            mig = dict(index.get("last_migration") or {})
            mig["kind"] = "rollback"
            index["last_migration"] = mig
            self._save_index(index)
            result["kind"] = "rollback"
        return result

    def view(self, role: str, *, version: str | None = None) -> dict[str, Any]:
        index = self._load_index()
        version = version or index.get("active_version")
        if not version:
            return {"ok": False, "error": "no_active_version"}
        if not self.verify_version(version):
            return {"ok": False, "error": "signature_invalid", "version": version}
        role = role.lower().strip()
        if role not in {"learner", "teacher", "student"}:
            return {"ok": False, "error": "role_unknown", "role": role}
        if role == "student":
            role = "learner"
        path = self.root / "versions" / version / ("learner_ingest.json" if role == "learner" else "teacher_ingest.json")
        doc = _read_json(path)
        if role == "learner":
            doc = _strip_learner_secrets(doc)
            leak = self._forbidden_present(doc)
            if leak:
                return {"ok": False, "error": "learner_key_leak", "keys": sorted(leak)}
        return {
            "ok": True,
            "role": role,
            "package_version": version,
            "course_ids": [c.get("course_id") for c in doc.get("courses", [])],
            "doc": doc,
            "offline_cache_present": (self.root / "versions" / version / "offline_cache").is_dir(),
        }

    @staticmethod
    def _forbidden_present(obj: Any, found: set[str] | None = None) -> set[str]:
        found = found if found is not None else set()
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k in LEARNER_FORBIDDEN_KEYS:
                    found.add(k)
                WaikeOwnerPackageStore._forbidden_present(v, found)
        elif isinstance(obj, list):
            for item in obj:
                WaikeOwnerPackageStore._forbidden_present(item, found)
        return found
