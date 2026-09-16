"""CX2F path helpers — isolated namespaces only."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

DEVICE_LAB_FORBIDDEN = (
    "os_build/device_lab_interactive_guest/artifacts",
    "os_build/device_lab_interactive_guest/pipeline",
)

CX2E_OVERLAY_REL = "os_build/cx2e_linux_lab/overlays/cx2e-aarch64.qcow2"


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx2f_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2f_linux_lab"


def cx2e_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2e_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx2f"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx2f_lab_root(repo)
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
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
