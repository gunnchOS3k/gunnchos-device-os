"""CX4 path helpers — evidence, lab, canonical store (worktree-independent)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

EXPECTED_CX33_TIP = "472819b839cd852459cc484c40d8b86eb5f86e96"
DEVICE_LAB_134_TIP = "ddc7788b68b2b0467268ba144175e4047a21a6c3"
CX2H2_OVERLAY_NAME = "cx2h2-aarch64.qcow2"
CX2H3_OVERLAY_NAME = "cx2h3-aarch64.qcow2"
CX2H4_OVERLAY_NAME = "cx2h4-aarch64.qcow2"
CX4_OVERLAY_NAME = "cx4-aarch64.qcow2"
LOCK_PATH = Path("/tmp/gunnchos-cx-qemu.lock")


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def durable_device_os_root(repo: Optional[Path] = None) -> Path:
    """Prefer the non-worktree checkout so overlays survive ephemeral worktrees."""
    repo = (repo or repo_root_from_here()).resolve()
    parts = repo.parts
    if ".worktrees" in parts:
        idx = parts.index(".worktrees")
        return Path(*parts[:idx])
    env = os.environ.get("GUNNCHOS_DEVICE_OS_DURABLE_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return repo


def canonical_root(repo: Optional[Path] = None) -> Path:
    env = os.environ.get("GUNNCHOS_CX_CANONICAL_ROOT")
    if env:
        return Path(env).expanduser().resolve()
    return durable_device_os_root(repo) / "os_build" / "cx_canonical"


def cx4_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx4_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx4_0"


def readiness_docs_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "docs" / "complete-experience" / "cx4_readiness"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx4_lab_root(repo)
    for sub in (
        "config",
        "scripts",
        "work",
        "work/a11y",
        "work/printer",
        "work/av",
        "work/peripherals",
        "work/support",
        "work/firmware",
        "images",
        "overlays",
        "evidence",
        "ssh",
        "seed",
        "dist",
        "captures",
        "harnesses",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def ensure_canonical_tree(repo: Optional[Path] = None) -> Path:
    root = canonical_root(repo)
    for sub in ("immutable", "campaigns", "provenance", "preflight"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
