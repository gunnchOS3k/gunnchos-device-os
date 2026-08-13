"""Honest FOUR_GAME earn criteria (WP-011R.2).

Independent verify rejected tautological earners, Godot `<defunct>` counted
alive, headless `--quit-after` / ProductionGateHarness as sole mutation proof,
Beat Link room-API-as-save, and SHA pin-lie (`observed_sha` = drifted sibling
while `ok=true` via owner_artifact_pin).

These helpers are pure: unit-tested, no guest I/O. Guest runners must AND
them — never OR-pass the suite.
"""
from __future__ import annotations

import json
import re
from typing import Any

BEATLINK_NATIVE_KEYS = ("beatlink_host", "beatlink_player", "beatlink_audience")
ARCHIVE_DEFAULT_SPAWN = {"x": 400, "y": 300, "currentRegion": "museum"}


def pid_stat_is_alive_non_zombie(stat: str | None, args: str = "") -> bool:
    """STAT starting with Z or argv containing <defunct> is a zombie — FAIL."""
    if not stat:
        return False
    s = str(stat).strip()
    if not s:
        return False
    if s[0].upper() == "Z":
        return False
    if "<defunct>" in (args or "").lower():
        return False
    return True


def parse_ps_pid_stat_args(stdout: str) -> list[dict[str, Any]]:
    """Parse `ps -eo pid,stat,args` (or `ps -o pid=,stat=,args=`). Skip header."""
    rows: list[dict[str, Any]] = []
    for line in (stdout or "").splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 2:
            continue
        if not parts[0].isdigit():
            continue
        pid = int(parts[0])
        stat = parts[1]
        args = parts[2] if len(parts) > 2 else ""
        alive = pid_stat_is_alive_non_zombie(stat, args)
        rows.append(
            {
                "pid": pid,
                "stat": stat,
                "args": args,
                "zombie": not alive,
                "alive_non_zombie": alive,
            }
        )
    return rows


def launched_pid_alive_non_zombie(pid: Any, rows: list[dict[str, Any]]) -> bool:
    try:
        want = int(pid)
    except (TypeError, ValueError):
        return False
    for row in rows:
        if row["pid"] == want:
            return bool(row["alive_non_zombie"])
    return False


def substring_alive_godot_forbidden(ps_args_only: str) -> bool:
    """True when the old tautology would PASS (`'godot' in stdout`) on zombies."""
    text = (ps_args_only or "").lower()
    return "godot" in text


def pedestrian_cfg_mutated(before: str, after: str) -> dict[str, Any]:
    """Seeded pp_progression.cfg must change. Presence of defaults is not mutation."""
    b = (before or "").strip()
    a = (after or "").strip()
    defaultish = bool(
        a
        and "xp=0" in a
        and "tutorial_completed=false" in a
        and "first_run_complete=false" in a
        and b != a
        and "save_version=1" not in b
    )
    changed = bool(b and a and a != b)
    out = {
        "changed": changed,
        "first_run_create_only": bool(a and not b),
        "default_unmutated_presence": bool(a and not changed),
        "headless_default_rejected": defaultish and not changed,
        "ok": changed and not (not b),
    }
    # Migration v1→v2 of a pre-seeded file while GUI is alive is owner persist.
    if changed and "save_version=1" in b and "save_version=2" in a:
        out["ok"] = True
        out["via"] = "seeded_v1_to_v2"
    elif changed:
        out["ok"] = True
        out["via"] = "seeded_bytes_changed"
    else:
        out["ok"] = False
        out["via"] = None
    return out


def anime_default_career_save(save: str) -> bool:
    """Default GameState._persist_save() profile is not input-driven mutation."""
    s = (save or "").replace(" ", "")
    return bool(
        s
        and "save_version=2" in s
        and "wins=0" in s
        and "losses=0" in s
        and "matches=0" in s
    )


def anime_cfg_mutated(before: str, after: str) -> dict[str, Any]:
    """Seeded aa_first_run.cfg must change (skip or complete). Harness-only create is FAIL."""
    b = (before or "").strip()
    a = (after or "").strip()
    changed = bool(b and a and a != b)
    skipped = bool(re.search(r"skipped\s*=\s*true", a, re.I))
    completed = bool(re.search(r"completed\s*=\s*true", a, re.I))
    seed_false = "completed=false" in b.replace(" ", "") or "completed = false" in b
    out = {
        "changed": changed,
        "skipped": skipped,
        "completed": completed,
        "first_run_create_only": bool(a and not b),
        "ok": bool(changed and (skipped or completed or seed_false)),
        "via": None,
    }
    if out["ok"]:
        out["via"] = "seeded_first_run_changed"
    return out


def _parse_archive_save(raw: Any) -> dict[str, Any] | None:
    if raw is None:
        return None
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return obj if isinstance(obj, dict) else None
    return None


def archive_save_mutated_from_default(raw: Any) -> dict[str, Any]:
    """Default museum spawn (x=400,y=300,region=museum) is start, not post-start mutation."""
    obj = _parse_archive_save(raw)
    if not obj:
        return {"ok": False, "present": False, "default_spawn": False, "via": None}
    player = obj.get("player") if isinstance(obj.get("player"), dict) else {}
    x = player.get("x")
    y = player.get("y")
    region = player.get("currentRegion")
    visited = player.get("visitedRegions") or []
    default = (
        x == ARCHIVE_DEFAULT_SPAWN["x"]
        and y == ARCHIVE_DEFAULT_SPAWN["y"]
        and region == ARCHIVE_DEFAULT_SPAWN["currentRegion"]
        and list(visited) == ["museum"]
    )
    pos_moved = (x != ARCHIVE_DEFAULT_SPAWN["x"]) or (y != ARCHIVE_DEFAULT_SPAWN["y"])
    region_changed = region not in (None, ARCHIVE_DEFAULT_SPAWN["currentRegion"])
    visited_grew = isinstance(visited, list) and len(visited) > 1
    ok = bool(obj) and (pos_moved or region_changed or visited_grew) and not default
    return {
        "ok": ok,
        "present": True,
        "default_spawn": default,
        "x": x,
        "y": y,
        "currentRegion": region,
        "visited_n": len(visited) if isinstance(visited, list) else 0,
        "via": "post_start_position_or_region" if ok else None,
    }


def beatlink_native_keys_present(native: dict[str, Any] | None, scrape: str = "") -> dict[str, Any]:
    """Room API create is NOT save. Require owner beatlink_* localStorage keys."""
    native = native or {}
    found = []
    for key in BEATLINK_NATIVE_KEYS:
        val = native.get(key)
        if val not in (None, "", "null"):
            found.append(key)
        elif key in (scrape or ""):
            found.append(key)
    scrape_hit = any(k in (scrape or "") for k in BEATLINK_NATIVE_KEYS)
    ok = bool(found) or scrape_hit
    return {
        "ok": ok,
        "keys_found": found,
        "scrape_hit": scrape_hit,
        "room_api_not_accepted_as_save": True,
    }


def honest_sha_entry(
    *,
    accepted_main_sha: str,
    sibling_head: str | None,
    meta: dict[str, Any] | None,
    owner_repo: str,
    lab_id: str,
    sibling_path: str | None,
) -> dict[str, Any]:
    """Do not report drifted sibling HEAD as observed_sha while ok=true via pin."""
    packaged = (meta or {}).get("accepted_main_sha") if meta else None
    sibling_match = bool(
        sibling_head
        and (
            sibling_head == accepted_main_sha
            or sibling_head.startswith(accepted_main_sha[:12])
        )
    )
    pin_ok = bool(packaged == accepted_main_sha)
    if sibling_match:
        source = "sibling_checkout"
        observed = sibling_head
        ok = True
    elif pin_ok:
        source = "owner_artifact_pin"
        observed = accepted_main_sha
        ok = True
    else:
        source = None
        observed = sibling_head
        ok = False
    return {
        "owner_repo": owner_repo,
        "accepted_main_sha": accepted_main_sha,
        "sibling_path": sibling_path,
        "sibling_head": sibling_head,
        "observed_sha": observed,
        "ok": ok,
        "source": source,
        "lab_id": lab_id,
        "sibling_matches_accepted_main": sibling_match,
        "successor_draft_not_accepted_main": bool(sibling_head and not sibling_match),
        "pin_lie_forbidden": True,
        "note": (
            "Successor drafts are NOT accepted-main unless Edmund merged. "
            "owner_artifact_pin reports packaged accepted_main_sha, never drifted sibling HEAD."
        ),
    }


def five_gate_and(
    *,
    four: bool,
    live: bool,
    dsxl: bool,
    ring: bool,
    eco010: bool,
) -> bool:
    return bool(four and live and dsxl and ring and eco010)


def master_complete_forbidden(
    *,
    silicon_exact: bool = False,
    shipping_image: bool = False,
    interactive_guest: bool = True,
) -> bool:
    """COMPLETE stays false on interactive guest / silicon-inexact / non-shipping."""
    if not silicon_exact or not shipping_image or interactive_guest:
        return False
    return False  # this packet never earns COMPLETE
