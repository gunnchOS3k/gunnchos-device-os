"""WP-011R production game runtime proofs.

http.server process proof is PROCESS_PROOF_ONLY and must not set
FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.ecosystem.games import FOUR_GAMES, discover_sibling_roots

CLAIM = (
    "Production runtime proof requires build/discover artifact, intended runtime "
    "(not http.server alone), process, viewport frame, input→state change, save, stop. "
    "SILICON_EXACT_EMULATION=false."
)


def _chromium_bin() -> str | None:
    for name in ("chromium", "chromium-browser", "google-chrome", "chrome"):
        p = shutil.which(name)
        if p:
            return p
    # macOS common path
    mac = Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")
    if mac.exists():
        return str(mac)
    return None


def _godot_bin() -> str | None:
    for name in ("godot", "Godot"):
        p = shutil.which(name)
        if p:
            return p
    return None


def prove_game_production_runtime(
    game_id: str,
    *,
    repo_root: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Attempt production runtime proof for one game. Honest PARTIAL/FAIL if host lacks runtime."""
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = FOUR_GAMES.get(game_id)
    if not meta:
        return {"game_id": game_id, "ok": False, "reason": "unknown_game"}

    siblings = discover_sibling_roots(repo_root)
    sibling = siblings.get(str(meta.get("sibling_repo") or ""))
    web_rel = meta["web_path"]
    web = repo_root / web_rel
    if sibling and (sibling / "index.html").exists():
        web = sibling
    elif not web.exists():
        # try in-tree games package
        alt = repo_root / "gunnchos_device_os" / "device_lab" / web_rel
        if alt.exists():
            web = alt

    result: dict[str, Any] = {
        "game_id": game_id,
        "claim": CLAIM,
        "http_server_alone_accepted": False,
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        "runtime_class": None,
        "ok": False,
        "artifact_root": str(web) if web.exists() else None,
    }

    if not web.exists():
        result["reason"] = "artifact_missing"
        (out_dir / f"{game_id}_result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    # Prefer Godot for foot-racing when available
    if game_id == "foot-racing":
        godot = _godot_bin()
        project = None
        if sibling:
            candidate = sibling / str(meta.get("godot_project_rel") or "project.godot")
            if candidate.exists():
                project = candidate
        if godot and project:
            log = out_dir / f"{game_id}_godot.log"
            proc = subprocess.Popen(
                [godot, "--path", str(project.parent), "--headless", "--quit-after", "3"],
                stdout=log.open("w"),
                stderr=subprocess.STDOUT,
                text=True,
            )
            proc.wait(timeout=60)
            result.update(
                {
                    "runtime_class": "GODOT_HEADLESS",
                    "ok": proc.returncode == 0,
                    "process_proof": True,
                    "note": "Godot headless quit-after probe; extend for frame/input when display available",
                }
            )
            (out_dir / f"{game_id}_result.json").write_text(json.dumps(result, indent=2) + "\n")
            return result

    chrome = _chromium_bin()
    if not chrome:
        result.update(
            {
                "runtime_class": "UNAVAILABLE",
                "reason": "no_chromium_or_godot",
                "depth": "PROCESS_PROOF_ONLY_HTTP_SERVER_REJECTED",
            }
        )
        (out_dir / f"{game_id}_result.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    # Serve via temporary http.server ONLY as transport; proof requires Chromium load + DOM marker.
    srv = subprocess.Popen(
        ["python3", "-m", "http.server", "0", "--bind", "127.0.0.1", "--directory", str(web)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(0.4)
    # Discover port via lsof-like fallback: use fixed probe by connecting — parse ss
    port = None
    try:
        import socket

        # http.server with port 0 — read from /proc not portable; restart with fixed port
        srv.terminate()
        srv.wait(timeout=5)
    except Exception:
        pass

    port = 8765 + (abs(hash(game_id)) % 100)
    srv = subprocess.Popen(
        [
            "python3",
            "-m",
            "http.server",
            str(port),
            "--bind",
            "127.0.0.1",
            "--directory",
            str(web),
        ],
        stdout=(out_dir / f"{game_id}_http.log").open("w"),
        stderr=subprocess.STDOUT,
        text=True,
    )
    time.sleep(0.5)
    url = f"http://127.0.0.1:{port}/"
    shot = out_dir / f"{game_id}_viewport.png"
    # Headless Chromium screenshot = real runtime viewport (not generated fake image).
    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--window-size=1280,720",
        f"--screenshot={shot}",
        url,
    ]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        alive = srv.poll() is None
        has_frame = shot.exists() and shot.stat().st_size > 1000
        # Input/state: inject via Chromium dump-dom marker if index has body
        state_ok = has_frame
        result.update(
            {
                "runtime_class": "CHROMIUM_HEADLESS_VIEWPORT",
                "ok": bool(cp.returncode == 0 and has_frame and alive),
                "process_proof": True,
                "viewport_frame": str(shot) if has_frame else None,
                "input_state_change": False,
                "save_state": False,
                "note": (
                    "Chromium viewport earned; input/save/suspend still required for full PASS token"
                ),
                "transport_http_server": True,
                "http_server_alone_accepted": False,
            }
        )
    except Exception as exc:
        result.update({"ok": False, "reason": f"chromium_failed:{exc}"})
    finally:
        srv.terminate()
        try:
            srv.wait(timeout=5)
        except Exception:
            srv.kill()

    (out_dir / f"{game_id}_result.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def prove_all_four(*, repo_root: Path, out_dir: Path) -> dict[str, Any]:
    results = {
        gid: prove_game_production_runtime(gid, repo_root=repo_root, out_dir=out_dir)
        for gid in FOUR_GAMES
    }
    all_ok = all(bool(r.get("ok")) for r in results.values())
    # Full token still requires input/state/save — never auto-true here
    aggregate = {
        "schema": "gunnchos.wp011r.four_game_production_runtime.v1",
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        "all_viewports_ok": all_ok,
        "games": results,
        "claim": CLAIM,
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "four_games_aggregate.json").write_text(json.dumps(aggregate, indent=2) + "\n")
    return aggregate
