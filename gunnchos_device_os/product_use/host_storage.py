"""Host free-space preflight for PRODUCT-USE QEMU persona runs.

HARD rule (PRODUCT-USE-RC-002):
  HOST_FREE_SPACE_REQUIRED  >= 25 GiB
  HOST_FREE_SPACE_PREFERRED >= 40 GiB

Prefer-12 from prior cycle is superseded. Never invent guest PASS when blocked.
Auto-cleanup may ONLY delete regenerable repo-local artifacts.
"""
from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REQUIRED_GIB = 25.0
PREFERRED_GIB = 40.0
GIB = float(2**30)

# Safe-to-delete regenerable roots under the device-os workspace (relative).
# NOTE: do NOT delete os_build/device_lab_interactive_guest/artifacts (primary
# interactive-root qcow2) — that is expensive to reprovision. Only scratch
# overlays / temp run dirs / caches.
REGENERABLE_REL_PATHS = (
    "artifacts/product_use/interactive_guest_session",
    "artifacts/product_use/interactive_guest_session_s1",
    "artifacts/product_use/interactive_guest_session_s1_probe",
    "artifacts/wp011r/interactive_guest_session",
    "artifacts/wp011r/cache",
    "artifacts/wp011r/dsxl_s1",
    ".pytest_cache",
    "scripts/__pycache__",
    "gunnchos_device_os/product_use/__pycache__",
    "tests/product_use/__pycache__",
)

# NEVER delete (safety classification).
NEVER_DELETE_CLASS = (
    "Cursor state.vscdb / IDE state",
    "user Downloads / docs outside regenerable roots",
    "repos/.git",
    "canonical evidence JSON under artifacts/product_use/VP_*",
    "model weights / GGUF",
    "CAD / EDA",
    "source media",
    "unknown files outside regenerable allowlist",
)


@dataclass(frozen=True)
class HostSpaceReport:
    path: str
    free_gib: float
    total_gib: float
    used_gib: float
    required_ok: bool
    preferred_ok: bool
    blocked: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "free_gib": round(self.free_gib, 2),
            "total_gib": round(self.total_gib, 2),
            "used_gib": round(self.used_gib, 2),
            "HOST_FREE_SPACE_REQUIRED_GIB": REQUIRED_GIB,
            "HOST_FREE_SPACE_PREFERRED_GIB": PREFERRED_GIB,
            "required_ok": self.required_ok,
            "preferred_ok": self.preferred_ok,
            "HOST_RESOURCE_BLOCKED": self.blocked,
        }


def measure_free_space(path: str | Path | None = None) -> HostSpaceReport:
    target = str(path or os.environ.get("HOST_SPACE_PATH") or "/")
    total, used, free = shutil.disk_usage(target)
    free_gib = free / GIB
    return HostSpaceReport(
        path=target,
        free_gib=free_gib,
        total_gib=total / GIB,
        used_gib=used / GIB,
        required_ok=free_gib >= REQUIRED_GIB,
        preferred_ok=free_gib >= PREFERRED_GIB,
        blocked=free_gib < REQUIRED_GIB,
    )


def largest_candidates(repo_root: Path, *, limit: int = 12) -> list[dict[str, Any]]:
    """Rank large paths under repo for operator triage (classified)."""
    root = Path(repo_root).resolve()
    rows: list[dict[str, Any]] = []
    scan = [
        root / "os_build",
        root / "artifacts",
        root / ".pytest_cache",
        root / "results",
    ]
    for base in scan:
        if not base.exists():
            continue
        try:
            for child in base.iterdir():
                if child.name == ".git":
                    continue
                size = _dir_size(child)
                rel = str(child.relative_to(root)) if child.is_relative_to(root) else str(child)
                regenerable = any(rel == r or rel.startswith(r + "/") for r in REGENERABLE_REL_PATHS)
                rows.append(
                    {
                        "path": rel,
                        "bytes": size,
                        "gib": round(size / GIB, 3),
                        "safety": "REGENERABLE_REPO_LOCAL" if regenerable else "REVIEW_BEFORE_DELETE",
                    }
                )
        except OSError:
            continue
    rows.sort(key=lambda r: r["bytes"], reverse=True)
    return rows[:limit]


def cleanup_regenerable(repo_root: Path, *, dry_run: bool = False) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    removed: list[str] = []
    skipped: list[str] = []
    for rel in REGENERABLE_REL_PATHS:
        path = root / rel
        if not path.exists():
            skipped.append(rel)
            continue
        if dry_run:
            removed.append(f"DRY_RUN:{rel}")
            continue
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        else:
            try:
                path.unlink()
            except OSError:
                skipped.append(rel)
                continue
        removed.append(rel)
    return {
        "ok": True,
        "removed": removed,
        "skipped_missing": skipped,
        "never_delete_class": list(NEVER_DELETE_CLASS),
    }


def preflight(repo_root: Path, *, cleanup_if_tight: bool = True) -> dict[str, Any]:
    """Measure; optionally clean regenerable; re-measure; block if still <25 GiB."""
    before = measure_free_space(repo_root)
    actions: list[str] = []
    cleanup_result = None
    if (not before.preferred_ok) and cleanup_if_tight:
        cleanup_result = cleanup_regenerable(repo_root, dry_run=False)
        actions.append("cleanup_regenerable")
    after = measure_free_space(repo_root)
    report = {
        "schema": "gunnchos.product_use.host_storage_preflight.v1",
        "before": before.as_dict(),
        "after": after.as_dict(),
        "actions": actions,
        "cleanup": cleanup_result,
        "largest_candidates": largest_candidates(repo_root),
        "never_delete_class": list(NEVER_DELETE_CLASS),
        "HOST_RESOURCE_BLOCKED": after.blocked,
        "qemu_persona_runs_allowed": not after.blocked,
        "claim_boundary": (
            "Host free-space gate only. Does not invent guest PASS. "
            "Cursor does not merge."
        ),
    }
    if after.blocked:
        report["error"] = "HOST_RESOURCE_BLOCKED"
        report["message"] = (
            f"Host free space {after.free_gib:.2f} GiB < required {REQUIRED_GIB} GiB. "
            "STOP — no QEMU persona run; no invented guest PASS."
        )
    return report


def _dir_size(path: Path) -> int:
    total = 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    for root, _dirs, files in os.walk(path, followlinks=False):
        for name in files:
            try:
                total += (Path(root) / name).stat().st_size
            except OSError:
                continue
    return total
