"""CX2H path helpers — isolated from Device Lab / predecessor CX evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

CX2G_OVERLAY_REL = "os_build/cx2g_linux_lab/overlays/cx2g-aarch64.qcow2"
CX2H_OVERLAY_REL = "os_build/cx2h_linux_lab/overlays/cx2h-aarch64.qcow2"


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx2h_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2h_linux_lab"


def cx2g_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2g_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx2h"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx2h_lab_root(repo)
    for sub in (
        "config",
        "scripts",
        "work",
        "images",
        "overlays",
        "evidence",
        "ssh",
        "seed",
        "dist",
        "captures",
        "flatpak",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
