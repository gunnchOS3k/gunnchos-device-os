"""CX3.2 path helpers — isolated evidence/lab roots."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

EXPECTED_CX31_TIP = "33673b4c6bfde858df526bd4b0cddf36d450336f"
EXPECTED_WAIKE_MAIN = "34fb050ccabec813cef4811d64581b32453e1ec2"


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx32_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx3_2_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx3_2"


def career_data_root(repo: Optional[Path] = None) -> Path:
    return cx32_lab_root(repo) / "work" / "career"


def share_data_root(repo: Optional[Path] = None) -> Path:
    return cx32_lab_root(repo) / "work" / "share"


def verifier_cache_root(repo: Optional[Path] = None) -> Path:
    return cx32_lab_root(repo) / "work" / "verifier_cache"


def wallet_data_root(repo: Optional[Path] = None) -> Path:
    return cx32_lab_root(repo) / "work" / "wallet"


def portfolio_data_root(repo: Optional[Path] = None) -> Path:
    return cx32_lab_root(repo) / "work" / "portfolio"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx32_lab_root(repo)
    for sub in (
        "config", "scripts", "work", "work/wallet", "work/portfolio", "work/career",
        "work/share", "work/verifier_cache", "work/exports", "work/resume",
        "images", "overlays", "evidence", "ssh", "seed", "dist", "captures",
    ):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root
