#!/usr/bin/env python3
"""Import accepted first-party game artifacts from sibling workspaces.

Does not vendor entire game repos. Beat Link web/server dists are copied;
others record/verify workspace artifacts via PACKAGE_MANIFEST.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def repos_root() -> Path:
    return repo_root().parents[0]


def tree_sha(path: Path) -> str:
    h = hashlib.sha256()
    for p in sorted(path.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(path))
        if "node_modules" in rel.split("/"):
            continue
        h.update(rel.encode())
        h.update(b"\0")
        h.update(hashlib.sha256(p.read_bytes()).digest())
    return h.hexdigest()


def import_beatlink() -> dict:
    src = repos_root() / "beatlink-party"
    sha = subprocess.check_output(["git", "-C", str(src), "rev-parse", "HEAD"], text=True).strip()
    web_src = src / "apps/web/dist"
    if not web_src.exists():
        raise SystemExit("beatlink web dist missing; build with: pnpm -r build")
    dest = repo_root() / "games/beatlink-party-web"
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(web_src, dest)
    pkg = repo_root() / "packages/first_party_games/beatlink-party"
    pkg.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src / "docker-compose.yml", pkg / "docker-compose.yml")
    server_dest = pkg / "server"
    if server_dest.exists():
        shutil.rmtree(server_dest)
    server_dest.mkdir(parents=True)
    shutil.copy2(src / "apps/server/package.json", server_dest / "package.json")
    if (src / "apps/server/dist").exists():
        shutil.copytree(src / "apps/server/dist", server_dest / "dist")
    digest = tree_sha(dest)
    manifest = {
        "schema": "gunnchos.first_party_game_package.v1",
        "id": "beatlink-party-web",
        "source_repo": "beatlink-party",
        "accepted_sha": sha,
        "build_command": "pnpm -r build",
        "artifact_path": "apps/web/dist",
        "imported_path": "games/beatlink-party-web",
        "artifact_tree_sha256": digest,
        "stub_content": False,
        "permissions": ["files_read", "network", "microphone"],
        "device_roles": ["student", "handheld", "ds_xl", "dock_host"],
    }
    (pkg / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (dest / "PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--beatlink-only", action="store_true")
    args = parser.parse_args()
    report = {"beatlink": import_beatlink()}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
