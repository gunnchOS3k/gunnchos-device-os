"""Owner-repo FOUR_GAME artifacts at accepted mains (WP-011R.2).

Builds/discovers real owner packages — never device-os HTML recreations,
probe facades, fake save bridges, or Python game mirrors.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.four_game_honest import honest_sha_entry

# PRODUCT-USE-RC-002: pin to current accepted mains (refresh after live GitHub wins).
ACCEPTED_MAINS: dict[str, dict[str, str]] = {
    "anime-aggressors": {
        "owner_repo": "gunnchOS3k/anime-aggressors",
        "accepted_main_sha": "9770674fdce94e19270d0f5683e6fcf74b4111f3",
        "sibling": "anime-aggressors",
        "lab_id": "anime-aggressors",
        "note": "accepted-main after #76 GAME-RC-003; do not reclassify ALPHA as RC",
    },
    "pedestrian-pursuit": {
        "owner_repo": "gunnchOS3k/pedestrian-pursuit",
        "accepted_main_sha": "80ca8ee7e96da0e86184fe24b10831265588c1a3",
        "sibling": "pedestrian-pursuit",
        "lab_id": "foot-racing",
        "note": "accepted-main after #17 GAME-RC-003",
    },
    "archive-of-life-artifact-world": {
        "owner_repo": "gunnchOS3k/archive-of-life-artifact-world",
        "accepted_main_sha": "74f5761cdc47fdb7de34ff93b402fac311bf2e47",
        "sibling": "archive-of-life-artifact-world",
        "lab_id": "earth-species",
        "note": "accepted-main after #30 GAME-RC-004",
    },
    "beatlink-party": {
        "owner_repo": "gunnchOS3k/beatlink-party",
        "accepted_main_sha": "4fc8fe017634ba6bdab62c676fde1355db0d36e0",
        "sibling": "beatlink-party",
        "lab_id": "beatlink-party",
        "note": "accepted-main after #21 GAME-RC-004",
    },
}

# Lab-facing ids used by existing evidence/scorer keys.
LAB_TO_OWNER = {
    "anime-aggressors": "anime-aggressors",
    "beatlink-party": "beatlink-party",
    "earth-species": "archive-of-life-artifact-world",
    "foot-racing": "pedestrian-pursuit",
}


def owner_builds_root(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "wp011r" / "owner_builds"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _hoist_pnpm_node_modules(node_modules: Path) -> int:
    """Copy pnpm isolated packages to top-level node_modules so Node can resolve them.

    `pnpm deploy` leaves express at a symlink into `.pnpm/.../express` whose sibling
    deps (body-parser, etc.) are invisible once that symlink is dereferenced into a tar.
    """
    pnpm = node_modules / ".pnpm"
    if not pnpm.is_dir():
        return 0
    copied = 0

    def _materialize(src: Path, dest: Path) -> None:
        nonlocal copied
        if dest.exists():
            return
        dest.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src.is_dir():
                shutil.copytree(src, dest, symlinks=False, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dest)
            copied += 1
        except OSError:
            pass

    for pkg_root in pnpm.glob("*/node_modules"):
        for child in pkg_root.iterdir():
            if child.name.startswith("."):
                continue
            if child.name.startswith("@"):
                for inner in child.iterdir():
                    _materialize(inner, node_modules / child.name / inner.name)
            else:
                _materialize(child, node_modules / child.name)
    # Drop pnpm virtual store after hoist — prevents multi-GB / truncated tars.
    try:
        shutil.rmtree(pnpm)
    except OSError:
        pass
    return copied


def _write_verified_targz(src_dir: Path, dest_tar: Path, arcname: str) -> str:
    """Write gzip tar and verify it opens + contains expected root."""
    if dest_tar.exists():
        dest_tar.unlink()
    with tarfile.open(dest_tar, "w:gz", compresslevel=6) as tf:
        tf.add(src_dir, arcname=arcname, filter=_beatlink_tar_filter if arcname == "beatlink-party" else None)
    # Integrity: must open and enumerate without EOFError.
    with tarfile.open(dest_tar, "r:gz") as tf:
        names = tf.getnames()
        if not names or not any(n.startswith(arcname) for n in names):
            raise RuntimeError(f"tar_empty_or_missing_root:{dest_tar}")
    return _sha256_file(dest_tar)


def _beatlink_tar_filter(tarinfo: tarfile.TarInfo) -> tarfile.TarInfo | None:
    """Exclude VCS/tests/maps that bloat guest packages."""
    name = tarinfo.name.replace("\\", "/")
    parts = name.split("/")
    banned = {".git", ".github", ".pnpm", "__pycache__", "test", "tests", ".nyc_output"}
    if any(p in banned for p in parts):
        return None
    if name.endswith((".map", ".ts", ".md")) and "/node_modules/" in f"/{name}/":
        # Keep package README? Drop maps/ts/md under node_modules only.
        if name.endswith(".map") or name.endswith(".ts"):
            return None
    return tarinfo


def _sha256_tree(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(path).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def _discover_sibling(repo_root: Path, name: str) -> Path | None:
    parents = [repo_root.parent, repo_root.parent.parent]
    # Worktree layout: gate-worktrees/X → repos/
    if repo_root.parent.name == "gate-worktrees":
        parents.insert(0, repo_root.parent.parent)
    for parent in parents:
        cand = parent / name
        if cand.is_dir():
            return cand
    absolute = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos") / name
    return absolute if absolute.is_dir() else None


def _git_sha(path: Path) -> str | None:
    try:
        cp = subprocess.run(
            ["git", "-C", str(path), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
            timeout=30,
        )
    except Exception:
        return None
    if cp.returncode != 0:
        return None
    return (cp.stdout or "").strip() or None


def load_owner_artifact_meta(repo_root: Path, owner_key: str) -> dict[str, Any] | None:
    meta = owner_builds_root(repo_root) / owner_key / "OWNER_ARTIFACT.json"
    if not meta.is_file():
        return None
    return json.loads(meta.read_text(encoding="utf-8"))


def verify_accepted_shas(repo_root: Path, *, allow_artifact_pin: bool = True) -> dict[str, Any]:
    """Verify siblings (or packaged OWNER_ARTIFACT pins) match accepted mains."""
    out: dict[str, Any] = {
        "recorded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "games": {},
        "ok": True,
    }
    for key, spec in ACCEPTED_MAINS.items():
        sib = _discover_sibling(repo_root, spec["sibling"])
        sha = _git_sha(sib) if sib else None
        meta = load_owner_artifact_meta(repo_root, key) if allow_artifact_pin else None
        entry = honest_sha_entry(
            accepted_main_sha=spec["accepted_main_sha"],
            sibling_head=sha,
            meta=meta if allow_artifact_pin else None,
            owner_repo=spec["owner_repo"],
            lab_id=spec["lab_id"],
            sibling_path=str(sib) if sib else None,
        )
        out["games"][key] = entry
        if not entry.get("ok"):
            out["ok"] = False
    return out


def prepare_owner_guest_staging(repo_root: Path) -> dict[str, Any]:
    """Assemble guest-facing owner artifact tree (no probe / no fake save bridge)."""
    builds = owner_builds_root(repo_root)
    staging = repo_root / "artifacts" / "wp011r" / "owner_games_guest_bundle"
    staging.mkdir(parents=True, exist_ok=True)
    # Prefer in-place overwrite. Full rmtree can fail on macOS provenance-locked
    # Godot copies; keep those binaries and refresh packages/helpers.

    manifest: dict[str, Any] = {
        "schema": "gunnchos.wp011r.owner_four_game_bundle.v1",
        "recorded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "FORBIDDEN": [
            "device-os HTML recreation",
            "game probe facade",
            "fake save bridge",
            "hardcoded state marker",
            "http.server alone as proof",
            "Python game mirror",
        ],
        "games": {},
        "staging": str(staging),
        "ok": True,
    }

    # Anime Godot project
    anime_tar = builds / "anime-aggressors" / "game-godot.tar.gz"
    anime_meta = load_owner_artifact_meta(repo_root, "anime-aggressors")
    if anime_tar.is_file():
        shutil.copy2(anime_tar, staging / "anime-aggressors.game-godot.tar.gz")
        manifest["games"]["anime-aggressors"] = {
            **(anime_meta or {}),
            "guest_package": "anime-aggressors.game-godot.tar.gz",
            "package_sha256": _sha256_file(anime_tar),
            "install_path": "/root/owner-games/anime-aggressors",
        }
    else:
        manifest["ok"] = False
        manifest["games"]["anime-aggressors"] = {"ok": False, "error": "anime_tar_missing"}

    # Pedestrian Pursuit
    pp_tar = builds / "pedestrian-pursuit" / "pedestrian-pursuit.tar.gz"
    pp_meta = load_owner_artifact_meta(repo_root, "pedestrian-pursuit")
    if pp_tar.is_file():
        shutil.copy2(pp_tar, staging / "pedestrian-pursuit.tar.gz")
        manifest["games"]["pedestrian-pursuit"] = {
            **(pp_meta or {}),
            "guest_package": "pedestrian-pursuit.tar.gz",
            "package_sha256": _sha256_file(pp_tar),
            "install_path": "/root/pedestrian-pursuit",
        }
    else:
        manifest["ok"] = False
        manifest["games"]["pedestrian-pursuit"] = {"ok": False, "error": "pp_tar_missing"}

    # Archive web dist
    archive_dist = builds / "archive-of-life-artifact-world" / "dist"
    archive_meta = load_owner_artifact_meta(repo_root, "archive-of-life-artifact-world")
    if (archive_dist / "index.html").is_file():
        dst = staging / "archive-of-life-artifact-world"
        shutil.copytree(archive_dist, dst, dirs_exist_ok=True)
        with tarfile.open(staging / "archive-of-life-artifact-world.tar.gz", "w:gz") as tf:
            tf.add(dst, arcname="archive-of-life-artifact-world")
        manifest["games"]["archive-of-life-artifact-world"] = {
            **(archive_meta or {}),
            "guest_package": "archive-of-life-artifact-world.tar.gz",
            "package_sha256": _sha256_file(staging / "archive-of-life-artifact-world.tar.gz"),
            "install_path": "/root/owner-games/archive-of-life-artifact-world",
        }
    else:
        manifest["ok"] = False
        manifest["games"]["archive-of-life-artifact-world"] = {
            "ok": False,
            "error": "archive_dist_missing",
        }

    # Beat Link web + server deploy + node binary
    bl_web = builds / "beatlink-party" / "web"
    bl_server = builds / "beatlink-party" / "server_deploy"
    bl_meta = load_owner_artifact_meta(repo_root, "beatlink-party")
    node_root = builds / "node"
    node_bin = None
    for cand in node_root.glob("node-*-linux-arm64/bin/node"):
        node_bin = cand
        break
    if (bl_web / "index.html").is_file() and (bl_server / "dist" / "index.js").is_file() and node_bin:
        bl_dir = staging / "beatlink-party"
        if bl_dir.exists():
            shutil.rmtree(bl_dir, ignore_errors=True)
        bl_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(bl_web, bl_dir / "web", dirs_exist_ok=True)
        # Slim server: dist + package.json + node_modules (materialized; no dangling symlinks)
        shutil.copytree(
            bl_server,
            bl_dir / "server",
            dirs_exist_ok=True,
            symlinks=False,
            ignore_dangling_symlinks=True,
            ignore=shutil.ignore_patterns(
                "tsconfig.json",
                "*.map",
                ".pnpm",
                ".git",
                ".github",
                "__pycache__",
            ),
        )
        hoist_n = _hoist_pnpm_node_modules(bl_dir / "server" / "node_modules")
        # Hard fail if Express cannot resolve es-errors/type on the host before packaging.
        side = bl_dir / "server" / "node_modules" / "es-errors" / "type.js"
        body = bl_dir / "server" / "node_modules" / "body-parser" / "package.json"
        emitter = (
            bl_dir / "server" / "node_modules" / "@socket.io" / "component-emitter" / "package.json"
        )
        if not side.is_file() or not body.is_file() or not emitter.is_file():
            manifest["ok"] = False
            manifest["games"]["beatlink-party"] = {
                "ok": False,
                "error": "beatlink_node_modules_incomplete",
                "es_errors_type": side.is_file(),
                "body_parser": body.is_file(),
                "socketio_component_emitter": emitter.is_file(),
                "pnpm_hoisted_packages": hoist_n,
            }
        else:
            node_dir = bl_dir / "node"
            node_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(node_bin, node_dir / "node")
            (node_dir / "node").chmod(0o755)
            # Owner release catalog (ACHIEVEMENTS.json) required by RoomManager path.
            release_src = builds / "beatlink-party" / "release"
            if (release_src / "ACHIEVEMENTS.json").is_file():
                if (bl_dir / "release").exists():
                    shutil.rmtree(bl_dir / "release")
                shutil.copytree(release_src, bl_dir / "release")
            tar_path = staging / "beatlink-party.tar.gz"
            pkg_sha = _write_verified_targz(bl_dir, tar_path, "beatlink-party")
            # Smoke: extract es-errors/type.js from tar
            with tarfile.open(tar_path, "r:gz") as tf:
                member = tf.getmember("beatlink-party/server/node_modules/es-errors/type.js")
                raw = tf.extractfile(member)
                if raw is None or not raw.read():
                    raise RuntimeError("beatlink_tar_missing_es_errors_type")
                try:
                    tf.getmember("beatlink-party/release/ACHIEVEMENTS.json")
                except KeyError as exc:
                    raise RuntimeError("beatlink_tar_missing_release_achievements") from exc
            manifest["games"]["beatlink-party"] = {
                **(bl_meta or {}),
                "guest_package": "beatlink-party.tar.gz",
                "package_sha256": pkg_sha,
                "install_path": "/root/owner-games/beatlink-party",
                "node_binary_sha256": _sha256_file(node_dir / "node"),
                "pnpm_hoisted_packages": hoist_n,
                "tar_verified": True,
                "release_achievements": True,
                "required_service_topology": [
                    "node /root/owner-games/beatlink-party/server (Express+Socket.IO :3001)",
                    "STATIC_ASSET_SERVER for web dist (labeled, not proof alone)",
                    "Chromium Wayland client",
                ],
            }
    else:
        manifest["ok"] = False
        manifest["games"]["beatlink-party"] = {
            "ok": False,
            "error": "beatlink_bundle_incomplete",
            "web": (bl_web / "index.html").is_file(),
            "server": (bl_server / "dist" / "index.js").is_file(),
            "node": bool(node_bin),
        }

    # Diagnostic-only observer (reads native localStorage; never writes fake saves).
    observer = staging / "lab_observe_only.py"
    observer.write_text(
        '''#!/usr/bin/env python3
"""LAB_DIAGNOSTIC_ONLY / NOT_PRODUCT_RUNTIME_EVIDENCE

Static asset server for owner web packages + observe-only POST sink.
Never invents game saves. Rejects any payload that looks like a probe autosave
unless it is explicitly labeled LAB_DIAGNOSTIC_ONLY observation of native keys.
"""
from __future__ import annotations
import json, time
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path("/root/owner-games")
STATE = Path("/var/lib/gunnchos/games")
STATE.mkdir(parents=True, exist_ok=True)
PORT = 18765

class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)
    def log_message(self, *args):
        return
    def translate_path(self, path):
        from urllib.parse import unquote, urlparse
        p = unquote(urlparse(path).path)
        rel = p.lstrip("/")
        # Beat Link BrowserRouter SPA fallback so /host runs owner HostPage → storeHostToken.
        if rel == "sw.js":
            cand = ROOT / "beatlink-party" / "sw.js"
            if cand.is_file():
                return str(cand)
        if rel.split("/")[0] in ("host", "join", "play", "audience"):
            idx = ROOT / "beatlink-party" / "index.html"
            if idx.is_file():
                return str(idx)
        # Game-prefixed paths.
        for prefix, folder in (("earth-species/", "earth-species"), ("beatlink-party/", "beatlink-party")):
            if rel.startswith(prefix):
                return str(ROOT / folder / rel[len(prefix):])
        # Vite absolute /assets /data /icons from pages under /<game>/index.html
        if rel.startswith(("assets/", "data/", "icons/", "manifest")):
            for folder in ("earth-species", "beatlink-party"):
                cand = ROOT / folder / rel
                if cand.is_file() or cand.is_dir():
                    return str(cand)
        return super().translate_path(path)
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()
    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()
    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            # sendBeacon / chunked may omit Content-Length; drain a bounded body.
            self.connection.settimeout(0.2)
            chunks = []
            try:
                while True:
                    chunk = self.rfile.read(4096)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    if sum(len(c) for c in chunks) > 1_000_000:
                        break
            except Exception:
                pass
            body = b"".join(chunks)
        else:
            body = self.rfile.read(length)
        parts = [p for p in self.path.strip("/").split("/") if p]
        game = parts[-1] if parts else "unknown"
        out = STATE / game
        out.mkdir(parents=True, exist_ok=True)
        try:
            data = json.loads(body.decode("utf-8"))
        except Exception:
            data = {"raw": body.decode("utf-8", "replace")}
        data["received_at"] = time.time()
        # Hard reject fake save bridges / probe autosaves as product evidence.
        if data.get("save") and not data.get("LAB_DIAGNOSTIC_ONLY"):
            data["REJECTED"] = "probe_or_fake_save_bridge_forbidden"
            (out / "rejected_probe.json").write_text(json.dumps(data, indent=2) + "\\n")
            self.send_response(403)
            self.end_headers()
            return
        data["LAB_DIAGNOSTIC_ONLY"] = True
        data["NOT_PRODUCT_RUNTIME_EVIDENCE"] = True
        (out / "observe.json").write_text(json.dumps(data, indent=2) + "\\n")
        # Persist native localStorage snapshots when present (observation only).
        native = data.get("native_localStorage") or {}
        if isinstance(native, dict) and native:
            (out / "native_localStorage.json").write_text(json.dumps(native, indent=2) + "\\n")
        self.send_response(204)
        self.end_headers()

def main():
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), H)
    (STATE / "bridge_ready.json").write_text(
        json.dumps({
            "ok": True,
            "port": PORT,
            "label": "STATIC_ASSET_SERVER_FOR_BROWSER_RUNTIME",
            "LAB_DIAGNOSTIC_ONLY_observe": True,
            "NOT_PRODUCT_RUNTIME_EVIDENCE": True,
        }) + "\\n"
    )
    httpd.serve_forever()

if __name__ == "__main__":
    main()
''',
        encoding="utf-8",
    )
    # Observe-only page helper (injected only for web titles; labeled).
    (staging / "lab_observe_only.js").write_text(
        r'''
/* LAB_DIAGNOSTIC_ONLY / NOT_PRODUCT_RUNTIME_EVIDENCE
 * Observes native localStorage keys + input counts. Does not write game saves.
 * For Archive: may click the real #btn-new-game once so owner startGame()/saveGame() run.
 */
(function(){
  const GAME_ID = document.documentElement.getAttribute('data-gunnchos-game') || 'unknown';
  const ENDPOINT = 'http://127.0.0.1:18765/observe/' + GAME_ID;
  const NATIVE_KEYS = (document.documentElement.getAttribute('data-native-save-keys') || '').split(',').filter(Boolean);
  let input = 0;
  let started = false;
  function report(extra){
    const native = {};
    NATIVE_KEYS.forEach(function(k){
      try { native[k] = localStorage.getItem(k); } catch (e) { native[k] = null; }
    });
    const payload = Object.assign({
      LAB_DIAGNOSTIC_ONLY: true,
      NOT_PRODUCT_RUNTIME_EVIDENCE: true,
      game_id: GAME_ID,
      input: input,
      ts: Date.now(),
      native_localStorage: native,
      has_owner_hook: typeof window.__aolStartExpedition === 'function'
    }, extra||{});
    try {
      fetch(ENDPOINT, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload), keepalive:true}).catch(function(){});
    } catch (e) {}
  }
  function tryStartArchive(){
    if (GAME_ID !== 'earth-species') return;
    try {
      if (localStorage.getItem('archive_of_life_save')) {
        started = true;
        return;
      }
      // Wait for owner module init() to install the real start hook.
      if (typeof window.__aolStartExpedition === 'function') {
        if (started) return;
        started = true;
        input += 1;
        window.__aolStartExpedition(false);
        report({event:'owner_accept_start'});
        return;
      }
    } catch (e) {
      report({event:'start_error', error: String(e)});
    }
  }
  window.addEventListener('keydown', function(){ input += 1; report({event:'keydown'}); }, true);
  window.addEventListener('pointerdown', function(){ input += 1; report({event:'pointerdown'}); }, true);
  function onReady(){ report({event:'load'}); tryStartArchive(); }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', onReady);
  } else {
    onReady();
  }
  setInterval(function(){ tryStartArchive(); report({event:'observe'}); }, 1500);
})();
''',
        encoding="utf-8",
    )

    (staging / "OWNER_BUNDLE_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    # Godot 4.5 binary for guest (Anime features=4.5); optional if absent.
    godot45 = repo_root / "artifacts" / "wp011r" / "cache" / "Godot_v4.5-stable_linux.arm64"
    if godot45.is_file():
        shutil.copy2(godot45, staging / "Godot_v4.5-stable_linux.arm64")
        manifest["godot45"] = {
            "path": "Godot_v4.5-stable_linux.arm64",
            "sha256": _sha256_file(staging / "Godot_v4.5-stable_linux.arm64"),
        }
        (staging / "OWNER_BUNDLE_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )
    return manifest


def start_host_artifact_httpd(
    staging: Path, *, port: int = 8766, log_path: Path | None = None
) -> subprocess.Popen[str]:
    """Serve owner packages to guest via 10.0.2.2 (QEMU usernet).

    Port 8766 avoids colliding with the Godot binary cache server on :8765.
    """
    logf = None
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logf = open(log_path, "w", encoding="utf-8")
    return subprocess.Popen(
        [
            sys.executable,
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(staging),
        ],
        stdout=logf or subprocess.DEVNULL,
        stderr=logf or subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )


def wait_host_artifact_httpd(
    port: int, *, proc: subprocess.Popen[str], attempts: int = 20, delay_s: float = 0.25
) -> tuple[bool, str | None]:
    """Poll until http.server accepts on 127.0.0.1:port (or process exits)."""
    import socket as _sock

    last_err: str | None = None
    for _ in range(max(1, attempts)):
        if proc.poll() is not None:
            return False, f"httpd_exited_rc_{proc.returncode}"
        try:
            with _sock.create_connection(("127.0.0.1", port), timeout=1.0):
                return True, None
        except OSError as exc:
            last_err = str(exc)
        time.sleep(delay_s)
    return False, last_err or "listen_timeout"
