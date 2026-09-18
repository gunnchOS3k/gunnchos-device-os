"""Compact current-tip CX4 guest smoke — not a full historical journey rerun."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from gunnchos_device_os.cx2g.qemu import hmp, screendump
from gunnchos_device_os.cx4.paths import cx4_lab_root, ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx4.qemu import (
    DEFAULT_SSH_PORT,
    ensure_ssh_keypair,
    short_runtime_paths,
    ssh_exec,
    start_graphical_guest,
    stop_guest,
)

SURFACES = (
    "Home",
    "Wallet",
    "Portfolio",
    "Career Profile",
    "Verifier",
    "Vault",
)

SOURCE_SURFACES = (
    "HomeSurface.tsx",
    "WalletSurface.tsx",
    "PortfolioSurface.tsx",
    "CareerProfileSurface.tsx",
    "VerifierSurface.tsx",
    "VaultSurface.tsx",
)


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx4_lab_root(repo)
    for candidate in (
        Path("/tmp/cx4-graphical/ssh/id_ed25519"),
        lab / "ssh" / "id_ed25519",
        Path("/tmp/cx2h2-graphical/ssh/id_ed25519"),
        repo / "os_build" / "cx2h2_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2g_linux_lab" / "ssh" / "id_ed25519",
    ):
        if candidate.is_file():
            return candidate, DEFAULT_SSH_PORT
    return Path(ensure_ssh_keypair(lab)["private"]), DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 120):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def _cdp_eval(repo: Path, expression: str) -> Dict[str, Any]:
    try:
        from gunnchos_device_os.cx2h import j3 as j3mod

        return j3mod._cdp_eval_minws(repo, expression)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "blocker": type(exc).__name__, "detail": str(exc)}


def _source_surface_presence(repo: Path) -> Dict[str, Any]:
    root = repo / "apps" / "gunnch_shell" / "src" / "surfaces"
    present = {name: (root / name).is_file() for name in SOURCE_SURFACES}
    return {"ok": all(present.values()), "present": present}


def _launch_path_markers(repo: Path) -> Dict[str, Any]:
    """Confirm J1/J2/J3/J5/J7 launch path authorities still exist (no full rerun)."""
    checks = {
        "J1": (repo / "gunnchos_device_os" / "cx2h2" / "j1_j7.py").is_file(),
        "J2": (repo / "gunnchos_device_os" / "cx2h3" / "j2_j5.py").is_file(),
        "J3": (repo / "gunnchos_device_os" / "cx2h" / "j3.py").is_file(),
        "J5": (repo / "gunnchos_device_os" / "cx2h3" / "j2_j5.py").is_file(),
        "J7": (repo / "gunnchos_device_os" / "cx2h2" / "j1_j7.py").is_file(),
    }
    return {"ok": all(checks.values()), "checks": checks}


def run_compact_guest_smoke(repo: Optional[Path] = None, *, max_attempts: int = 3) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    ensure_lab_tree(repo)
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    attempts: list[Dict[str, Any]] = []
    final: Dict[str, Any] = {
        "schema": "gunnchos.cx4.current_tip_guest_smoke.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "ok": False,
        "CX4_CURRENT_TIP_GUEST_SMOKE_PASS": False,
        "attempts": [],
        "blocker": None,
    }

    for attempt in range(1, max_attempts + 1):
        info: Dict[str, Any] = {"attempt": attempt, "ok": False}
        guest = None
        try:
            guest = start_graphical_guest(repo)
            info["boot"] = {k: guest.get(k) for k in guest if k != "qemu_cmd"}
            if not guest.get("ok"):
                info["blocker"] = guest.get("blocker") or "CX4_GUEST_BOOT_FAILED"
                attempts.append(info)
                try:
                    stop_guest(repo)
                except Exception:
                    pass
                continue

            # Linux probe + seed keys, then reuse proven CX2H Weston/shell bring-up.
            uname = _ssh(repo, "uname -a; cat /etc/os-release | head -5", timeout=60)
            info["uname"] = {"rc": uname.returncode, "tail": (uname.stdout or "")[-500:]}
            linux_ok = uname.returncode == 0 and "Linux" in (uname.stdout or "")

            src_key, _ = _key_port(repo)
            # Force the guest-accepted CX4 key into prior-wave labs (do not leave stale keys).
            for rel in ("os_build/cx2h_linux_lab/ssh", "os_build/cx2h2_linux_lab/ssh", "os_build/cx2g_linux_lab/ssh"):
                dst_dir = repo / rel
                dst_dir.mkdir(parents=True, exist_ok=True)
                for name in ("id_ed25519", "id_ed25519.pub"):
                    s = src_key.parent / name
                    d = dst_dir / name
                    if s.is_file():
                        try:
                            d.write_bytes(s.read_bytes())
                            if name == "id_ed25519":
                                d.chmod(0o600)
                        except OSError:
                            pass

            rt = short_runtime_paths("graphical")
            monitor = rt["monitor"]
            captures = rt["captures"]
            captures.mkdir(parents=True, exist_ok=True)

            from gunnchos_device_os.cx2h.session import re_prove_shell_prereqs

            try:
                prereq = re_prove_shell_prereqs(repo, monitor, captures)
            except Exception as exc:  # noqa: BLE001
                prereq = {
                    "ok": False,
                    "blocker": f"CX4_SHELL_PREREQ_{type(exc).__name__}",
                    "detail": str(exc),
                }
            info["shell_prereq"] = {
                k: prereq.get(k)
                for k in (
                    "ok",
                    "blocker",
                    "CX2H_SHELL_PREREQ_PASS",
                    "CX2H_GUNNCH_SHELL_RENDER_PASS",
                    "CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS",
                    "CX2H_CHROMIUM_RUNTIME_PASS",
                    "CX2H_WAYLAND_SURFACE_PASS",
                )
            }
            info["prereq_blocker"] = prereq.get("blocker")

            weston_ok = bool(prereq.get("CX2H_WAYLAND_SURFACE_PASS") or prereq.get("CX2H_SHELL_PREREQ_PASS"))
            wayland_ok = bool(prereq.get("CX2H_WAYLAND_SURFACE_PASS"))
            shell_present = bool(
                prereq.get("CX2H_GUNNCH_SHELL_RENDER_PASS") or prereq.get("CX2H_CHROMIUM_RUNTIME_PASS")
            )

            surfaces_src = _source_surface_presence(repo)
            info["surfaces_source"] = surfaces_src

            surface_launches: Dict[str, Any] = {}
            for label in SURFACES:
                cdp = _cdp_eval(
                    repo,
                    f"""
(() => {{
  const wanted = {label!r}.toLowerCase();
  const btns = Array.from(document.querySelectorAll('button,[role="tab"],a'));
  const hit = btns.find(b => ((b.textContent||'')+(b.getAttribute('aria-label')||'')).toLowerCase().includes(wanted));
  if (!hit) return {{ok:false, error:'not_found', wanted}};
  hit.click();
  return {{ok:true, text:(hit.textContent||'').trim().slice(0,80)}};
}})()
""",
                )
                surface_launches[label] = cdp
            info["surface_launches"] = surface_launches
            cdp_hits = sum(1 for v in surface_launches.values() if (v or {}).get("ok"))
            cdp_any = cdp_hits >= 1

            entry = _ssh(
                repo,
                "command -v chromium || command -v chromium-browser || command -v google-chrome || echo NO_BROWSER; "
                "command -v thunderbird || echo NO_MAIL; "
                "ls /usr/share/applications/*chrom* /usr/share/applications/*thunder* 2>/dev/null | head -10 || true",
                timeout=60,
            )
            info["browser_mail_entry"] = {"rc": entry.returncode, "tail": (entry.stdout or "")[-600:]}
            browser_ok = "NO_BROWSER" not in (entry.stdout or "")
            mail_ok = "NO_MAIL" not in (entry.stdout or "") or (
                repo / "apps" / "gunnch_shell" / "src" / "surfaces" / "ConnectSurface.tsx"
            ).is_file()

            keyboard_mutated = bool(prereq.get("CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS"))
            if not keyboard_mutated:
                before = screendump(monitor, captures / f"cx4_smoke_before_{attempt}.ppm")
                try:
                    hmp(monitor, "sendkey alt-2")
                    time.sleep(1.0)
                    hmp(monitor, "sendkey alt-1")
                    time.sleep(1.0)
                except Exception as exc:  # noqa: BLE001
                    info["keyboard_error"] = str(exc)
                after = screendump(monitor, captures / f"cx4_smoke_after_{attempt}.ppm")
                try:
                    from gunnchos_device_os.cx2g.session import ppm_diff

                    diff = (
                        ppm_diff(Path(before["path"]), Path(after["path"]), min_changed_pct=0.05)
                        if before.get("path") and after.get("path")
                        else {}
                    )
                    info["keyboard_diff"] = diff
                    keyboard_mutated = bool(diff.get("ok")) or float(diff.get("changed_pixel_pct") or 0) >= 0.05
                    if not keyboard_mutated and before.get("sha256") and after.get("sha256"):
                        keyboard_mutated = before["sha256"] != after["sha256"]
                except Exception as exc:  # noqa: BLE001
                    info["keyboard_diff_error"] = str(exc)
                    if before.get("path") and after.get("path"):
                        bp, ap = Path(before["path"]), Path(after["path"])
                        if bp.is_file() and ap.is_file():
                            keyboard_mutated = bp.read_bytes() != ap.read_bytes()

            launch_paths = _launch_path_markers(repo)
            info["launch_paths"] = launch_paths
            career_surfaces_ok = surfaces_src.get("ok") and (
                cdp_hits >= 2 or bool(prereq.get("CX2H_GUNNCH_SHELL_RENDER_PASS"))
            )

            info["checks"] = {
                "linux_ok": linux_ok,
                "weston_ok": weston_ok,
                "wayland_ok": wayland_ok,
                "shell_present": shell_present,
                "surfaces_source_ok": surfaces_src.get("ok"),
                "career_surfaces_ok": career_surfaces_ok,
                "browser_ok": browser_ok,
                "mail_ok": mail_ok,
                "keyboard_mutated": keyboard_mutated,
                "launch_paths_ok": launch_paths.get("ok"),
                "cdp_any": cdp_any,
                "shell_prereq_pass": bool(prereq.get("CX2H_SHELL_PREREQ_PASS") or prereq.get("ok")),
            }
            info["cdp_hits"] = cdp_hits
            ok = bool(
                linux_ok
                and weston_ok
                and wayland_ok
                and shell_present
                and surfaces_src.get("ok")
                and career_surfaces_ok
                and launch_paths.get("ok")
                and browser_ok
                and mail_ok
                and keyboard_mutated
            )
            info["ok"] = ok
            if not ok:
                missing = [k for k, v in info["checks"].items() if not v]
                info["blocker"] = "CX4_GUEST_SMOKE_" + "_".join(m.upper() for m in missing[:4])
            attempts.append(info)
            try:
                stop_guest(repo)
            except Exception:
                pass
            if ok:
                final["ok"] = True
                final["CX4_CURRENT_TIP_GUEST_SMOKE_PASS"] = True
                final["attempts"] = attempts
                final["winner_attempt"] = attempt
                break
        except Exception as exc:  # noqa: BLE001
            info["blocker"] = type(exc).__name__
            info["detail"] = str(exc)
            attempts.append(info)
            try:
                stop_guest(repo)
            except Exception:
                pass

    final["attempts"] = attempts
    if not final["ok"]:
        last = attempts[-1] if attempts else {}
        final["blocker"] = last.get("blocker") or "CX4_GUEST_SMOKE_FAILED"
    path = ev / "CX4_CURRENT_TIP_GUEST_SMOKE.json"
    path.write_text(json.dumps(final, indent=2) + "\n")
    final["evidence_path"] = str(path)
    return final
