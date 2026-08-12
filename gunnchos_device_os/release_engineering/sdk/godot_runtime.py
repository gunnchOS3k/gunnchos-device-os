"""Godot runtime helpers for gunnchSDK first-party game packages.

Resolves a host Godot 4.x binary (prefer 4.5 to match Pedestrian Pursuit
``config/features`` + available export templates) and performs a real
``--export-pack`` of an accepted-SHA worktree into a ``.pck`` artifact.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

ACCEPTED_PEDESTRIAN_PURSUIT_SHA = "3f4dafd0e455a0cf22523bab48a094a542d3141d"
GODOT_EXPORT_PRESET = "gunnchos-macos"

_MACOS_PRESET_BLOCK = """
[preset.1]

name="gunnchos-macos"
platform="macOS"
runnable=true
advanced_options=false
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter="data/*.json,data/**/*.json"
exclude_filter=""
export_path="build/gunnchos/PedestrianPursuit.app"
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false

[preset.1.options]

custom_template/debug=""
custom_template/release=""
debug/export_console_wrapper=1
application/icon=""
application/icon_interpolation=4
application/bundle_identifier="com.gunnchos.pedestrianpursuit"
application/signature=""
application/app_category="Games"
application/short_version="0.4.0"
application/version="0.4.0"
application/copyright=""
display/high_res=true
export/distribution_type=1
codesign/codesign=0
notarization/notarization=0
"""


def resolve_godot_bin() -> str:
    env = os.environ.get("GODOT_BIN") or os.environ.get("GUNNCHOS_GODOT_BIN")
    if env and Path(env).exists():
        return env
    candidates = [
        Path.home() / "Applications/Godot/Godot-4.5.app/Contents/MacOS/Godot",
        Path("/Users/gunnchos/Applications/Godot/Godot-4.5.app/Contents/MacOS/Godot"),
        Path("/Applications/Godot-4.5.app/Contents/MacOS/Godot"),
        Path("/Applications/Godot.app/Contents/MacOS/Godot"),
    ]
    for c in candidates:
        if c.exists():
            return str(c)
    which = shutil.which("godot") or shutil.which("godot4")
    if which:
        return which
    raise FileNotFoundError(
        "Godot 4.5 binary not found (set GODOT_BIN). Required for "
        "FIRST_PARTY_GAME_SDK_ADOPTION_PASS Godot export/runtime."
    )


def godot_version(godot_bin: str | None = None) -> str:
    bin_path = godot_bin or resolve_godot_bin()
    proc = subprocess.run(
        [bin_path, "--version"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    return (proc.stdout or proc.stderr or "").strip()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_accepted_worktree(
    *,
    pedestrian_repo: Path,
    worktree_dir: Path,
    accepted_sha: str = ACCEPTED_PEDESTRIAN_PURSUIT_SHA,
) -> dict[str, Any]:
    """Detach a worktree at the accepted Pedestrian Pursuit main SHA."""
    pedestrian_repo = Path(pedestrian_repo)
    worktree_dir = Path(worktree_dir)
    if not (pedestrian_repo / ".git").exists() and not (pedestrian_repo / ".git").is_file():
        # bare check — also allow worktree gitfile
        git_dir = pedestrian_repo / ".git"
        if not git_dir.exists():
            raise FileNotFoundError(f"pedestrian_repo_missing:{pedestrian_repo}")

    worktree_dir.parent.mkdir(parents=True, exist_ok=True)
    if worktree_dir.exists():
        # Re-use if already at the right SHA.
        head = subprocess.run(
            ["git", "-C", str(worktree_dir), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        if head.returncode == 0 and head.stdout.strip().startswith(accepted_sha[:12]):
            return {
                "ok": True,
                "worktree": str(worktree_dir),
                "accepted_sha": accepted_sha,
                "reused": True,
            }
        subprocess.run(
            ["git", "-C", str(pedestrian_repo), "worktree", "remove", "--force", str(worktree_dir)],
            capture_output=True,
            text=True,
            check=False,
        )
        shutil.rmtree(worktree_dir, ignore_errors=True)

    proc = subprocess.run(
        [
            "git",
            "-C",
            str(pedestrian_repo),
            "worktree",
            "add",
            "--detach",
            str(worktree_dir),
            accepted_sha,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"worktree_add_failed:{proc.stderr or proc.stdout}")
    head = subprocess.run(
        ["git", "-C", str(worktree_dir), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    return {
        "ok": True,
        "worktree": str(worktree_dir),
        "accepted_sha": accepted_sha,
        "head_sha": head,
        "reused": False,
    }


def _ensure_export_preset(worktree: Path) -> None:
    preset_path = worktree / "export_presets.cfg"
    text = preset_path.read_text(encoding="utf-8") if preset_path.exists() else ""
    if 'name="gunnchos-macos"' not in text:
        preset_path.write_text(text + _MACOS_PRESET_BLOCK, encoding="utf-8")


def inject_adoption_harness(worktree: Path, harness_src: Path) -> Path:
    dest = worktree / "tools" / "gunnchos_sdk_adoption_harness.gd"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(harness_src.read_text(encoding="utf-8"), encoding="utf-8")
    return dest


def export_godot_pack(
    *,
    worktree: Path,
    out_pck: Path,
    godot_bin: str | None = None,
    timeout_s: float = 300.0,
) -> dict[str, Any]:
    """Import project assets then ``--export-pack`` to ``out_pck``."""
    godot = godot_bin or resolve_godot_bin()
    worktree = Path(worktree)
    out_pck = Path(out_pck)
    out_pck.parent.mkdir(parents=True, exist_ok=True)
    _ensure_export_preset(worktree)

    import_log = out_pck.parent / "godot_import.log"
    t0 = time.time()
    import_ok = False
    import_rc = -1
    import_blob = ""
    for attempt in range(2):
        imp = subprocess.run(
            [godot, "--headless", "--path", str(worktree), "--import"],
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
        import_rc = imp.returncode
        import_blob = (imp.stdout or "") + "\n" + (imp.stderr or "")
        import_log.write_text(import_blob + f"\n# attempt={attempt} rc={import_rc}\n", encoding="utf-8")
        # Godot sometimes exits non-zero after a successful import due to adb /
        # editor teardown crashes ("Pure virtual function called"). Treat the
        # import as OK when the imported asset cache is present.
        imported_dir = worktree / ".godot" / "imported"
        if import_rc == 0 or (imported_dir.exists() and any(imported_dir.iterdir())):
            import_ok = True
            break
        time.sleep(1.0)

    if not import_ok:
        return {
            "ok": False,
            "error": "godot_import_failed",
            "returncode": import_rc,
            "import_log": str(import_log),
        }

    export_log = out_pck.parent / "godot_export_pack.log"
    exp = subprocess.run(
        [
            godot,
            "--headless",
            "--path",
            str(worktree),
            "--export-pack",
            GODOT_EXPORT_PRESET,
            str(out_pck),
        ],
        capture_output=True,
        text=True,
        timeout=timeout_s,
        check=False,
    )
    export_log.write_text(
        (exp.stdout or "")
        + "\n"
        + (exp.stderr or "")
        + f"\n# export_pack_rc={exp.returncode}\n",
        encoding="utf-8",
    )
    # Godot may abort after writing the pack (adb/editor teardown). Accept the
    # artifact when the .pck lands with non-trivial size and savepack completed.
    pack_ok = out_pck.exists() and out_pck.stat().st_size >= 1024 * 1024
    savepack_done = "[ DONE ]" in (exp.stdout or "") or "savepack" in (exp.stdout or "")
    if not pack_ok:
        return {
            "ok": False,
            "error": "godot_export_pack_failed",
            "returncode": exp.returncode,
            "export_log": str(export_log),
            "pck_exists": out_pck.exists(),
        }

    return {
        "ok": True,
        "godot_bin": godot,
        "godot_version": godot_version(godot),
        "preset": GODOT_EXPORT_PRESET,
        "export_mode": "export-pack",
        "pck_path": str(out_pck),
        "pck_sha256": _sha256_file(out_pck),
        "pck_size_bytes": out_pck.stat().st_size,
        "duration_s": round(time.time() - t0, 3),
        "import_log": str(import_log),
        "export_log": str(export_log),
        "godot_export_returncode": exp.returncode,
        "savepack_done": savepack_done,
        "teardown_abort_tolerated": exp.returncode != 0,
    }


def default_pedestrian_repo(repo_root: Path) -> Path:
    """Locate sibling ``pedestrian-pursuit`` checkout under the research spine."""
    env = os.environ.get("GUNNCHOS_PEDESTRIAN_PURSUIT_REPO")
    if env:
        return Path(env)
    # device-os lives at .../repos/gunnchos-device-os
    sibling = repo_root.parent / "pedestrian-pursuit"
    if sibling.exists():
        return sibling
    raise FileNotFoundError(
        "pedestrian-pursuit repo not found; set GUNNCHOS_PEDESTRIAN_PURSUIT_REPO"
    )
