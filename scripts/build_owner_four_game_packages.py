#!/usr/bin/env python3
"""Build owner four-game packages into artifacts/wp011r/owner_builds from accepted mains.

Does not commit multi-GB images. Packages only. Uses sibling origin/main SHAs
matching ACCEPTED_MAINS (or live origin/main when pins already refreshed).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import tarfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys_path_insert = ROOT
import sys

sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.owner_four_game_artifacts import (  # noqa: E402
    ACCEPTED_MAINS,
    _discover_sibling,
    _sha256_file,
    owner_builds_root,
    prepare_owner_guest_staging,
)

NODE_VER = "v20.18.1"
NODE_URL = f"https://nodejs.org/dist/{NODE_VER}/node-{NODE_VER}-linux-arm64.tar.xz"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _run(cmd: list[str], *, cwd: Path | None = None) -> None:
    subprocess.run(cmd, cwd=str(cwd) if cwd else None, check=True)


def _write_meta(dest: Path, *, owner_key: str, sha: str, package: str, package_sha: str) -> None:
    meta = {
        "schema": "gunnchos.wp011r.owner_artifact.v1",
        "owner_key": owner_key,
        "accepted_main_sha": sha,
        "package": package,
        "package_sha256": package_sha,
        "built_at_utc": _utc(),
        "SHIPPING_IMAGE": False,
    }
    (dest / "OWNER_ARTIFACT.json").write_text(json.dumps(meta, indent=2) + "\n")


def build_anime(builds: Path, sib: Path, sha: str) -> dict[str, Any]:
    out = builds / "anime-aggressors"
    out.mkdir(parents=True, exist_ok=True)
    staging = out / "_game-godot"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    # Extract game-godot from accepted tip without dirty checkout
    archive = subprocess.check_output(
        ["git", "-C", str(sib), "archive", f"{sha}:game-godot"],
    )
    subprocess.run(["tar", "-xf", "-"], input=archive, cwd=str(staging), check=True)
    # Nest as game-godot/ for guest unpacker
    nested = out / "game-godot-root" / "game-godot"
    if nested.parent.exists():
        shutil.rmtree(nested.parent)
    nested.parent.mkdir(parents=True)
    shutil.move(str(staging), str(nested))
    tar_path = out / "game-godot.tar.gz"
    if tar_path.exists():
        tar_path.unlink()
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(nested, arcname="game-godot")
    shutil.rmtree(nested.parent, ignore_errors=True)
    psha = _sha256_file(tar_path)
    _write_meta(out, owner_key="anime-aggressors", sha=sha, package=tar_path.name, package_sha=psha)
    return {"ok": True, "path": str(tar_path), "sha256": psha, "accepted_main_sha": sha}


def build_pedestrian(builds: Path, sib: Path, sha: str) -> dict[str, Any]:
    out = builds / "pedestrian-pursuit"
    out.mkdir(parents=True, exist_ok=True)
    # Archive whole tree at sha excluding .git
    tar_path = out / "pedestrian-pursuit.tar.gz"
    if tar_path.exists():
        tar_path.unlink()
    # git archive of repo root
    archive = subprocess.check_output(["git", "-C", str(sib), "archive", "--prefix=pedestrian-pursuit/", sha])
    tar_path.write_bytes(archive)  # git archive default is tar
    # recompress as gz if needed — git archive is uncompressed tar
    raw = out / "pedestrian-pursuit.tar"
    raw.write_bytes(archive)
    with tarfile.open(raw, "r:") as tin, tarfile.open(tar_path, "w:gz") as tout:
        for m in tin.getmembers():
            f = tin.extractfile(m)
            tout.addfile(m, f)
    raw.unlink(missing_ok=True)
    psha = _sha256_file(tar_path)
    _write_meta(out, owner_key="pedestrian-pursuit", sha=sha, package=tar_path.name, package_sha=psha)
    return {"ok": True, "path": str(tar_path), "sha256": psha, "accepted_main_sha": sha}


def build_archive(builds: Path, sib: Path, sha: str) -> dict[str, Any]:
    out = builds / "archive-of-life-artifact-world"
    dist = out / "dist"
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    # Prefer live dist if HEAD matches; else checkout files via git archive
    live_sha = subprocess.check_output(["git", "-C", str(sib), "rev-parse", "HEAD"], text=True).strip()
    live_dist = sib / "dist"
    if live_sha == sha and (live_dist / "index.html").is_file():
        shutil.copytree(live_dist, dist, dirs_exist_ok=True)
    else:
        archive = subprocess.check_output(["git", "-C", str(sib), "archive", f"{sha}:dist"])
        subprocess.run(["tar", "-xf", "-"], input=archive, cwd=str(dist), check=True)
    if not (dist / "index.html").is_file():
        # flat archive may place files differently
        return {"ok": False, "error": "archive_dist_index_missing"}
    psha = _sha256_file(dist / "index.html")
    _write_meta(out, owner_key="archive-of-life-artifact-world", sha=sha, package="dist/", package_sha=psha)
    return {"ok": True, "path": str(dist), "sha256": psha, "accepted_main_sha": sha}


def ensure_node_arm64(builds: Path) -> Path:
    node_root = builds / "node"
    node_root.mkdir(parents=True, exist_ok=True)
    existing = list(node_root.glob("node-*-linux-arm64/bin/node"))
    if existing:
        return existing[0]
    txz = node_root / f"node-{NODE_VER}-linux-arm64.tar.xz"
    if not txz.is_file():
        print(f"fetch {NODE_URL}", flush=True)
        urllib.request.urlretrieve(NODE_URL, txz)
    _run(["tar", "-xJf", str(txz), "-C", str(node_root)])
    node = next(node_root.glob("node-*-linux-arm64/bin/node"))
    node.chmod(0o755)
    return node


def _materialize_linked_package_deps(dest_nm: Path, src_link: Path) -> list[str]:
    """Copy pnpm sibling deps next to a linked package (e.g. express → body-parser).

    `rsync --copy-links` materializes the package itself but drops the virtual
    store siblings Node needs at runtime. Recurses newly copied packages so
    transitive deps (es-errors, side-channel, …) land at top-level too.
    """
    if not src_link.exists():
        return []
    queue: list[Path] = [src_link]
    seen: set[str] = set()
    copied: list[str] = []
    while queue:
        cur = queue.pop(0)
        try:
            real = cur.resolve()
        except OSError:
            continue
        parent_nm = real.parent
        if not parent_nm.is_dir():
            continue
        for child in parent_nm.iterdir():
            if child.name.startswith("."):
                continue
            # Scoped packages (@socket.io, …): merge each inner pkg; do not
            # treat an empty first @scope hit as "already seen".
            if child.name.startswith("@") and child.is_dir():
                scope_dest = dest_nm / child.name
                scope_dest.mkdir(parents=True, exist_ok=True)
                for inner in child.iterdir():
                    if inner.name.startswith("."):
                        continue
                    key = f"{child.name}/{inner.name}"
                    if key in seen:
                        continue
                    seen.add(key)
                    idest = scope_dest / inner.name
                    if not (idest / "package.json").is_file():
                        try:
                            if idest.exists():
                                shutil.rmtree(idest)
                            shutil.copytree(
                                inner,
                                idest,
                                symlinks=False,
                                ignore_dangling_symlinks=True,
                                dirs_exist_ok=True,
                            )
                            copied.append(key)
                        except OSError:
                            continue
                    queue.append(inner)
                continue
            if child.name in seen:
                continue
            seen.add(child.name)
            dest = dest_nm / child.name
            if not dest.exists():
                try:
                    if child.is_dir():
                        shutil.copytree(
                            child,
                            dest,
                            symlinks=False,
                            ignore_dangling_symlinks=True,
                            dirs_exist_ok=True,
                        )
                    else:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(child, dest)
                    copied.append(child.name)
                except OSError:
                    continue
            # Follow nested package.json deps via sibling discovery on the
            # *source* tree (pnpm isolates each package under its own store).
            if child.is_dir() or (dest.exists() and dest.is_dir()):
                try:
                    src_pkg = child if child.is_dir() else dest
                    if (src_pkg / "package.json").is_file() or (
                        dest.exists() and (dest / "package.json").is_file()
                    ):
                        # Prefer unresolved symlink target in source nm if present.
                        queue.append(child if child.exists() else dest)
                except OSError:
                    continue
    return copied


def _materialize_pnpm_package(dest_nm: Path, root_pnpm: Path, name: str) -> bool:
    """Copy one package from monorepo .pnpm into dest_nm if missing."""
    if name.startswith("@"):
        scope, _, pkg = name.partition("/")
        dest = dest_nm / scope / pkg
    else:
        dest = dest_nm / name
    if (dest / "package.json").is_file():
        return True
    if not root_pnpm.is_dir():
        return False
    hits: list[Path] = []
    if name.startswith("@"):
        scope, _, pkg = name.partition("/")
        hits = sorted(root_pnpm.glob(f"{scope[1:]}+{pkg}@*/node_modules/{scope}/{pkg}"))
    else:
        hits = sorted(root_pnpm.glob(f"{name}@*/node_modules/{name}"))
    if not hits:
        return False
    src = hits[0]
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            return True
        shutil.copytree(src, dest, symlinks=False, ignore_dangling_symlinks=True)
        _materialize_linked_package_deps(dest_nm, src)
        return True
    except OSError:
        return False


def _ensure_node_runtime_closure(dest_nm: Path, root_pnpm: Path, seeds: list[str]) -> dict[str, Any]:
    """BFS package.json dependencies from seeds until closure or missing."""
    missing: list[str] = []
    resolved: list[str] = []
    queue = list(seeds)
    seen: set[str] = set()
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        if name.startswith("@"):
            scope, _, pkg = name.partition("/")
            present = (dest_nm / scope / pkg / "package.json").is_file()
        else:
            present = (dest_nm / name / "package.json").is_file()
        if not present and not _materialize_pnpm_package(dest_nm, root_pnpm, name):
            missing.append(name)
            continue
        if not present and not (
            (dest_nm / name / "package.json").is_file()
            if not name.startswith("@")
            else (dest_nm / name.split("/")[0] / name.split("/", 1)[1] / "package.json").is_file()
        ):
            # rematerialize may have filled it
            if name.startswith("@"):
                scope, _, pkg = name.partition("/")
                if not (dest_nm / scope / pkg / "package.json").is_file():
                    missing.append(name)
                    continue
            elif not (dest_nm / name / "package.json").is_file():
                missing.append(name)
                continue
        resolved.append(name)
        if name.startswith("@"):
            scope, _, pkg = name.partition("/")
            pkg_path = dest_nm / scope / pkg / "package.json"
        else:
            pkg_path = dest_nm / name / "package.json"
        if not pkg_path.is_file():
            continue
        try:
            deps = json.loads(pkg_path.read_text(encoding="utf-8")).get("dependencies") or {}
        except json.JSONDecodeError:
            continue
        for dep in deps:
            if dep not in seen:
                queue.append(dep)
    # Critical gate: express + socket.io scoped emitter must resolve.
    critical_ok = (
        (dest_nm / "body-parser" / "package.json").is_file()
        and (dest_nm / "es-errors" / "package.json").is_file()
        and (dest_nm / "@socket.io" / "component-emitter" / "package.json").is_file()
    )
    return {
        "resolved": resolved,
        "missing": missing,
        "ok": critical_ok and not missing,
        "critical_ok": critical_ok,
    }


def build_beatlink(builds: Path, sib: Path, sha: str) -> dict[str, Any]:
    out = builds / "beatlink-party"
    web = out / "web"
    server = out / "server_deploy"
    for p in (web, server):
        if p.exists():
            shutil.rmtree(p)
    live_sha = subprocess.check_output(["git", "-C", str(sib), "rev-parse", "HEAD"], text=True).strip()
    # Prefer apps/web/dist + apps/server (pnpm deploy-like)
    web_src = sib / "apps" / "web" / "dist"
    if not (web_src / "index.html").is_file():
        web_src = sib / "apps" / "web"
    server_src = sib / "apps" / "server"
    if live_sha != sha:
        return {"ok": False, "error": "beatlink_head_not_accepted_main", "head": live_sha, "want": sha}
    if not (web_src / "index.html").is_file():
        return {"ok": False, "error": "beatlink_web_missing"}
    if not (server_src / "dist" / "index.js").is_file():
        return {"ok": False, "error": "beatlink_server_dist_missing"}
    shutil.copytree(web_src, web)
    # server_deploy: dist + package.json + node_modules if present
    server.mkdir(parents=True)
    shutil.copytree(server_src / "dist", server / "dist")
    for name in ("package.json", "package-lock.json"):
        src = server_src / name
        if src.is_file():
            shutil.copy2(src, server / name)
    # Owner release catalog required at runtime (RoomManager resolves ../../../../release).
    release_src = sib / "release"
    release_dst = out / "release"
    if release_dst.exists():
        shutil.rmtree(release_dst)
    if (release_src / "ACHIEVEMENTS.json").is_file():
        shutil.copytree(
            release_src,
            release_dst,
            ignore=shutil.ignore_patterns("*.md", ".git"),
        )
    nm = server_src / "node_modules"
    dest_nm = server / "node_modules"
    if nm.is_dir():
        # pnpm uses symlinks; materialize and skip dangling
        subprocess.run(
            [
                "rsync",
                "-a",
                "--copy-links",
                "--exclude",
                ".cache",
                f"{nm}/",
                f"{dest_nm}/",
            ],
            check=False,
        )
        if not dest_nm.is_dir():
            shutil.copytree(
                nm,
                dest_nm,
                symlinks=True,
                ignore_dangling_symlinks=True,
                dirs_exist_ok=True,
            )
        # Express (and friends) need pnpm virtual-store siblings like body-parser.
        materialized: list[str] = []
        for pkg in ("express", "cors", "socket.io", "ioredis", "socket.io-client"):
            materialized.extend(_materialize_linked_package_deps(dest_nm, nm / pkg))
        # Second pass from monorepo .pnpm for newly materialized packages.
        root_pnpm = sib / "node_modules" / ".pnpm"
        for pkg in list(dict.fromkeys(materialized)):
            src_candidate = nm / pkg
            if not src_candidate.exists() and root_pnpm.is_dir():
                hits = sorted(root_pnpm.glob(f"{pkg}@*/node_modules/{pkg}"))
                if hits:
                    src_candidate = hits[0]
            if src_candidate.exists():
                materialized.extend(_materialize_linked_package_deps(dest_nm, src_candidate))
        # Full dependency closure from package.json seeds (fixes es-errors, etc.).
        seeds = [
            "express",
            "cors",
            "socket.io",
            "socket.io-parser",
            "socket.io-adapter",
            "engine.io",
            "ioredis",
            "socket.io-client",
            "body-parser",
            "@socket.io/component-emitter",
        ]
        closure = _ensure_node_runtime_closure(dest_nm, root_pnpm, seeds=seeds)
    else:
        closure = {"ok": False, "missing": ["node_modules"], "resolved": []}
    ensure_node_arm64(builds)
    psha = _sha256_file(server / "dist" / "index.js")
    body_ok = (dest_nm / "body-parser" / "package.json").is_file()
    es_ok = (dest_nm / "es-errors" / "package.json").is_file()
    emitter_ok = (dest_nm / "@socket.io" / "component-emitter" / "package.json").is_file()
    if not body_ok or not es_ok or not emitter_ok:
        # Last-resort: pull from monorepo .pnpm express/socket store.
        root_pnpm = sib / "node_modules" / ".pnpm"
        hits = sorted(root_pnpm.glob("express@*/node_modules/body-parser")) if root_pnpm.is_dir() else []
        if hits:
            _materialize_linked_package_deps(dest_nm, hits[0].parent / "express")
        _materialize_pnpm_package(dest_nm, root_pnpm, "@socket.io/component-emitter")
        _materialize_pnpm_package(dest_nm, root_pnpm, "socket.io-parser")
        closure = _ensure_node_runtime_closure(
            dest_nm,
            root_pnpm,
            seeds=[
                "express",
                "cors",
                "socket.io",
                "socket.io-parser",
                "ioredis",
                "socket.io-client",
                "body-parser",
                "qs",
                "side-channel",
                "@socket.io/component-emitter",
            ],
        )
        body_ok = (dest_nm / "body-parser" / "package.json").is_file()
        es_ok = (dest_nm / "es-errors" / "package.json").is_file()
        emitter_ok = (dest_nm / "@socket.io" / "component-emitter" / "package.json").is_file()
    # Runtime smoke on host before packaging (catches truncated/scoped gaps).
    smoke = {"ok": False}
    try:
        smoke_cp = subprocess.run(
            [
                "node",
                "-e",
                "require('express'); require('socket.io'); require('@socket.io/component-emitter'); "
                "require('es-errors/type'); console.log('BEATLINK_NM_OK')",
            ],
            cwd=str(server),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        smoke = {
            "ok": "BEATLINK_NM_OK" in (smoke_cp.stdout or ""),
            "stdout": (smoke_cp.stdout or "")[-200:],
            "stderr": (smoke_cp.stderr or "")[-400:],
            "returncode": smoke_cp.returncode,
        }
    except Exception as exc:  # noqa: BLE001
        smoke = {"ok": False, "error": str(exc)[:200]}
    _write_meta(out, owner_key="beatlink-party", sha=sha, package="web+server_deploy", package_sha=psha)
    if not (body_ok and es_ok and emitter_ok and smoke.get("ok") and closure.get("critical_ok", closure.get("ok"))):
        return {
            "ok": False,
            "error": "node_runtime_closure_incomplete",
            "web": str(web),
            "server": str(server),
            "accepted_main_sha": sha,
            "body_parser_present": body_ok,
            "es_errors_present": es_ok,
            "socketio_component_emitter_present": emitter_ok,
            "smoke": smoke,
            "closure": closure,
        }
    return {
        "ok": True,
        "web": str(web),
        "server": str(server),
        "sha256": psha,
        "accepted_main_sha": sha,
        "body_parser_present": True,
        "es_errors_present": True,
        "socketio_component_emitter_present": True,
        "smoke": smoke,
        "closure": closure,
    }


def main() -> int:
    builds = owner_builds_root(ROOT)
    builds.mkdir(parents=True, exist_ok=True)
    report: dict[str, Any] = {"at_utc": _utc(), "games": {}}
    for key, spec in ACCEPTED_MAINS.items():
        sib = _discover_sibling(ROOT, spec["sibling"])
        sha = spec["accepted_main_sha"]
        if not sib:
            report["games"][key] = {"ok": False, "error": "sibling_missing"}
            continue
        # Prefer origin/main if it matches pin
        origin = subprocess.check_output(
            ["git", "-C", str(sib), "rev-parse", "origin/main"], text=True
        ).strip()
        if origin == sha:
            use_sha = origin
        else:
            use_sha = sha
        print(f"build {key} @{use_sha[:12]} from {sib}", flush=True)
        try:
            if key == "anime-aggressors":
                report["games"][key] = build_anime(builds, sib, use_sha)
            elif key == "pedestrian-pursuit":
                report["games"][key] = build_pedestrian(builds, sib, use_sha)
            elif key == "archive-of-life-artifact-world":
                report["games"][key] = build_archive(builds, sib, use_sha)
            elif key == "beatlink-party":
                report["games"][key] = build_beatlink(builds, sib, use_sha)
        except Exception as exc:  # noqa: BLE001
            report["games"][key] = {"ok": False, "error": str(exc)}
    staging = prepare_owner_guest_staging(ROOT)
    report["staging"] = {
        "ok": staging.get("ok"),
        "path": staging.get("staging"),
        "games": {
            k: {"ok": (v or {}).get("ok", "guest_package" in (v or {})), "error": (v or {}).get("error")}
            for k, v in (staging.get("games") or {}).items()
        },
    }
    out = ROOT / "artifacts/wp011r/owner_builds/BUILD_REPORT.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2), flush=True)
    return 0 if staging.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
