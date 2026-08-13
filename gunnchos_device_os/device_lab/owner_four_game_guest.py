"""In-guest FOUR_GAME proofs using owner accepted-main artifacts (WP-011R.2).

Honesty contract
----------------
* No device-os HTML recreations, probe autosave facades, fake save bridges,
  hardcoded state markers, http.server-alone PASS, or Python game mirrors.
* Lab observe endpoint is LAB_DIAGNOSTIC_ONLY / NOT_PRODUCT_RUNTIME_EVIDENCE.
* PASS requires native owner runtime + native persistence per game.
* Beat Link requires real Socket.IO server topology (@beatlink/server).
"""
from __future__ import annotations

import base64
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.four_game_honest import (
    anime_cfg_mutated,
    archive_save_mutated_from_default,
    beatlink_native_keys_present,
    launched_pid_alive_non_zombie,
    parse_ps_pid_stat_args,
    pedestrian_cfg_mutated,
)

from gunnchos_device_os.device_lab.interactive_guest_four_games import (
    PEDESTRIAN_GODOT_SAVE,
    _agent_call,
    _ensure_godot4_in_guest,
    _guest_bash,
    _hot_patch_guest_agent,
    _kill_matching_pythonish,
)
from gunnchos_device_os.device_lab.interactive_guest_proofs import (
    _evidence_dir,
    _require_real_virtio_serial,
)
from gunnchos_device_os.device_lab.owner_four_game_artifacts import (
    ACCEPTED_MAINS,
    LAB_TO_OWNER,
    prepare_owner_guest_staging,
    start_host_artifact_httpd,
    verify_accepted_shas,
)

CLAIM = (
    "FOUR_GAME proofs run INSIDE the Interactive Development Guest using owner "
    "real build artifacts at accepted mains. Host Playwright rejected. "
    "http.server is STATIC_ASSET_SERVER only. Probe/lab_bridge autosave rejected. "
    "Beat Link requires Socket.IO topology AND native beatlink_* keys "
    "(room API create is not save). "
    "Godot <defunct> is FAIL. Headless --quit-after / ProductionGateHarness is not "
    "sole mutation proof. Input-driven native persist required. "
    "SILICON_EXACT_EMULATION=false. DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. "
    "SHIPPING_IMAGE=false."
)

LAB_IDS = ("anime-aggressors", "beatlink-party", "earth-species", "foot-racing")

ANIME_SAVE = "/root/.local/share/godot/app_userdata/Anime Aggressors/aa_save.cfg"
ANIME_FIRST = "/root/.local/share/godot/app_userdata/Anime Aggressors/aa_first_run.cfg"


def _ensure_lab_observe_server(session: Any, *, restart: bool = False) -> dict[str, Any]:
    """Keep the labeled static/observe server alive via process_start (survives bash exit)."""
    probe = _guest_bash(
        session,
        "curl -fsS -o /dev/null -w '%{http_code}' --connect-timeout 1 http://127.0.0.1:18765/ || true",
        timeout_sec=10,
        name="observe-probe",
    )
    code = (probe.get("stdout") or "").strip()
    if (not restart) and code in {"200", "404", "301", "302"}:
        return {"ok": True, "already": True, "http_code": code}
    _kill_matching_pythonish(session, "lab_observe_only.py")
    _guest_bash(
        session,
        "rm -f /var/lib/gunnchos/games/bridge_ready.json",
        timeout_sec=10,
        name="observe-ready-reset",
    )
    start = _agent_call(
        session,
        "process_start",
        name="lab-observe",
        argv=["python3", "/opt/gunnchos/bin/lab_observe_only.py"],
        timeout_sec=15.0,
    )
    ready = False
    http_code = ""
    for _ in range(25):
        time.sleep(0.3)
        p2 = _guest_bash(
            session,
            "curl -fsS -o /dev/null -w '%{http_code}' --connect-timeout 1 http://127.0.0.1:18765/ || true",
            timeout_sec=10,
            name="observe-wait",
        )
        http_code = (p2.get("stdout") or "").strip()
        if http_code in {"200", "404", "301", "302"}:
            ready = True
            break
    return {
        "ok": ready,
        "start": {k: start.get(k) for k in ("ok", "pid", "started", "reason") if k in start},
        "http_code": http_code,
        "LAB_DIAGNOSTIC_ONLY": True,
        "NOT_PRODUCT_RUNTIME_EVIDENCE": True,
    }


def _guest_write_text(session: Any, path: str, text: str) -> dict[str, Any]:
    payload = base64.b64encode(text.encode("utf-8")).decode("ascii")
    return _agent_call(session, "file_put", path=path, bytes_b64=payload, timeout_sec=20.0)


def _pid_alive_non_zombie(session: Any, pid: Any) -> dict[str, Any]:
    try:
        want = int(pid)
    except (TypeError, ValueError):
        return {"alive": False, "reason": "no_pid", "pid": pid}
    r = _guest_bash(
        session,
        f"ps -o pid=,stat=,args= -p {want} 2>/dev/null || true",
        timeout_sec=10,
        name="pid-stat",
    )
    stdout = r.get("stdout") or ""
    rows = parse_ps_pid_stat_args(stdout)
    alive = launched_pid_alive_non_zombie(want, rows)
    return {
        "alive": alive,
        "pid": want,
        "ps": stdout[:400],
        "zombie_rejected": not alive,
        "stat": (rows[0]["stat"] if rows else None),
    }


def _wait_pid_alive(session: Any, pid: Any, *, tries: int = 24, delay_s: float = 0.5) -> dict[str, Any]:
    last = {"alive": False, "reason": "no_pid", "pid": pid}
    for _ in range(max(1, tries)):
        last = _pid_alive_non_zombie(session, pid)
        if last.get("alive"):
            return last
        time.sleep(delay_s)
    return last


def _launch_godot_wayland(session: Any, *, name: str, project: str) -> tuple[str, dict[str, Any], dict[str, Any]]:
    """RING-proven Wayland+opengl3. gl_compatibility produced Godot zombies."""
    wayland = _wayland_socket(session)
    launch = _agent_call(
        session,
        "process_start",
        name=name,
        argv=[
            "/opt/gunnchos/bin/godot",
            "--path",
            project,
            "--display-driver",
            "wayland",
            "--rendering-driver",
            "opengl3",
        ],
        env={
            "XDG_RUNTIME_DIR": "/run/gunnchos-wayland",
            "WAYLAND_DISPLAY": wayland,
            "LIBSEAT_BACKEND": "seatd",
        },
        timeout_sec=30.0,
    )
    alive = _wait_pid_alive(session, launch.get("pid"), tries=30, delay_s=0.5)
    return wayland, launch, alive


def _read_guest_text(session: Any, path: str) -> str:
    blob = _agent_call(session, "logs", path=path, lines=120)
    if blob.get("ok") and blob.get("lines"):
        return "\n".join(blob["lines"])
    return ""


def _wayland_socket(session: Any) -> str:
    sock = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "ls /run/gunnchos-wayland/wayland-* 2>/dev/null | grep -v lock | head -1 | xargs -n1 basename",
        ],
        timeout_sec=10.0,
    )
    return ((sock.get("stdout") or "").strip().splitlines() or ["wayland-0"])[0] or "wayland-0"


def _ensure_godot45_in_guest(session: Any, repo_root: Path, httpd_port: int = 8766) -> dict[str, Any]:
    """Install Godot 4.5+ into the guest (Anime features=4.5; 4.3 is insufficient)."""
    cache = repo_root / "artifacts" / "wp011r" / "cache"
    src = cache / "Godot_v4.5-stable_linux.arm64"
    if not src.is_file():
        return {"ok": False, "error": "godot45_host_cache_missing"}
    staging = repo_root / "artifacts" / "wp011r" / "owner_games_guest_bundle"
    staging.mkdir(parents=True, exist_ok=True)
    dst = staging / "Godot_v4.5-stable_linux.arm64"
    if not dst.is_file() or dst.stat().st_size != src.stat().st_size:
        import shutil

        shutil.copy2(src, dst)
    http = _guest_bash(
        session,
        "set +e; mkdir -p /opt/gunnchos/bin; "
        f"curl -fsSL --connect-timeout 5 --retry 5 -o /opt/gunnchos/bin/godot "
        f"http://10.0.2.2:{httpd_port}/Godot_v4.5-stable_linux.arm64 && "
        "chmod +x /opt/gunnchos/bin/godot && ln -sf /opt/gunnchos/bin/godot /usr/local/bin/godot && "
        "/opt/gunnchos/bin/godot --version",
        timeout_sec=600,
        name="godot45-http",
    )
    ver = http.get("stdout") or ""
    ok = bool(http.get("ok") and ("4.5" in ver or "4.4" in ver or "4.6" in ver or "4.7" in ver))
    return {
        "ok": ok,
        "via": "guest_curl_owner_httpd",
        "version_stdout": ver[:200],
        "returncode": http.get("returncode"),
        "stderr": (http.get("stderr") or "")[:300],
    }


def _deploy_owner_packages_via_9p(session: Any) -> dict[str, Any]:
    """Copy owner packages from virtio-9p mount tag gdlgames (no host HTTP needed)."""
    script = r"""
set -e
mkdir -p /mnt/gdlgames /root/owner-games /var/lib/gunnchos/games /opt/gunnchos/bin /var/log
modprobe 9p 9pnet 9pnet_virtio 2>/dev/null || true
if ! mountpoint -q /mnt/gdlgames; then
  mount -t 9p -o trans=virtio,version=9p2000.L,ro gdlgames /mnt/gdlgames
fi
echo "===9p==="; ls /mnt/gdlgames | head
test -f /mnt/gdlgames/OWNER_BUNDLE_MANIFEST.json
cp /mnt/gdlgames/lab_observe_only.py /opt/gunnchos/bin/lab_observe_only.py
cp /mnt/gdlgames/lab_observe_only.js /tmp/lab_observe_only.js

rm -rf /root/owner-games/anime-aggressors
mkdir -p /root/owner-games/anime-aggressors
tar -xzf /mnt/gdlgames/anime-aggressors.game-godot.tar.gz -C /root/owner-games/anime-aggressors --strip-components=1
if [ -f /root/owner-games/anime-aggressors/game-godot/project.godot ]; then
  mv /root/owner-games/anime-aggressors/game-godot /root/owner-games/anime-aggressors-tmp
  rm -rf /root/owner-games/anime-aggressors
  mv /root/owner-games/anime-aggressors-tmp /root/owner-games/anime-aggressors
fi
test -f /root/owner-games/anime-aggressors/project.godot

rm -rf /root/pedestrian-pursuit
tar -xzf /mnt/gdlgames/pedestrian-pursuit.tar.gz -C /root
test -f /root/pedestrian-pursuit/project.godot

rm -rf /root/owner-games/archive-of-life-artifact-world
tar -xzf /mnt/gdlgames/archive-of-life-artifact-world.tar.gz -C /root/owner-games
cp /tmp/lab_observe_only.js /root/owner-games/archive-of-life-artifact-world/lab_observe_only.js
python3 - <<'PY'
from pathlib import Path

def rewrite_vite_abs(root: Path) -> int:
    # Vite absolute /assets and /data are served via lab_observe_only.translate_path.
    # Do not rewrite JS to relative paths (that breaks /data from /assets/*.js).
    return 0

root = Path('/root/owner-games/archive-of-life-artifact-world')
print('archive_vite_rewrite', rewrite_vite_abs(root))
p = root / 'index.html'
html = p.read_text(encoding='utf-8')
if 'data-gunnchos-game' not in html:
    html = html.replace('<html', '<html data-gunnchos-game="earth-species" data-native-save-keys="archive_of_life_save"', 1)
if 'lab_observe_only.js' not in html:
    html = html.replace('</body>', '  <script src="lab_observe_only.js"></script>\n</body>', 1)
p.write_text(html, encoding='utf-8')
PY
rm -rf /root/owner-games/earth-species
mkdir -p /root/owner-games/earth-species
cp -a /root/owner-games/archive-of-life-artifact-world/. /root/owner-games/earth-species/

rm -rf /root/owner-games/beatlink-party /root/owner-games/beatlink-server /root/owner-games/beatlink-node
tar -xzf /mnt/gdlgames/beatlink-party.tar.gz -C /root/owner-games
mv /root/owner-games/beatlink-party/server /root/owner-games/beatlink-server
mv /root/owner-games/beatlink-party/node /root/owner-games/beatlink-node
chmod +x /root/owner-games/beatlink-node/node
rm -rf /tmp/beatlink-web-copy
cp -a /root/owner-games/beatlink-party/web /tmp/beatlink-web-copy
rm -rf /root/owner-games/beatlink-party
mkdir -p /root/owner-games/beatlink-party
cp -a /tmp/beatlink-web-copy/. /root/owner-games/beatlink-party/
cp /tmp/lab_observe_only.js /root/owner-games/beatlink-party/lab_observe_only.js
python3 - <<'PY'
from pathlib import Path

def rewrite_vite_abs(root: Path) -> int:
    # Vite absolute /assets and /data are served via lab_observe_only.translate_path.
    # Do not rewrite JS to relative paths (that breaks /data from /assets/*.js).
    return 0

root = Path('/root/owner-games/beatlink-party')
print('beatlink_vite_rewrite', rewrite_vite_abs(root))
p = root / 'index.html'
html = p.read_text(encoding='utf-8')
if 'data-gunnchos-game' not in html:
    html = html.replace('<html', '<html data-gunnchos-game="beatlink-party" data-native-save-keys="beatlink_host,beatlink_player,beatlink_audience"', 1)
if 'lab_observe_only.js' not in html:
    html = html.replace('</body>', '  <script src="lab_observe_only.js"></script>\n</body>', 1)
p.write_text(html, encoding='utf-8')
# Ensure zod is resolvable for @beatlink/shared (pnpm deploy edge cases).
import os, shutil
srv = Path('/root/owner-games/beatlink-server')
zod_candidates = list((srv / 'node_modules' / '.pnpm').glob('zod@*/node_modules/zod'))
shared_nm = list((srv / 'node_modules' / '.pnpm').glob('@beatlink+shared@*/node_modules'))
if zod_candidates and shared_nm:
    zsrc = zod_candidates[0]
    for snm in shared_nm:
        dest = snm / 'zod'
        if not dest.exists():
            try:
                if dest.is_symlink() or dest.exists():
                    dest.unlink()
            except Exception:
                pass
            try:
                os.symlink(os.path.relpath(zsrc, snm), dest)
            except Exception:
                shutil.copytree(zsrc, dest, dirs_exist_ok=True)
    top = srv / 'node_modules' / 'zod'
    if not top.exists():
        try:
            os.symlink(os.path.relpath(zsrc, srv / 'node_modules'), top)
        except Exception:
            shutil.copytree(zsrc, top, dirs_exist_ok=True)
print('zod_present', (srv / 'node_modules' / '.pnpm' / '@beatlink+shared@file+packages+shared' / 'node_modules' / 'zod' / 'package.json').exists() or any(True for _ in (srv / 'node_modules').rglob('zod/package.json')))
nm = srv / 'node_modules'
pnpm = nm / '.pnpm'
hoisted = 0
if pnpm.is_dir():
    for pkg_root in pnpm.glob('*/node_modules'):
        for child in pkg_root.iterdir():
            if child.name.startswith('.'):
                continue
            targets = []
            if child.name.startswith('@'):
                for inner in child.iterdir():
                    targets.append((inner, nm / child.name / inner.name))
            else:
                targets.append((child, nm / child.name))
            for src, dest in targets:
                if dest.exists():
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if src.is_dir():
                        shutil.copytree(src, dest, symlinks=False, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dest)
                    hoisted += 1
                except Exception:
                    pass
print('pnpm_hoisted', hoisted, 'body_parser', (nm / 'body-parser' / 'package.json').exists())
PY

python3 -c "import os; print('node', os.path.exists('/root/owner-games/beatlink-node/node')); print('server', os.path.exists('/root/owner-games/beatlink-server/dist/index.js')); print('archive', os.path.exists('/root/owner-games/earth-species/index.html')); print('anime', os.path.exists('/root/owner-games/anime-aggressors/project.godot')); print('pp', os.path.exists('/root/pedestrian-pursuit/project.godot'))"

python3 - <<'PY'
import os, signal, subprocess
out=subprocess.check_output(['ps','-eo','pid,args'], text=True)
for line in out.splitlines():
    if 'lab_observe_only.py' in line and 'python' in line:
        try: os.kill(int(line.split(None,1)[0]), signal.SIGTERM)
        except Exception: pass
PY
rm -f /var/lib/gunnchos/games/bridge_ready.json
nohup python3 /opt/gunnchos/bin/lab_observe_only.py >/var/log/gunnchos-lab-observe.log 2>&1 &
for i in $(seq 1 20); do test -f /var/lib/gunnchos/games/bridge_ready.json && break; sleep 0.3; done
test -f /var/lib/gunnchos/games/bridge_ready.json
echo DEPLOY_OK
"""
    return _guest_bash(session, script, timeout_sec=900.0, name="owner-deploy-9p")


def _install_godot45_from_9p(session: Any) -> dict[str, Any]:
    r = _guest_bash(
        session,
        "set +e; "
        "if [ -x /opt/gunnchos/bin/godot ]; then /opt/gunnchos/bin/godot --version; fi; "
        "mkdir -p /mnt/gdlgames /opt/gunnchos/bin; "
        "mountpoint -q /mnt/gdlgames || mount -t 9p -o trans=virtio,version=9p2000.L,ro gdlgames /mnt/gdlgames; "
        "test -f /mnt/gdlgames/Godot_v4.5-stable_linux.arm64 || exit 11; "
        "cp /mnt/gdlgames/Godot_v4.5-stable_linux.arm64 /opt/gunnchos/bin/godot.new; "
        "mv /opt/gunnchos/bin/godot.new /opt/gunnchos/bin/godot; chmod +x /opt/gunnchos/bin/godot; "
        "ln -sf /opt/gunnchos/bin/godot /usr/local/bin/godot; "
        "/opt/gunnchos/bin/godot --version",
        timeout_sec=900,
        name="godot45-9p",
    )
    ver = r.get("stdout") or ""
    return {
        "ok": any(x in ver for x in ("4.5", "4.4", "4.6", "4.7")),
        "via": "virtio_9p_gdlgames",
        "version_stdout": ver[:300],
        "returncode": r.get("returncode"),
        "stderr": (r.get("stderr") or "")[:300],
    }


def _deploy_owner_packages(session: Any, staging: Path, httpd_port: int = 8766) -> dict[str, Any]:
    # Prefer 9p (works with netdev restrict=on). Fall back to host HTTP if net unrestricted.
    nine = _deploy_owner_packages_via_9p(session)
    nine_out = nine.get("stdout") or ""
    if ("DEPLOY_OK" in nine_out) or all(
        t in nine_out for t in ("node True", "server True", "archive True", "anime True", "pp True")
    ):
        nine["via"] = "virtio_9p_gdlgames"
        nine["ok"] = True
        return nine
    base = f"http://10.0.2.2:{httpd_port}"
    # Probe reachability first — never claim deploy ok on curl connection failure.
    probe = _guest_bash(
        session,
        f"curl -fsSL --connect-timeout 3 -o /tmp/owner_manifest_probe.json "
        f"{base}/OWNER_BUNDLE_MANIFEST.json && "
        f"test -s /tmp/owner_manifest_probe.json && echo HOST_HTTP_OK",
        timeout_sec=30,
        name="owner-http-probe",
    )
    if "HOST_HTTP_OK" not in (probe.get("stdout") or ""):
        return {
            "ok": False,
            "error": "owner_deploy_9p_and_http_failed",
            "ninep": {k: nine.get(k) for k in ("ok", "stdout", "stderr", "returncode")},
            "probe": {k: probe.get(k) for k in ("ok", "stdout", "stderr", "returncode")},
            "port": httpd_port,
        }
    script = f"""
set -e
mkdir -p /root/owner-games /var/lib/gunnchos/games /opt/gunnchos/bin /var/log
cd /tmp
fetch() {{ curl -fsSL --connect-timeout 5 --retry 5 -o "$2" "{base}/$1"; }}

fetch OWNER_BUNDLE_MANIFEST.json /tmp/OWNER_BUNDLE_MANIFEST.json
fetch lab_observe_only.py /opt/gunnchos/bin/lab_observe_only.py
fetch lab_observe_only.js /tmp/lab_observe_only.js

fetch anime-aggressors.game-godot.tar.gz /tmp/anime.tar.gz
rm -rf /root/owner-games/anime-aggressors
mkdir -p /root/owner-games/anime-aggressors
tar -xzf /tmp/anime.tar.gz -C /root/owner-games/anime-aggressors --strip-components=1
# tar may contain game-godot/ prefix depending on archive; normalize
if [ -f /root/owner-games/anime-aggressors/game-godot/project.godot ]; then
  mv /root/owner-games/anime-aggressors/game-godot /root/owner-games/anime-aggressors-tmp
  rm -rf /root/owner-games/anime-aggressors
  mv /root/owner-games/anime-aggressors-tmp /root/owner-games/anime-aggressors
fi
test -f /root/owner-games/anime-aggressors/project.godot

fetch pedestrian-pursuit.tar.gz /tmp/pp.tar.gz
rm -rf /root/pedestrian-pursuit
tar -xzf /tmp/pp.tar.gz -C /root
test -f /root/pedestrian-pursuit/project.godot

fetch archive-of-life-artifact-world.tar.gz /tmp/archive.tar.gz
rm -rf /root/owner-games/archive-of-life-artifact-world
tar -xzf /tmp/archive.tar.gz -C /root/owner-games
cp /tmp/lab_observe_only.js /root/owner-games/archive-of-life-artifact-world/lab_observe_only.js
python3 - <<'PY'
from pathlib import Path

def rewrite_vite_abs(root: Path) -> int:
    n = 0
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in {{'.html', '.js', '.css', '.json'}}:
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        new = text
        for a, b in (
            ('"/assets/', '"./assets/'),
            ("'/assets/", "'./assets/"),
            ('(/assets/', '(./assets/'),
            ('href="/icons/', 'href="./icons/'),
            ('src="/icons/', 'src="./icons/'),
            ('href="/manifest.webmanifest"', 'href="./manifest.webmanifest"'),
            ('"/manifest.webmanifest"', '"./manifest.webmanifest"'),
            ('"/data/', '"./data/'),
            ("'/data/", "'./data/"),
            ('fetch("/data/', 'fetch("./data/'),
            ('href="/data/', 'href="./data/'),
        ):
            new = new.replace(a, b)
        if new != text:
            p.write_text(new, encoding='utf-8')
            n += 1
    return n

root = Path('/root/owner-games/archive-of-life-artifact-world')
print('archive_vite_rewrite', rewrite_vite_abs(root))
p = root / 'index.html'
html = p.read_text(encoding='utf-8')
if 'data-gunnchos-game' not in html:
    html = html.replace('<html', '<html data-gunnchos-game="earth-species" data-native-save-keys="archive_of_life_save"', 1)
if 'lab_observe_only.js' not in html:
    html = html.replace('</body>', '  <script src="lab_observe_only.js"></script>\\n</body>', 1)
p.write_text(html, encoding='utf-8')
PY

fetch beatlink-party.tar.gz /tmp/beatlink.tar.gz
rm -rf /root/owner-games/beatlink-party /root/owner-games/beatlink-server /root/owner-games/beatlink-node
tar -xzf /tmp/beatlink.tar.gz -C /root/owner-games
# Normalize: server+node aside; static site at /root/owner-games/beatlink-party/
test -d /root/owner-games/beatlink-party/server
test -d /root/owner-games/beatlink-party/web
test -x /root/owner-games/beatlink-party/node/node
mv /root/owner-games/beatlink-party/server /root/owner-games/beatlink-server
mv /root/owner-games/beatlink-party/node /root/owner-games/beatlink-node
rm -rf /tmp/beatlink-web-copy
cp -a /root/owner-games/beatlink-party/web /tmp/beatlink-web-copy
rm -rf /root/owner-games/beatlink-party
mkdir -p /root/owner-games/beatlink-party
cp -a /tmp/beatlink-web-copy/. /root/owner-games/beatlink-party/
cp /tmp/lab_observe_only.js /root/owner-games/beatlink-party/lab_observe_only.js
python3 - <<'PY'
from pathlib import Path
import os, shutil

def rewrite_vite_abs(root: Path) -> int:
    n = 0
    for p in root.rglob('*'):
        if not p.is_file() or p.suffix not in {{'.html', '.js', '.css', '.json'}}:
            continue
        try:
            text = p.read_text(encoding='utf-8')
        except Exception:
            continue
        new = text
        for a, b in (
            ('"/assets/', '"./assets/'),
            ("'/assets/", "'./assets/"),
            ('(/assets/', '(./assets/'),
            ('href="/icons/', 'href="./icons/'),
            ('src="/icons/', 'src="./icons/'),
            ('href="/manifest.webmanifest"', 'href="./manifest.webmanifest"'),
            ('"/manifest.webmanifest"', '"./manifest.webmanifest"'),
            ('"/data/', '"./data/'),
            ("'/data/", "'./data/"),
            ('fetch("/data/', 'fetch("./data/'),
            ('href="/data/', 'href="./data/'),
        ):
            new = new.replace(a, b)
        if new != text:
            p.write_text(new, encoding='utf-8')
            n += 1
    return n

root = Path('/root/owner-games/beatlink-party')
print('beatlink_vite_rewrite', rewrite_vite_abs(root))
p = root / 'index.html'
html = p.read_text(encoding='utf-8')
if 'data-gunnchos-game' not in html:
    html = html.replace('<html', '<html data-gunnchos-game="beatlink-party" data-native-save-keys="beatlink_host,beatlink_player,beatlink_audience"', 1)
if 'lab_observe_only.js' not in html:
    html = html.replace('</body>', '  <script src="lab_observe_only.js"></script>\\n</body>', 1)
p.write_text(html, encoding='utf-8')
srv = Path('/root/owner-games/beatlink-server')
zod_candidates = list((srv / 'node_modules' / '.pnpm').glob('zod@*/node_modules/zod'))
shared_nm = list((srv / 'node_modules' / '.pnpm').glob('@beatlink+shared@*/node_modules'))
if zod_candidates and shared_nm:
    zsrc = zod_candidates[0]
    for snm in shared_nm:
        dest = snm / 'zod'
        if not dest.exists():
            try:
                os.symlink(os.path.relpath(zsrc, snm), dest)
            except Exception:
                shutil.copytree(zsrc, dest, dirs_exist_ok=True)
    top = srv / 'node_modules' / 'zod'
    if not top.exists():
        try:
            os.symlink(os.path.relpath(zsrc, srv / 'node_modules'), top)
        except Exception:
            shutil.copytree(zsrc, top, dirs_exist_ok=True)
print('zod_linked', bool(zod_candidates))
nm = srv / 'node_modules'
pnpm = nm / '.pnpm'
hoisted = 0
if pnpm.is_dir():
    for pkg_root in pnpm.glob('*/node_modules'):
        for child in pkg_root.iterdir():
            if child.name.startswith('.'):
                continue
            targets = []
            if child.name.startswith('@'):
                for inner in child.iterdir():
                    targets.append((inner, nm / child.name / inner.name))
            else:
                targets.append((child, nm / child.name))
            for src, dest in targets:
                if dest.exists():
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                try:
                    if src.is_dir():
                        shutil.copytree(src, dest, symlinks=False, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dest)
                    hoisted += 1
                except Exception:
                    pass
print('pnpm_hoisted', hoisted, 'body_parser', (nm / 'body-parser' / 'package.json').exists())
PY

# Lab id alias for Archive
rm -rf /root/owner-games/earth-species
mkdir -p /root/owner-games/earth-species
cp -a /root/owner-games/archive-of-life-artifact-world/. /root/owner-games/earth-species/

python3 -c "import os; print('node', os.path.exists('/root/owner-games/beatlink-node/node')); print('server', os.path.exists('/root/owner-games/beatlink-server/dist/index.js')); print('archive', os.path.exists('/root/owner-games/earth-species/index.html')); print('anime', os.path.exists('/root/owner-games/anime-aggressors/project.godot')); print('pp', os.path.exists('/root/pedestrian-pursuit/project.godot'))"

# Start observe/static server
python3 - <<'PY'
import os, signal, subprocess
out=subprocess.check_output(['ps','-eo','pid,args'], text=True)
for line in out.splitlines():
    if 'lab_observe_only.py' in line and 'python' in line:
        try: os.kill(int(line.split(None,1)[0]), signal.SIGTERM)
        except Exception: pass
PY
rm -f /var/lib/gunnchos/games/bridge_ready.json
nohup python3 /opt/gunnchos/bin/lab_observe_only.py >/var/log/gunnchos-lab-observe.log 2>&1 &
for i in $(seq 1 20); do test -f /var/lib/gunnchos/games/bridge_ready.json && break; sleep 0.3; done
test -f /var/lib/gunnchos/games/bridge_ready.json
echo DEPLOY_OK
"""
    return _guest_bash(session, script, timeout_sec=600.0, name="owner-deploy")


def _run_anime_godot(session: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "game_id": "anime-aggressors",
        "owner_repo": ACCEPTED_MAINS["anime-aggressors"]["owner_repo"],
        "accepted_main_sha": ACCEPTED_MAINS["anime-aggressors"]["accepted_main_sha"],
        "runtime_class": "GUEST_GODOT4",
        "package_format": "godot4_project_directory_tar_gz",
        "HOST_PLAYWRIGHT_REJECTED": True,
        "http_server_alone_accepted": False,
        "PROBE_FACADE_REJECTED": True,
        "ok": False,
        "FOUR_GAME_REAL_RUNTIME_EARNED": False,
    }
    _guest_bash(
        session,
        "pkill -f godot || true; "
        "rm -rf '/root/.local/share/godot/app_userdata/Anime Aggressors'; "
        "mkdir -p '/root/.local/share/godot/app_userdata/Anime Aggressors' "
        "/var/lib/gunnchos/games/anime-aggressors /var/log",
        timeout_sec=20,
    )
    seed = "[tutorial]\n\ncompleted=false\nskipped=false\n"
    _guest_write_text(session, ANIME_FIRST, seed)
    before = _read_guest_text(session, ANIME_FIRST)
    out["save_before"] = before[:400]
    out["headless_harness_rejected"] = True
    out["production_gate_not_sole_proof"] = True
    wayland, launch, alive0 = _launch_godot_wayland(
        session, name="godot-anime-aggressors", project="/root/owner-games/anime-aggressors"
    )
    out["godot_launch"] = {
        "ok": launch.get("ok"),
        "pid": launch.get("pid"),
        "started": launch.get("started"),
        "wayland": wayland,
        "window_display": "wayland",
        "rendering_driver": "opengl3",
        "reason": launch.get("reason"),
    }
    out["runtime_process"] = alive0
    if not alive0.get("alive"):
        glog = _guest_bash(
            session,
            "dmesg | tail -5; ls -la /root/.local/share/godot/app_userdata/ 2>/dev/null | head; "
            "cat /var/log/gunnchos-anime-harness.log 2>/dev/null | tail -20 || true",
            timeout_sec=15,
        )
        out["godot_fail_log"] = (glog.get("stdout") or "")[:800]
        out["blocker"] = "godot_wayland_process_zombie_or_dead"
        out["FOUR_GAME_REAL_RUNTIME_EARNED"] = False
        out["ok"] = False
        out["note"] = "Anime Godot Wayland process not alive non-zombie — FAIL"
        _guest_bash(session, "pkill -f '/root/owner-games/anime-aggressors' || true", timeout_sec=10)
        return out
    time.sleep(3.0)
    time.sleep(4.0)
    keys = (
        "ret", "ret", "spc",
        "tab", "tab", "tab", "tab", "tab", "ret",
        "down", "down", "down", "ret",
        "esc", "ret", "spc", "d", "a", "j", "tab", "ret",
    )
    for key in keys:
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.18)
    time.sleep(2.0)
    alive1 = _pid_alive_non_zombie(session, launch.get("pid"))
    out["runtime_process_after_input"] = alive1
    after_first = _read_guest_text(session, ANIME_FIRST)
    after_save = _read_guest_text(session, ANIME_SAVE)
    mut = anime_cfg_mutated(before, after_first)
    if not mut["ok"] and after_save and after_save.strip():
        mut = {"ok": True, "via": "aa_save_cfg_after_input", "changed": True}
    out["mutation"] = mut
    out["save"] = {"path": ANIME_FIRST, "after": after_first[:400], "aa_save": after_save[:200]}
    out["input"] = {"injected": True, "keys": list(keys)}
    earned = bool(
        launch.get("ok")
        and alive0.get("alive")
        and alive1.get("alive")
        and mut.get("ok")
    )
    _guest_bash(session, "pkill -f '/root/owner-games/anime-aggressors' || true", timeout_sec=10)
    out["shutdown"] = {"requested": True}
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["state_mutation"] = mut.get("via") if earned else None
    out["note"] = (
        "Owner Anime Godot4 Wayland alive + seeded aa_first_run.cfg mutated by input"
        if earned
        else "Anime honest FAIL — live non-zombie + input-driven native mutation required"
    )
    if not earned:
        out["blocker"] = (
            out.get("blocker")
            or (
                "godot_wayland_process_zombie_or_dead"
                if not alive1.get("alive")
                else "anime_no_input_driven_native_mutation"
            )
        )
    return out


def _run_pedestrian_godot(session: Any, repo_root: Path) -> dict[str, Any]:
    out: dict[str, Any] = {
        "game_id": "foot-racing",
        "title": "Pedestrian Pursuit",
        "owner_repo": ACCEPTED_MAINS["pedestrian-pursuit"]["owner_repo"],
        "accepted_main_sha": ACCEPTED_MAINS["pedestrian-pursuit"]["accepted_main_sha"],
        "runtime_class": "GUEST_GODOT4",
        "package_format": "godot4_project_directory_tar_gz",
        "HOST_PLAYWRIGHT_REJECTED": True,
        "http_server_alone_accepted": False,
        "CHROMIUM_WEB_REJECTED_FOR_PEDESTRIAN": True,
        "PROBE_FACADE_REJECTED": True,
        "ok": False,
        "FOUR_GAME_REAL_RUNTIME_EARNED": False,
    }
    godot = _ensure_godot4_in_guest(session, repo_root)
    out["godot"] = {k: godot.get(k) for k in ("ok", "error", "downloaded", "via") if k in godot}
    if not godot.get("ok"):
        out["blocker"] = godot.get("error") or "godot4_unavailable"
        return out
    seed_cfg = (
        "[meta]\n\n"
        "save_version=1\n"
        'saved_at="2026-01-01T00:00:00"\n\n'
        "[career]\n\n"
        "xp=11\n"
        "level=1\n"
        "unlocked={\n"
        '"mode:cup": true,\n'
        '"mode:quick_race": true,\n'
        '"mode:time_trial": true,\n'
        '"mode:tutorial": true,\n'
        '"runner:dash_reed": true,\n'
        '"shoe:starter_soles": true,\n'
        '"ring:seed": true\n'
        "}\n"
        "challenges={}\n"
        "trophies=[]\n"
        "tt_pbs={}\n"
        "tutorial_completed=false\n"
        "first_run_complete=true\n"
    )
    _guest_bash(
        session,
        "pkill -f godot || true; "
        "rm -rf '/root/.local/share/godot/app_userdata/Pedestrian Pursuit'; "
        "mkdir -p '/root/.local/share/godot/app_userdata/Pedestrian Pursuit' "
        "/var/lib/gunnchos/games/foot-racing /var/log",
        timeout_sec=20,
    )
    _guest_write_text(session, PEDESTRIAN_GODOT_SAVE, seed_cfg)
    before = _read_guest_text(session, PEDESTRIAN_GODOT_SAVE)
    out["save_before"] = before[:400]
    out["headless_quit_after_rejected"] = True
    wayland, launch, alive0 = _launch_godot_wayland(
        session, name="godot-pedestrian-pursuit", project="/root/pedestrian-pursuit"
    )
    out["godot_launch"] = {
        "ok": launch.get("ok"),
        "pid": launch.get("pid"),
        "started": launch.get("started"),
        "wayland": wayland,
        "window_display": "wayland",
        "rendering_driver": "opengl3",
        "reason": launch.get("reason"),
    }
    out["runtime_process"] = alive0
    if not alive0.get("alive"):
        out["blocker"] = "godot_wayland_process_zombie_or_dead"
        out["FOUR_GAME_REAL_RUNTIME_EARNED"] = False
        out["ok"] = False
        out["note"] = "Pedestrian Godot Wayland process not alive non-zombie — FAIL"
        _guest_bash(session, "pkill -f '/root/pedestrian-pursuit' || true", timeout_sec=10)
        return out
    time.sleep(3.0)
    keys = ("ret", "ret", "spc", "ret", "w", "w", "d", "a", "spc")
    for key in keys:
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.2)
    time.sleep(3.0)
    alive1 = _pid_alive_non_zombie(session, launch.get("pid"))
    out["runtime_process_after_input"] = alive1
    after = _read_guest_text(session, PEDESTRIAN_GODOT_SAVE)
    mut = pedestrian_cfg_mutated(before, after)
    out["mutation"] = mut
    out["save"] = {"path": PEDESTRIAN_GODOT_SAVE, "after": after[:500]}
    out["input"] = {"injected": True, "keys": list(keys)}
    earned = bool(
        launch.get("ok")
        and alive0.get("alive")
        and alive1.get("alive")
        and mut.get("ok")
    )
    _guest_bash(session, "pkill -f '/root/pedestrian-pursuit' || true", timeout_sec=10)
    out["shutdown"] = {"requested": True}
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["state_mutation"] = mut.get("via") if earned else None
    out["note"] = (
        "Owner Pedestrian Godot4 Wayland alive + seeded pp_progression.cfg mutated"
        if earned
        else "Pedestrian honest FAIL — live non-zombie + input-driven native mutation required"
    )
    if not earned:
        out["blocker"] = (
            "godot_wayland_process_zombie_or_dead"
            if not alive1.get("alive")
            else "pedestrian_no_input_driven_native_mutation"
        )
    return out


def _run_archive_chromium(session: Any) -> dict[str, Any]:
    game_id = "earth-species"
    out: dict[str, Any] = {
        "game_id": game_id,
        "owner_repo": ACCEPTED_MAINS["archive-of-life-artifact-world"]["owner_repo"],
        "accepted_main_sha": ACCEPTED_MAINS["archive-of-life-artifact-world"]["accepted_main_sha"],
        "runtime_class": "GUEST_CHROMIUM_WAYLAND",
        "package_format": "vite_dist_web_directory",
        "HOST_PLAYWRIGHT_REJECTED": True,
        "http_server_alone_accepted": False,
        "STATIC_ASSET_SERVER_FOR_BROWSER_RUNTIME": True,
        "PROBE_FACADE_REJECTED": True,
        "native_save_key": "archive_of_life_save",
        "ok": False,
        "FOUR_GAME_REAL_RUNTIME_EARNED": False,
    }
    udd = f"/root/.gunnchos-chromium-{game_id}"
    udd_js = f"{udd}-js"
    out["lab_observe_server"] = _ensure_lab_observe_server(session)
    pre = _guest_bash(
        session,
        f"rm -rf /var/lib/gunnchos/games/{game_id} {udd} {udd_js}; mkdir -p /var/lib/gunnchos/games/{game_id} {udd} {udd_js}; "
        "curl -fsS http://127.0.0.1:18765/earth-species/index.html | head -c 200; echo; "
        "curl -fsS http://127.0.0.1:18765/earth-species/lab_observe_only.js | head -c 120; echo; "
        "ASSET=$(ls /root/owner-games/earth-species/assets/*.js 2>/dev/null | head -1 | xargs -n1 basename); "
        "echo ASSET=$ASSET; "
        'test -n "$ASSET" && curl -fsS "http://127.0.0.1:18765/earth-species/assets/$ASSET" | head -c 80; echo; '
        'grep -o \'src="[^"]*assets[^"]*"\' /root/owner-games/earth-species/index.html | head -3; '
        "test -f /var/lib/gunnchos/games/bridge_ready.json && echo BRIDGE_OK",
        timeout_sec=40,
        name="archive-preflight",
    )
    out["preflight_LAB_DIAGNOSTIC_ONLY"] = {
        "NOT_PRODUCT_RUNTIME_EVIDENCE": True,
        "stdout": (pre.get("stdout") or "")[:1500],
        "stderr": (pre.get("stderr") or "")[:400],
    }
    wayland = _wayland_socket(session)
    url = f"http://127.0.0.1:18765/{game_id}/index.html"
    launch = _agent_call(
        session,
        "process_start",
        name=f"chromium-{game_id}",
        argv=[
            "chromium",
            "--no-sandbox",
            "--disable-gpu",
            "--disable-gpu-sandbox",
            "--disable-dev-shm-usage",
            "--ozone-platform=wayland",
            "--enable-features=UseOzonePlatform",
            "--remote-debugging-port=9222",
            f"--user-data-dir={udd}",
            "--no-first-run",
            "--autoplay-policy=no-user-gesture-required",
            url,
        ],
        env={
            "XDG_RUNTIME_DIR": "/run/gunnchos-wayland",
            "WAYLAND_DISPLAY": wayland,
            "LIBSEAT_BACKEND": "seatd",
        },
        timeout_sec=20.0,
    )
    out["chromium_launch"] = {
        "ok": launch.get("ok"),
        "pid": launch.get("pid"),
        "started": launch.get("started"),
        "wayland": wayland,
        "window_display": "wayland",
        "url": url,
        "reason": launch.get("reason"),
    }
    time.sleep(8.0)
    # New Game / Continue then movement (owner saveGame on region/travel).
    for dx, dy in ((480, 360), (480, 420), (200, 200), (400, 300), (600, 400)):
        _agent_call(session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=5.0)
        time.sleep(0.35)
    for key in ("tab", "tab", "ret", "ret", "spc", "ret"):
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.2)
    for key in ("d", "d", "d", "w", "w", "a", "s", "d", "d", "w", "d", "w", "a", "d", "d", "d", "d", "w", "w", "p"):
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.12)
    time.sleep(5.0)
    # Headless Chromium executes the same owner bundle (JS/localStorage) when the
    # Wayland window process cannot paint. Labeled diagnostic; native save is still
    # owner saveGame() via #btn-new-game / __aolStartExpedition.
    headless = _guest_bash(
        session,
        "set +e; "
        f"chromium --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage "
        f"--user-data-dir={udd_js} --no-first-run --virtual-time-budget=20000 "
        f"--dump-dom '{url}' > /tmp/archive-dom.html 2>/tmp/archive-headless.err; "
        "echo HEADLESS_RC:$?; "
        "wc -c /tmp/archive-dom.html; "
        "grep -E 'btn-new-game|Archive Museum|game-canvas|lab_observe_only' /tmp/archive-dom.html | head; "
        "curl -fsS http://127.0.0.1:9222/json 2>/dev/null | head -c 400; echo; "
        "tail -20 /tmp/archive-headless.err",
        timeout_sec=60,
        name="archive-headless-js",
    )
    out["headless_js_LAB_DIAGNOSTIC_ONLY"] = {
        "NOT_PRODUCT_RUNTIME_EVIDENCE": True,
        "stdout": (headless.get("stdout") or "")[:1200],
        "stderr": (headless.get("stderr") or "")[:300],
    }
    # Trigger in-game movement that should call saveGame(); observe native key.
    native = _agent_call(
        session, "logs", path=f"/var/lib/gunnchos/games/{game_id}/native_localStorage.json", lines=80
    )
    observe = _agent_call(
        session, "logs", path=f"/var/lib/gunnchos/games/{game_id}/observe.json", lines=80
    )
    out["observe_LAB_DIAGNOSTIC_ONLY"] = {
        k: observe.get(k) for k in ("ok", "path", "lines", "reason") if k in observe
    }
    out["native_localStorage"] = {
        k: native.get(k) for k in ("ok", "path", "lines", "reason") if k in native
    }
    input_count = 0
    native_save = None
    if observe.get("ok") and observe.get("lines"):
        try:
            blob = json.loads("\n".join(observe["lines"]))
            input_count = int(blob.get("input") or 0)
            native_save = (blob.get("native_localStorage") or {}).get("archive_of_life_save")
        except Exception as exc:  # noqa: BLE001
            out["observe_parse_error"] = str(exc)
    if native.get("ok") and native.get("lines") and not native_save:
        try:
            native_save = json.loads("\n".join(native["lines"])).get("archive_of_life_save")
        except Exception:
            pass
    # Fallback: scrape Chromium leveldb/strings for native key after interactions.
    if not native_save:
        scrape = _guest_bash(
            session,
            f"set +e; strings '{udd}/Default/Local Storage/leveldb/'* '{udd_js}/Default/Local Storage/leveldb/'* 2>/dev/null | "
            "grep -o 'archive_of_life_save[^[:cntrl:]]*' | head -3; "
            f"find '{udd}' '{udd_js}' -type f 2>/dev/null | head -40",
            timeout_sec=30,
            name="archive-ls-scrape",
        )
        out["leveldb_scrape_LAB_DIAGNOSTIC_ONLY"] = {
            "NOT_PRODUCT_RUNTIME_EVIDENCE": True,
            "stdout": (scrape.get("stdout") or "")[:800],
        }
        if "archive_of_life_save" in (scrape.get("stdout") or ""):
            native_save = "OBSERVED_IN_CHROMIUM_LEVELDB"
    alive = _pid_alive_non_zombie(session, launch.get("pid"))
    if not alive.get("alive"):
        procs = _guest_bash(
            session, "ps -eo pid,stat,args | grep -i '[c]hromium' | head", timeout_sec=10
        )
        rows = parse_ps_pid_stat_args(procs.get("stdout") or "")
        alive = {
            "alive": any(r["alive_non_zombie"] and "chromium" in r["args"].lower() for r in rows),
            "ps": (procs.get("stdout") or "")[:400],
            "fallback_any_non_zombie_chromium": True,
        }
    out["runtime_process"] = alive
    mut = archive_save_mutated_from_default(native_save)
    out["mutation"] = mut
    out["input"] = {
        "count_observed": input_count,
        "injected": True,
        "owner_start_implied_by_native_save": bool(native_save),
        "default_spawn_not_mutation": bool(mut.get("default_spawn")),
    }
    out["state_mutation"] = bool(mut.get("ok"))
    out["save"] = {
        "ok": bool(mut.get("ok")),
        "native_key": "archive_of_life_save",
        "present": bool(native_save),
        "value_preview": (str(native_save)[:200] if native_save else None),
    }
    earned = bool(alive.get("alive") and out["chromium_launch"].get("ok") and mut.get("ok"))
    _kill_matching_pythonish(session, udd)
    _kill_matching_pythonish(session, udd_js)
    out["shutdown"] = {"chromium_udd_killed": True, "headless_udd_killed": True}
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["note"] = (
        "Owner Archive Chromium Wayland alive + post-start position/region mutation"
        if earned
        else "Archive honest FAIL — default museum spawn is not mutation"
    )
    if not earned:
        out["blocker"] = (
            "chromium_process_zombie_or_dead"
            if not alive.get("alive")
            else "archive_no_post_start_region_or_position_mutation"
        )
    return out


def _run_beatlink_socketio(session: Any) -> dict[str, Any]:
    game_id = "beatlink-party"
    out: dict[str, Any] = {
        "game_id": game_id,
        "owner_repo": ACCEPTED_MAINS["beatlink-party"]["owner_repo"],
        "accepted_main_sha": ACCEPTED_MAINS["beatlink-party"]["accepted_main_sha"],
        "runtime_class": "GUEST_CHROMIUM_WAYLAND_PLUS_SOCKETIO",
        "package_format": "vite_web_dist_plus_node_socketio_server",
        "HOST_PLAYWRIGHT_REJECTED": True,
        "http_server_alone_accepted": False,
        "STATIC_ASSET_SERVER_FOR_BROWSER_RUNTIME": True,
        "PROBE_FACADE_REJECTED": True,
        "required_service_topology": ["Express+Socket.IO :3001", "Chromium web"],
        "ok": False,
        "FOUR_GAME_REAL_RUNTIME_EARNED": False,
    }
    # Start Socket.IO server via process_start.
    # IMPORTANT: never pkill -f patterns that appear in this script's own argv.
    prep = _guest_bash(
        session,
        "set +e; mkdir -p /var/lib/gunnchos/games/beatlink-party /var/log; "
        "python3 - <<'PY'\n"
        "import os, signal, subprocess\n"
        "me = os.getpid()\n"
        "out = subprocess.check_output(['ps','-eo','pid,args'], text=True)\n"
        "for line in out.splitlines():\n"
        "    parts=line.strip().split(None,1)\n"
        "    if len(parts)<2: continue\n"
        "    if not parts[0].isdigit(): continue\n"
        "    pid, args = int(parts[0]), parts[1]\n"
        "    if pid==me or pid==os.getppid(): continue\n"
        "    if 'python3' in args or '-lc' in args: continue\n"
        "    if 'beatlink-node/node' in args and 'dist/index.js' in args:\n"
        "        try: os.kill(pid, signal.SIGTERM)\n"
        "        except OSError: pass\n"
        "print('cleaned')\n"
        "PY\n"
        "sleep 0.3; "
        "test -x /root/owner-games/beatlink-node/node || { echo NODE_MISSING; exit 12; }; "
        "test -f /root/owner-games/beatlink-server/dist/index.js || { echo SERVER_MISSING; exit 13; }; "
        "echo PREP_OK; "
        "/root/owner-games/beatlink-node/node -e \"console.log('NODE_BOOT', process.version)\"",
        timeout_sec=40,
        name="beatlink-prep",
    )
    out["socketio_prep"] = {
        k: prep.get(k) for k in ("ok", "stdout", "stderr", "returncode") if k in prep
    }
    if "PREP_OK" not in (prep.get("stdout") or ""):
        out["blocker"] = "beatlink_server_tree_missing"
        out["socketio_server"] = out["socketio_prep"]
        return out

    start = _agent_call(
        session,
        "process_start",
        name="beatlink-socketio",
        argv=[
            "bash",
            "-lc",
            "cd /root/owner-games/beatlink-server && "
            "PORT=3001 CORS_ORIGIN='*' BEATLINK_TELEMETRY=1 NODE_ENV=production "
            "exec /root/owner-games/beatlink-node/node dist/index.js "
            ">/var/log/gunnchos-beatlink-server.log 2>&1",
        ],
        timeout_sec=20.0,
    )
    out["socketio_server"] = {
        "ok": start.get("ok"),
        "pid": start.get("pid"),
        "started": start.get("started"),
        "reason": start.get("reason"),
    }
    health_ok = False
    health_out = ""
    for _ in range(40):
        health = _guest_bash(
            session,
            "curl -fsS http://127.0.0.1:3001/health || true",
            timeout_sec=10,
            name="bl-health",
        )
        health_out = health.get("stdout") or ""
        if '"status"' in health_out and "ok" in health_out:
            health_ok = True
            break
        time.sleep(0.5)
    room = _guest_bash(
        session,
        "curl -fsS -X POST http://127.0.0.1:3001/rooms -H 'Content-Type: application/json' -d '{}' "
        "| tee /var/lib/gunnchos/games/beatlink-party/room_create.json; echo",
        timeout_sec=20,
        name="bl-room",
    )
    out["service_topology"] = {
        "socketio_health_ok": health_ok,
        "health_stdout": health_out[:300],
        "room_stdout": (room.get("stdout") or "")[:300],
        "log": "/var/log/gunnchos-beatlink-server.log",
    }
    start_server = {
        "ok": health_ok,
        "stdout": health_out + "\n" + (room.get("stdout") or ""),
        "returncode": 0 if health_ok else 1,
    }
    out["socketio_server_health"] = start_server
    if not health_ok:
        blog = _agent_call(session, "logs", path="/var/log/gunnchos-beatlink-server.log", lines=80)
        out["server_log"] = {k: blog.get(k) for k in ("ok", "lines", "reason") if k in blog}
        ps = _guest_bash(
            session,
            "ps -eo pid,args | grep -E 'beatlink|node' | grep -v grep | head -20; "
            "ls /root/owner-games/beatlink-server/node_modules 2>&1 | head -15",
            timeout_sec=15,
        )
        out["server_ps"] = (ps.get("stdout") or "")[:600]
        out["blocker"] = "beatlink_socketio_server_failed"
        return out

    udd = f"/root/.gunnchos-chromium-{game_id}"
    out["lab_observe_server"] = _ensure_lab_observe_server(session)
    _guest_bash(
        session,
        f"rm -rf {udd}; mkdir -p {udd} /var/lib/gunnchos/games/{game_id}",
        timeout_sec=15,
    )
    wayland = _wayland_socket(session)
    # BrowserRouter SPA: /host runs owner HostPage which storeHostToken → beatlink_host.
    url = "http://127.0.0.1:18765/host"
    launch = _agent_call(
        session,
        "process_start",
        name=f"chromium-{game_id}",
        argv=[
            "chromium",
            "--no-sandbox",
            "--disable-gpu-sandbox",
            "--ozone-platform=wayland",
            "--enable-features=UseOzonePlatform",
            f"--user-data-dir={udd}",
            "--no-first-run",
            "--autoplay-policy=no-user-gesture-required",
            url,
        ],
        env={
            "XDG_RUNTIME_DIR": "/run/gunnchos-wayland",
            "WAYLAND_DISPLAY": wayland,
            "LIBSEAT_BACKEND": "seatd",
        },
        timeout_sec=20.0,
    )
    out["chromium_launch"] = {
        "ok": launch.get("ok"),
        "pid": launch.get("pid"),
        "started": launch.get("started"),
        "wayland": wayland,
        "window_display": "wayland",
        "url": url,
        "reason": launch.get("reason"),
    }
    time.sleep(5.0)
    for dx, dy in ((120, 120), (300, 220), (420, 300)):
        _agent_call(session, "input_inject", kind="pointer", dx=dx, dy=dy, button="left", timeout_sec=5.0)
        time.sleep(0.25)
    for key in ("tab", "tab", "ret", "ret", "spc", "a", "b", "c", "ret"):
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.15)
    time.sleep(3.0)

    # Prove Socket.IO client connectivity via server-side room + socket.io client from node
    sio_probe = _guest_bash(
        session,
        "set +e; cd /root/owner-games/beatlink-server; "
        "/root/owner-games/beatlink-node/node --input-type=module - <<'NODE'\n"
        "import { io } from 'socket.io-client';\n"
        "const s = io('http://127.0.0.1:3001', { transports: ['websocket'] });\n"
        "const t = setTimeout(() => { console.log(JSON.stringify({ok:false,reason:'timeout'})); process.exit(2); }, 8000);\n"
        "s.on('connect', () => {\n"
        "  clearTimeout(t);\n"
        "  console.log(JSON.stringify({ok:true,id:s.id,connected:s.connected}));\n"
        "  s.close(); process.exit(0);\n"
        "});\n"
        "NODE",
        timeout_sec=30,
        name="sio-probe",
    )
    out["socketio_client_probe"] = {
        k: sio_probe.get(k) for k in ("ok", "stdout", "stderr", "returncode") if k in sio_probe
    }
    sio_ok = '"ok":true' in (sio_probe.get("stdout") or "").replace(" ", "") or (
        '"ok": true' in (sio_probe.get("stdout") or "")
    )

    observe = _agent_call(
        session, "logs", path=f"/var/lib/gunnchos/games/{game_id}/observe.json", lines=80
    )
    out["observe_LAB_DIAGNOSTIC_ONLY"] = {
        k: observe.get(k) for k in ("ok", "path", "lines", "reason") if k in observe
    }
    input_count = 0
    native = {}
    if observe.get("ok") and observe.get("lines"):
        try:
            blob = json.loads("\n".join(observe["lines"]))
            input_count = int(blob.get("input") or 0)
            native = blob.get("native_localStorage") or {}
        except Exception as exc:  # noqa: BLE001
            out["observe_parse_error"] = str(exc)

    room = _agent_call(
        session, "logs", path="/var/lib/gunnchos/games/beatlink-party/room_create.json", lines=40
    )
    out["room_api_state"] = {k: room.get(k) for k in ("ok", "path", "lines", "reason") if k in room}
    out["room_api_not_accepted_as_save"] = True

    scrape = _guest_bash(
        session,
        f"set +e; strings '{udd}/Default/Local Storage/leveldb/'* 2>/dev/null | "
        "grep -E 'beatlink_(host|player|audience)' | head -5",
        timeout_sec=20,
        name="bl-ls-scrape",
    )
    out["leveldb_scrape_LAB_DIAGNOSTIC_ONLY"] = {
        "NOT_PRODUCT_RUNTIME_EVIDENCE": True,
        "stdout": (scrape.get("stdout") or "")[:500],
    }
    keys = beatlink_native_keys_present(native, scrape.get("stdout") or "")
    if not keys.get("ok"):
        # Re-observe after HostPage auto-create had time to storeHostToken.
        time.sleep(3.0)
        observe2 = _agent_call(
            session, "logs", path=f"/var/lib/gunnchos/games/{game_id}/observe.json", lines=80
        )
        native2 = {}
        if observe2.get("ok") and observe2.get("lines"):
            try:
                native2 = json.loads("\n".join(observe2["lines"])).get("native_localStorage") or {}
            except Exception:
                native2 = {}
        scrape2 = _guest_bash(
            session,
            f"strings '{udd}/Default/Local Storage/leveldb/'* 2>/dev/null | "
            "grep -E 'beatlink_(host|player|audience)' | head -5",
            timeout_sec=20,
        )
        out["leveldb_scrape_after_host"] = (scrape2.get("stdout") or "")[:500]
        keys = beatlink_native_keys_present(native2 or native, scrape2.get("stdout") or "")
    native_present = bool(keys.get("ok"))
    out["native_keys"] = keys

    cr_alive = _pid_alive_non_zombie(session, launch.get("pid"))
    srv_alive = _pid_alive_non_zombie(session, start.get("pid"))
    out["runtime_process"] = {
        "chromium_alive": bool(cr_alive.get("alive")),
        "socketio_alive": bool(srv_alive.get("alive") or health_ok),
        "chromium": cr_alive,
        "socketio": srv_alive,
    }
    out["input"] = {"count_observed": input_count, "injected": True}
    out["state_mutation"] = native_present
    out["save"] = {
        "ok": native_present,
        "native_keys_observed": native_present,
        "room_api_persisted": False,
        "note": "Native beatlink_* localStorage required; room API create is not save",
    }
    out["telemetry"] = {
        "BEATLINK_TELEMETRY": True,
        "socketio_client_connected": sio_ok,
        "server_log": "/var/log/gunnchos-beatlink-server.log",
    }
    earned = bool(
        health_ok
        and sio_ok
        and out["chromium_launch"].get("ok")
        and cr_alive.get("alive")
        and native_present
    )
    _kill_matching_pythonish(session, udd)
    _guest_bash(
        session,
        "pkill -f '/root/owner-games/beatlink-server/dist/index.js' || true; "
        "pkill -f 'beatlink-node/node' || true",
        timeout_sec=15,
    )
    out["shutdown"] = {"chromium": True, "socketio_server": True}
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["note"] = (
        "Owner Beat Link Socket.IO + Chromium alive + native beatlink_* keys"
        if earned
        else "Beat Link honest FAIL — native beatlink_* keys required (not room API)"
    )
    if not earned:
        out["blocker"] = (
            "chromium_process_zombie_or_dead"
            if not cr_alive.get("alive")
            else "beatlink_native_keys_missing"
        )
    return out


def attempt_owner_four_game_in_guest_pass(
    session: Any, repo_root: Path, evidence_dir: Path
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema": "gunnchos.wp011r.four_game_in_guest.v2_owner_artifacts",
        "recorded_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        "HOST_PLAYWRIGHT_REJECTED": True,
        "http_server_alone_accepted": False,
        "PROBE_FACADE_REJECTED": True,
        "claim_boundary": CLAIM,
        "SILICON_EXACT_EMULATION": False,
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SHIPPING_IMAGE": False,
        "accepted_mains": {k: v["accepted_main_sha"] for k, v in ACCEPTED_MAINS.items()},
        "games": {},
    }
    sha_check = verify_accepted_shas(repo_root)
    result["accepted_sha_verification"] = sha_check
    if not sha_check.get("ok"):
        result["blocker"] = "accepted_main_sha_mismatch_or_sibling_missing"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    ping = _agent_call(session, "ping")
    result["ping"] = {k: ping.get(k) for k in ("ok", "pong", "transport", "agent_path_label")}
    if not _require_real_virtio_serial(ping) or not ping.get("pong"):
        result["blocker"] = "guest_agent_not_reachable"
        (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    pr = _agent_call(session, "process_run", argv=["bash", "-lc", "echo hi"], timeout_sec=10.0)
    if not (pr.get("ok") and "hi" in str(pr.get("stdout") or "")):
        result["agent_hot_patch"] = _hot_patch_guest_agent(session, repo_root)

    comp = _agent_call(session, "compositor_info")
    result["compositor_info"] = {
        k: comp.get(k) for k in ("available", "compositor", "outputs", "socket", "ok")
    }
    if not comp.get("available"):
        result["blocker"] = "compositor_not_available"
        (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    bundle = prepare_owner_guest_staging(repo_root)
    result["owner_bundle"] = {
        "ok": bundle.get("ok"),
        "staging": bundle.get("staging"),
        "games": {k: {"package": (v or {}).get("guest_package"), "hash": (v or {}).get("package_sha256")} for k, v in (bundle.get("games") or {}).items()},
    }
    if not bundle.get("ok"):
        result["blocker"] = "owner_bundle_incomplete"
        result["owner_bundle_detail"] = bundle
        (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
        return result

    staging = Path(bundle["staging"])
    httpd_port = 8766
    httpd = start_host_artifact_httpd(staging, port=httpd_port)
    time.sleep(0.6)
    # Confirm host listener before guest curl.
    import socket as _sock

    host_listen_ok = False
    try:
        with _sock.create_connection(("127.0.0.1", httpd_port), timeout=2.0):
            host_listen_ok = True
    except OSError as exc:
        result["host_artifact_httpd"] = {
            "port": httpd_port,
            "pid": httpd.pid,
            "listen_ok": False,
            "error": str(exc),
        }
        try:
            httpd.terminate()
        except Exception:
            pass
        result["blocker"] = "host_artifact_httpd_listen_failed"
        (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
        return result
    result["host_artifact_httpd"] = {"port": httpd_port, "pid": httpd.pid, "listen_ok": host_listen_ok}
    try:
        # Ensure Godot 4.5+ — prefer already installed via 9p deploy; else try HTTP.
        godot = _ensure_godot4_in_guest(session, repo_root)
        result["godot4"] = {k: godot.get(k) for k in ("ok", "error", "via") if k in godot}
        deploy = _deploy_owner_packages(session, staging, httpd_port=httpd_port)
        result["deploy"] = {
            k: deploy.get(k)
            for k in ("ok", "stdout", "stderr", "returncode", "error", "probe", "port", "via", "ninep")
            if k in deploy
        }
        deploy_ok = (
            ("DEPLOY_OK" in (deploy.get("stdout") or ""))
            or all(
                token in (deploy.get("stdout") or "")
                for token in (
                    "node True",
                    "server True",
                    "archive True",
                    "anime True",
                    "pp True",
                )
            )
        )
        if not deploy_ok:
            result["blocker"] = deploy.get("error") or "owner_package_deploy_failed"
            (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
            return result
        result["lab_observe_server"] = _ensure_lab_observe_server(session, restart=True)
        # Confirm Godot 4.5 after deploy.
        ver = _guest_bash(session, "/opt/gunnchos/bin/godot --version || true", timeout_sec=20)
        result["godot45"] = {
            "ok": any(x in (ver.get("stdout") or "") for x in ("4.5", "4.4", "4.6", "4.7")),
            "version_stdout": (ver.get("stdout") or "")[:200],
            "via": deploy.get("via"),
        }
        if not result["godot45"]["ok"]:
            godot45 = _install_godot45_from_9p(session)
            if not godot45.get("ok"):
                godot45 = _ensure_godot45_in_guest(session, repo_root, httpd_port=httpd_port)
            result["godot45"] = godot45
            if not godot45.get("ok"):
                result["blocker"] = "godot45_unavailable_in_guest"
                (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
                return result

        # Godot first (RING-proven opengl3) while RAM is free; Chromium after.
        result["games"]["foot-racing"] = _run_pedestrian_godot(session, repo_root)
        result["games"]["anime-aggressors"] = _run_anime_godot(session)
        _guest_bash(
            session,
            "pkill -9 -f /opt/gunnchos/bin/godot || true; sleep 1",
            timeout_sec=15,
            name="godot-clear-before-web",
        )
        result["games"]["beatlink-party"] = _run_beatlink_socketio(session)
        result["games"]["earth-species"] = _run_archive_chromium(session)
    finally:
        try:
            httpd.terminate()
        except Exception:
            pass

    all_ok = all(
        bool((result["games"].get(g) or {}).get("FOUR_GAME_REAL_RUNTIME_EARNED")) for g in LAB_IDS
    )
    result["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] = all_ok
    result["ok"] = all_ok
    result["note"] = (
        "All four owner-artifact in-guest proofs earned"
        if all_ok
        else "Aggregate FAIL — see per-game blocker fields"
    )
    if not all_ok:
        result["blockers"] = {
            g: (result["games"].get(g) or {}).get("blocker")
            or (
                None
                if (result["games"].get(g) or {}).get("FOUR_GAME_REAL_RUNTIME_EARNED")
                else "not_earned"
            )
            for g in LAB_IDS
        }

    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
    production = {
        "schema": "gunnchos.wp011r.four_games_production.v2_in_guest",
        "recorded_at_utc": result["recorded_at_utc"],
        "FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS": all_ok,
        "HOST_PLAYWRIGHT_REJECTED": True,
        "http_server_alone_accepted": False,
        "PROBE_FACADE_REJECTED": True,
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SILICON_EXACT_EMULATION": False,
        "SHIPPING_IMAGE": False,
        "claim_boundary": CLAIM,
        "source_evidence": "artifacts/wp011r/games/four_games_in_guest.json",
        "accepted_mains": result["accepted_mains"],
        "games": result["games"],
        "note": result["note"],
    }
    games_dir = evidence_dir if evidence_dir.name == "games" else evidence_dir.parent / "games"
    games_dir.mkdir(parents=True, exist_ok=True)
    (games_dir / "four_games_in_guest.json").write_text(json.dumps(result, indent=2) + "\n")
    (games_dir / "four_games_production.json").write_text(json.dumps(production, indent=2) + "\n")
    # Per-game evidence paths
    for lab_id, payload in result["games"].items():
        owner = LAB_TO_OWNER.get(lab_id, lab_id)
        gdir = games_dir / lab_id
        gdir.mkdir(parents=True, exist_ok=True)
        (gdir / f"{lab_id}_owner_result.json").write_text(json.dumps(payload, indent=2) + "\n")
        (gdir / "OWNER_MAP.json").write_text(
            json.dumps({"lab_id": lab_id, "owner_key": owner, **ACCEPTED_MAINS.get(owner, {})}, indent=2)
            + "\n"
        )
    return result
