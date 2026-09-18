"""CX2E path helpers — isolated namespaces only."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

DEVICE_LAB_FORBIDDEN = (
    "os_build/device_lab_interactive_guest/artifacts",
    "os_build/device_lab_interactive_guest/pipeline",
)


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx2e_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2e_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx2e"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx2e_lab_root(repo)
    for sub in (
        "config",
        "cloud-init",
        "scripts",
        "work",
        "images",
        "overlays",
        "evidence",
        "ssh",
        "seed",
        "dist",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
