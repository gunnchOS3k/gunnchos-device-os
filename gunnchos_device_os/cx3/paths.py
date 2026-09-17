"""CX3 path helpers — isolated evidence/lab roots."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

CX2H4_OVERLAY_REL = "os_build/cx2h4_linux_lab/overlays/cx2h4-aarch64.qcow2"
CX3_OVERLAY_REL = "os_build/cx3_linux_lab/overlays/cx3-aarch64.qcow2"
EXPECTED_CX2H4_TIP = "5381963b7734511d58d18c279d8e941f858896f8"


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx3_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx3_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx3"


def wallet_data_root(repo: Optional[Path] = None) -> Path:
    return cx3_lab_root(repo) / "work" / "wallet"


def portfolio_data_root(repo: Optional[Path] = None) -> Path:
    return cx3_lab_root(repo) / "work" / "portfolio"


def issuer_ephemeral_root(repo: Optional[Path] = None) -> Path:
    """Ephemeral issuer keys live under /tmp — never committed."""
    return Path("/tmp/cx3-issuer-ephemeral")


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx3_lab_root(repo)
    for sub in (
        "config",
        "scripts",
        "work",
        "work/wallet",
        "work/portfolio",
        "work/exports",
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
