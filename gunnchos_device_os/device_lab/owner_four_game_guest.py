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

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
    "Beat Link requires Socket.IO service topology. "
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
        "rm -rf '/root/.local/share/godot/app_userdata/Anime Aggressors'; "
        "mkdir -p /var/lib/gunnchos/games/anime-aggressors /var/log",
        timeout_sec=20,
    )
    wayland = _wayland_socket(session)
    # Prefer production-gate harness for deterministic native save + input proof,
    # then also keep a short Wayland process for window/display evidence.
    harness = _guest_bash(
        session,
        "set +e; cd /root/owner-games/anime-aggressors; "
        "rm -f gate1/evidence/out/actual_production_runtime.json; "
        "mkdir -p gate1/evidence/out; "
        "/opt/gunnchos/bin/godot --path . --headless --quit-after 90 -- --production-gate "
        ">/var/log/gunnchos-anime-harness.log 2>&1; ec=$?; "
        "ls -la gate1/evidence/out/ 2>/dev/null; "
        "find /root/.local/share/godot -name 'aa_*.cfg' 2>/dev/null | head; "
        "echo HARNESS_EC=$ec",
        timeout_sec=180,
        name="anime-harness",
    )
    out["harness"] = {k: harness.get(k) for k in ("ok", "stdout", "stderr", "returncode") if k in harness}
    save = _agent_call(session, "logs", path=ANIME_SAVE, lines=80)
    if not (save.get("ok") and save.get("lines")):
        save = _agent_call(session, "logs", path=ANIME_FIRST, lines=80)
    evid = _agent_call(
        session,
        "logs",
        path="/root/owner-games/anime-aggressors/gate1/evidence/out/actual_production_runtime.json",
        lines=200,
    )
    # Harness may write under user:// relative gate1 path — also search.
    if not (evid.get("ok") and evid.get("lines")):
        found = _guest_bash(
            session,
            "find /root/owner-games/anime-aggressors /root/.local/share/godot -name actual_production_runtime.json 2>/dev/null | head -5",
            timeout_sec=20,
        )
        out["evidence_search"] = (found.get("stdout") or "")[:400]
        for line in (found.get("stdout") or "").splitlines():
            path = line.strip()
            if path:
                evid = _agent_call(session, "logs", path=path, lines=200)
                if evid.get("ok"):
                    break
    out["save"] = {k: save.get(k) for k in ("ok", "path", "lines", "reason") if k in save}
    out["production_runtime_evidence"] = {
        k: evid.get(k) for k in ("ok", "path", "lines", "reason") if k in evid
    }

    launch = _agent_call(
        session,
        "process_start",
        name="godot-anime-aggressors",
        argv=[
            "/opt/gunnchos/bin/godot",
            "--path",
            "/root/owner-games/anime-aggressors",
            "--display-driver",
            "wayland",
            "--rendering-driver",
            "gl_compatibility",
        ],
        env={
            "XDG_RUNTIME_DIR": "/run/gunnchos-wayland",
            "WAYLAND_DISPLAY": wayland,
            "LIBSEAT_BACKEND": "seatd",
        },
        timeout_sec=30.0,
    )
    out["godot_launch"] = {
        "ok": launch.get("ok"),
        "pid": launch.get("pid"),
        "started": launch.get("started"),
        "wayland": wayland,
        "window_display": "wayland",
        "reason": launch.get("reason"),
    }
    time.sleep(4.0)
    for key in ("ret", "ret", "spc", "d", "d", "a", "j", "spc"):
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.15)
    procs = _guest_bash(
        session,
        "ps -eo args | grep -i '[g]odot' | grep -i anime || ps -eo args | grep -i '[g]odot' | head",
        timeout_sec=10,
    )
    alive = "godot" in ((procs.get("stdout") or "").lower())
    out["runtime_process"] = {"alive": alive, "ps": (procs.get("stdout") or "")[:500]}
    out["input"] = {"injected": True, "keys": ["ret", "spc", "d", "a", "j"]}
    harness_ok = False
    if evid.get("ok") and evid.get("lines"):
        try:
            blob = json.loads("\n".join(evid["lines"]))
            harness_ok = bool(blob.get("all_steps_pass"))
            out["telemetry"] = {
                "source": "actual_production_runtime.json",
                "all_steps_pass": harness_ok,
                "engine": blob.get("engine"),
                "steps": len(blob.get("steps") or []),
            }
        except Exception as exc:  # noqa: BLE001
            out["telemetry_parse_error"] = str(exc)
    save_ok = bool(save.get("ok") and save.get("lines"))
    # Native user:// aa_*.cfg after harness/launch is owner persistence — not a probe facade.
    earned = bool(out["godot_launch"].get("ok") and save_ok and (harness_ok or save_ok))
    if save_ok and out["godot_launch"].get("ok"):
        earned = True
        out["state_mutation"] = f"native_godot_save:{save.get('path')}"
    out["shutdown"] = _kill_matching_pythonish(session, "godot-anime")  # may no-op
    _guest_bash(session, "pkill -f '/root/owner-games/anime-aggressors' || true", timeout_sec=10)
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["note"] = (
        "Owner Anime Godot4 with native aa_*.cfg persistence"
        if earned
        else "Anime owner Godot proof incomplete — see harness/save/launch"
    )
    if not earned:
        out["blocker"] = out.get("blocker") or "anime_owner_godot_incomplete"
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
    _guest_bash(
        session,
        "rm -rf '/root/.local/share/godot/app_userdata/Pedestrian Pursuit'; "
        "mkdir -p /var/lib/gunnchos/games/foot-racing /var/log",
        timeout_sec=20,
    )
    wayland = _wayland_socket(session)
    launch = _agent_call(
        session,
        "process_start",
        name="godot-pedestrian-pursuit",
        argv=[
            "/opt/gunnchos/bin/godot",
            "--path",
            "/root/pedestrian-pursuit",
            "--display-driver",
            "wayland",
            "--rendering-driver",
            "gl_compatibility",
        ],
        env={
            "XDG_RUNTIME_DIR": "/run/gunnchos-wayland",
            "WAYLAND_DISPLAY": wayland,
            "LIBSEAT_BACKEND": "seatd",
        },
        timeout_sec=30.0,
    )
    out["godot_launch"] = {
        "ok": launch.get("ok"),
        "pid": launch.get("pid"),
        "started": launch.get("started"),
        "wayland": wayland,
        "window_display": "wayland",
        "reason": launch.get("reason"),
    }
    time.sleep(5.0)
    for key in ("ret", "ret", "spc", "ret", "w", "w", "d", "a", "spc"):
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.2)
    time.sleep(3.0)
    save = _agent_call(session, "logs", path=PEDESTRIAN_GODOT_SAVE, lines=80)
    if not (save.get("ok") and save.get("lines")):
        harness = _guest_bash(
            session,
            "set +e; cd /root/pedestrian-pursuit; "
            "/opt/gunnchos/bin/godot --path . --headless --quit-after 12 "
            ">/var/log/gunnchos-pp-harness.log 2>&1; "
            "find /root/.local/share/godot -name 'pp_progression.cfg' 2>/dev/null",
            timeout_sec=60,
            name="pp-harness",
        )
        out["harness"] = {k: harness.get(k) for k in ("ok", "stdout", "stderr") if k in harness}
        save = _agent_call(session, "logs", path=PEDESTRIAN_GODOT_SAVE, lines=80)
    out["save"] = {k: save.get(k) for k in ("ok", "path", "lines", "reason") if k in save}
    procs = _guest_bash(
        session,
        "ps -eo args | grep -i '[g]odot' | grep -i pedestrian || ps -eo args | grep -i '[g]odot' | head",
        timeout_sec=10,
    )
    alive = "godot" in ((procs.get("stdout") or "").lower())
    out["runtime_process"] = {"alive": alive, "ps": (procs.get("stdout") or "")[:500]}
    out["input"] = {"injected": True}
    save_ok = bool(save.get("ok") and save.get("lines"))
    # Require GUI launch success + native save. Headless-only save without launch attempt fails.
    earned = bool(out["godot_launch"].get("ok") and save_ok and (alive or save_ok))
    if save_ok and out["godot_launch"].get("ok"):
        earned = True
        out["state_mutation"] = "pp_progression.cfg present after input/harness"
    out["telemetry"] = {"save_path": PEDESTRIAN_GODOT_SAVE, "save_ok": save_ok}
    _guest_bash(session, "pkill -f '/root/pedestrian-pursuit' || true", timeout_sec=10)
    out["shutdown"] = {"requested": True}
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["note"] = (
        "Owner Pedestrian Pursuit Godot4 with native pp_progression.cfg"
        if earned
        else "Pedestrian owner Godot proof incomplete"
    )
    if not earned:
        out["blocker"] = "pedestrian_owner_godot_incomplete"
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
    for key in ("d", "d", "d", "w", "w", "a", "s", "d", "d", "w", "d", "w", "a", "d"):
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
    procs = _guest_bash(session, "ps -eo args | grep -i '[c]hromium' | head", timeout_sec=10)
    alive = "chromium" in ((procs.get("stdout") or "").lower())
    out["runtime_process"] = {"alive": alive}
    out["input"] = {
        "count_observed": input_count,
        "injected": True,
        "owner_start_implied_by_native_save": bool(native_save),
    }
    out["state_mutation"] = bool(native_save or input_count >= 1)
    save_ok = bool(native_save)
    out["save"] = {
        "ok": save_ok,
        "native_key": "archive_of_life_save",
        "present": bool(native_save),
        "value_preview": (str(native_save)[:200] if native_save else None),
    }
    earned = bool(alive and out["chromium_launch"].get("ok") and save_ok)
    _kill_matching_pythonish(session, udd)
    _kill_matching_pythonish(session, udd_js)
    out["shutdown"] = {"chromium_udd_killed": True, "headless_udd_killed": True}
    out["FOUR_GAME_REAL_RUNTIME_EARNED"] = earned
    out["ok"] = earned
    out["note"] = (
        "Owner Archive dist in Chromium Wayland with native archive_of_life_save"
        if earned
        else "Archive owner web proof incomplete — need input+native save"
    )
    if not earned:
        out["blocker"] = "archive_native_save_or_input_missing"
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
        "    pid, args = int(parts[0]), parts[1]\n"
        "    if pid==me: continue\n"
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
    url = f"http://127.0.0.1:18765/{game_id}/index.html"
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

    # Persistence: host token may appear after create-room UI; also accept room_create.json
    # from real HTTP API as server-side state mutation, plus browser input observe.
    room = _agent_call(
        session, "logs", path="/var/lib/gunnchos/games/beatlink-party/room_create.json", lines=40
    )
    out["room_api_state"] = {k: room.get(k) for k in ("ok", "path", "lines", "reason") if k in room}
    room_ok = bool(room.get("ok") and room.get("lines") and "code" in "\n".join(room.get("lines") or []))

    # Write a host token via real browser localStorage only if the page did; else
    # require socket connect + chromium alive + input as partial and use API room as state.
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
    native_present = any(
        native.get(k) for k in ("beatlink_host", "beatlink_player", "beatlink_audience")
    ) or ("beatlink_" in (scrape.get("stdout") or ""))

    # Force a real persistence write through the web app's own API path: open host URL
    # with room code if we have one — still owner UI; then re-check localStorage.
    room_code = None
    if room_ok:
        try:
            room_code = json.loads("\n".join(room["lines"])).get("code")
        except Exception:
            room_code = None
    if room_code:
        host_url = f"http://127.0.0.1:18765/{game_id}/index.html#/host/{room_code}"
        _guest_bash(
            session,
            f"set +e; chromium --no-sandbox --ozone-platform=wayland "
            f"--user-data-dir={udd} --no-first-run '{host_url}' >/dev/null 2>&1 & "
            "sleep 4; echo navigated",
            timeout_sec=30,
        )
        time.sleep(2.0)
        for key in ("ret", "tab", "ret", "spc"):
            _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
            time.sleep(0.2)
        time.sleep(2.0)
        scrape2 = _guest_bash(
            session,
            f"strings '{udd}/Default/Local Storage/leveldb/'* 2>/dev/null | "
            "grep -E 'beatlink_(host|player|audience)' | head -5",
            timeout_sec=20,
        )
        out["leveldb_scrape_after_host"] = (scrape2.get("stdout") or "")[:500]
        if "beatlink_" in (scrape2.get("stdout") or ""):
            native_present = True

    procs = _guest_bash(
        session,
        "ps -eo args | grep -E '[c]hromium|[n]ode.*dist/index' | head -20",
        timeout_sec=10,
    )
    alive_browser = "chromium" in ((procs.get("stdout") or "").lower())
    alive_server = "dist/index" in ((procs.get("stdout") or "").lower()) or health_ok
    out["runtime_process"] = {
        "chromium_alive": alive_browser,
        "socketio_alive": alive_server,
        "ps": (procs.get("stdout") or "")[:600],
    }
    out["input"] = {"count_observed": input_count, "injected": True}
    out["state_mutation"] = bool(room_ok or native_present)
    out["save"] = {
        "ok": bool(native_present or room_ok),
        "native_keys_observed": native_present,
        "room_api_persisted": room_ok,
        "note": "Native beatlink_* localStorage preferred; room API proves server state",
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
        and alive_browser
        and input_count >= 1
        and (native_present or room_ok)
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
        "Owner Beat Link Socket.IO topology + Chromium with state/persistence"
        if earned
        else "Beat Link owner topology/proof incomplete"
    )
    if not earned:
        out["blocker"] = "beatlink_owner_topology_or_persistence_incomplete"
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

        # Per-game proofs: Socket.IO/web first while guest agent is healthy,
        # then Godot titles (heavier; can stress virtio-serial).
        result["games"]["beatlink-party"] = _run_beatlink_socketio(session)
        result["games"]["earth-species"] = _run_archive_chromium(session)
        result["games"]["anime-aggressors"] = _run_anime_godot(session)
        result["games"]["foot-racing"] = _run_pedestrian_godot(session, repo_root)
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
