"""Cont VII cross-repo E2E hooks — prefer real packages when present."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

CLAIM_BOUNDARY = (
    "Cross-repo digital E2E hooks. Sibling absence is non-fatal for probe, "
    "but packaged Beat Link inside device-os must be real."
)


def _repos_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _device_os() -> Path:
    return Path(__file__).resolve().parents[1]


HOOKS = (
    {
        "id": "E2E-01",
        "title": "QEMU boot → WAIKE → gunnchAI tutoring",
        "local": ("apps/waike_learning/index.html",),
        "sibling": ("gunnchAI3k", ("README.md", "package.json", "pyproject.toml")),
    },
    {
        "id": "E2E-02",
        "title": "Creator Studio → local build/log",
        "local": ("apps/creator_studio/index.html",),
        "sibling": None,
    },
    {
        "id": "E2E-03",
        "title": "Device Manager → service diagnostics",
        "local": ("apps/device_management/index.html",),
        "sibling": None,
    },
    {
        "id": "E2E-04",
        "title": "Packaged Anime",
        "local": ("games/anime-aggressors-web/PACKAGE_MANIFEST.json",),
        "sibling": ("anime-aggressors", ("apps/web/dist/index.html", "README.md")),
    },
    {
        "id": "E2E-05",
        "title": "Packaged Pedestrian",
        "local": ("games/foot-racing-web/PACKAGE_MANIFEST.json",),
        "sibling": ("pedestrian-pursuit", ("project.godot", "README.md")),
    },
    {
        "id": "E2E-06",
        "title": "Packaged Archive",
        "local": ("games/earth-species-web/PACKAGE_MANIFEST.json",),
        "sibling": ("archive-of-life-artifact-world", ("dist/index.html", "README.md")),
    },
    {
        "id": "E2E-07",
        "title": "Packaged Beat Link → Redis → clients",
        "local": (
            "games/beatlink-party-web/index.html",
            "games/beatlink-party-web/PACKAGE_MANIFEST.json",
            "packages/first_party_games/beatlink-party/docker-compose.yml",
        ),
        "sibling": ("beatlink-party", ("apps/web/dist/index.html", "docker-compose.yml")),
    },
    {
        "id": "E2E-08",
        "title": "Ring firmware sim → gunnchOS ring",
        "local": ("gunnchos_device_os/runtime/adapters.py",),
        "sibling": ("edge-io-measurement-node", ("README.md", "west.yml", "CMakeLists.txt")),
    },
    {
        "id": "E2E-11",
        "title": "Wi-Fi → cellular → Ethernet → simulated NTN",
        "local": ("gunnchos_device_os/connectivity/cellular_stack.py",),
        "sibling": None,
    },
)


def probe_hooks(repos_root: Path | None = None) -> dict[str, Any]:
    root = repos_root or _repos_root()
    dos = _device_os()
    rows = []
    for hook in HOOKS:
        local_ok = all((dos / rel).exists() for rel in hook["local"])
        sibling = hook.get("sibling")
        sibling_present = False
        sibling_usable = False
        probes = []
        if sibling:
            repo_name, probe_files = sibling
            repo_path = root / repo_name
            sibling_present = repo_path.exists()
            for rel in probe_files:
                exists = (repo_path / rel).exists()
                probes.append({"path": rel, "exists": exists})
            sibling_usable = sibling_present and any(p["exists"] for p in probes)
        beatlink_stub = False
        if hook["id"] == "E2E-07":
            idx = dos / "games/beatlink-party-web/index.html"
            if idx.exists():
                text = idx.read_text(encoding="utf-8", errors="ignore")
                beatlink_stub = "GUNNCHOS_GAME_STUB_CONTENT=true" in text or "DEV stub" in text
        rows.append(
            {
                "id": hook["id"],
                "title": hook["title"],
                "local_ok": local_ok and not beatlink_stub,
                "sibling_present": sibling_present,
                "sibling_usable": sibling_usable,
                "probes": probes,
                "usable": local_ok and not beatlink_stub,
            }
        )
    man_path = dos / "games/beatlink-party-web/PACKAGE_MANIFEST.json"
    beat_meta = json.loads(man_path.read_text()) if man_path.exists() else {}
    return {
        "schema": "gunnchos.cross_repo.cont_vii_hooks.v1",
        "repos_root": str(root),
        "hooks": rows,
        "usable_count": sum(1 for r in rows if r["usable"]),
        "beatlink_accepted_sha": beat_meta.get("accepted_sha"),
        "claim_boundary": CLAIM_BOUNDARY,
        "stub_as_product": False,
        "mock": False,
    }
