"""CX2H.4 path helpers — isolated evidence/lab roots."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

CX2H3_OVERLAY_REL = "os_build/cx2h3_linux_lab/overlays/cx2h3-aarch64.qcow2"
CX2H4_OVERLAY_REL = "os_build/cx2h4_linux_lab/overlays/cx2h4-aarch64.qcow2"


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx2h4_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2h4_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx2h4"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx2h4_lab_root(repo)
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
        "https",
        "mail",
        "caldav",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
