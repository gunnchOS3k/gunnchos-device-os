"""Cont VI cross-repo scenario hooks (digital) — soft links to sibling repos.

These hooks document and lightly probe sibling workspaces without requiring them
to be present. Physical / production claims are never made here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any


CLAIM_BOUNDARY = (
    "Cross-repo digital hooks only. Sibling absence is non-fatal. "
    "Not FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE."
)


def _repos_root() -> Path:
    return Path(__file__).resolve().parents[2]


HOOKS = (
    {
        "id": "gunnchai_ai_interface",
        "repo": "gunnchAI3k",
        "purpose": "ai_interface local request / capability discovery",
        "probe": ("README.md", "pyproject.toml", "package.json"),
    },
    {
        "id": "edge_io_ring",
        "repo": "edge-io-measurement-node",
        "purpose": "ring service software path vs firmware",
        "probe": ("README.md", "CMakeLists.txt", "west.yml"),
    },
    {
        "id": "field_kit_control_plane",
        "repo": "gunnchos-7gc-ai-ran-field-kit",
        "purpose": "program control plane / requirements trace",
        "probe": ("README.md", "control_plane"),
    },
    {
        "id": "beatlink_game",
        "repo": "beatlink-party-game",
        "purpose": "fourth game category content source",
        "probe": ("README.md",),
    },
)


def probe_hooks(repos_root: Path | None = None) -> dict[str, Any]:
    root = repos_root or _repos_root()
    rows = []
    for hook in HOOKS:
        repo_path = root / hook["repo"]
        present = repo_path.exists()
        probes = []
        for rel in hook["probe"]:
            p = repo_path / rel
            probes.append({"path": rel, "exists": p.exists()})
        rows.append(
            {
                **hook,
                "present": present,
                "probes": probes,
                "usable": present and any(p["exists"] for p in probes),
            }
        )
    return {
        "schema": "gunnchos.cross_repo.cont_vi_hooks.v1",
        "repos_root": str(root),
        "hooks": rows,
        "present_count": sum(1 for r in rows if r["present"]),
        "claim_boundary": CLAIM_BOUNDARY,
        "full_gunnchos_platform_digital_complete": False,
        "mock": False,
    }
