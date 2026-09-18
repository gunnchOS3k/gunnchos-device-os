"""CX3.3 path helpers — isolated evidence/lab roots."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

EXPECTED_CX31_TIP = "33673b4c6bfde858df526bd4b0cddf36d450336f"
EXPECTED_CX32_TIP = "47c860c97f6deae2bf83633863530da8dea94af8"
EXPECTED_WAIKE_MAIN = "34fb050ccabec813cef4811d64581b32453e1ec2"
DEVICE_LAB_134_TIP = "ddc7788b68b2b0467268ba144175e4047a21a6c3"


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx33_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx3_3_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx3_3"


def education_data_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "education"


def skill_graph_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "skill_graph"


def career_package_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "career_package"


def recovery_profile_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "recovery_profile"


def wallet_data_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "wallet"


def portfolio_data_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "portfolio"


def career_data_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "career"


def share_data_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "share"


def verifier_cache_root(repo: Optional[Path] = None) -> Path:
    return cx33_lab_root(repo) / "work" / "verifier_cache"


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx33_lab_root(repo)
    for sub in (
        "config",
        "scripts",
        "work",
        "work/wallet",
        "work/portfolio",
        "work/career",
        "work/share",
        "work/verifier_cache",
        "work/education",
        "work/skill_graph",
        "work/career_package",
        "work/recovery_profile",
        "work/exports",
        "work/resume",
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
