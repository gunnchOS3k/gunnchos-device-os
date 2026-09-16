"""17G.5 — Real WAIKE Tauri GUI/WebView + real Hub journey on Interactive Guest.

Zero WAIKE source changes. Prefer FAIL over false PASS.
Forbidden PASS surrogates: mock LMS, static HTML, API-only, headless ack-only, Xvfb-as-primary.
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.interactive_guest_proofs import (
    _agent_call,
    _wait_agent,
    boot_interactive_guest,
)
from gunnchos_device_os.device_lab.owner_four_game_artifacts import (
    start_host_artifact_httpd,
    wait_host_artifact_httpd,
)
from gunnchos_device_os.device_lab.owner_waike_artifacts import (
    ACCEPTED_WAIKE_LP_SHA,
    APP_VERSION,
    BUNDLE_ID,
    MAIN_AARCH64_GLIBC236_SHA256,
    PIN_MANIFEST_SHA256,
    resolve_waike_lp_checkout,
    stage_owner_waike_bundle,
)
from gunnchos_device_os.device_lab.owner_waike_guest import (
    CLAIM,
    ensure_tauri_aarch64_runtime,
    fetch_bundle_into_guest,
    guest_device_os_launch,
    maybe_enable_qemu_wrapper,
    probe_binary_exec,
    role_boundary_probe,
    _b64_put,
    _guest_sh,
    _utc,
)
from gunnchos_device_os.device_lab.runtime_target_preflight import (
    PREFERRED_LABEL,
    run_runtime_target_preflight,
)

HUB_PORT = 8787
HUB_GUEST_URL = f"http://10.0.2.2:{HUB_PORT}"


def write_capability_map(repo_root: Path, out_dir: Path) -> dict[str, Any]:
    """Section 1: diagnose accepted-main GUI/Hub capability (inspect only)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    lp = resolve_waike_lp_checkout(repo_root)
    sha = subprocess.check_output(["git", "-C", str(lp), "rev-parse", "HEAD"], text=True).strip()
    tauri_conf = json.loads(
        (lp / "apps/client/src-tauri/tauri.conf.json").read_text(encoding="utf-8")
    )
    resolve_hub = (lp / "apps/client/src/lib/hub/resolveHub.ts").read_text(encoding="utf-8")
    offline_rs = (lp / "apps/client/src-tauri/src/offline.rs").read_text(encoding="utf-8")
    lib_rs = (lp / "apps/client/src-tauri/src/lib.rs").read_text(encoding="utf-8")
    deviceos_launch = (lp / "apps/client/src-tauri/src/deviceos_launch.rs").read_text(
        encoding="utf-8"
    )
    app_tsx = (lp / "apps/client/src/App.tsx").read_text(encoding="utf-8")

    has_runtime_hub_override = (
        "WAIKE_HUB_URL" in resolve_hub
        or "hub_url" in resolve_hub
        or "context.hub_url" in app_tsx
        or "launchContext" in resolve_hub
    )
    headless_skips_webview = "ci_headless_ui" in lib_rs and "return;" in lib_rs
    native_offline = "sync_outbox" in offline_rs and "EncryptedDb" in offline_rs
    product_name = (tauri_conf.get("productName") or "")
    window_title = ((tauri_conf.get("app") or {}).get("windows") or [{}])[0].get("title")

    doc = {
        "schema": "gunnchos.device_lab.waike_gui_hub_capability_map.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5",
        "accepted_main_sha": sha,
        "expected_accepted_main_sha": ACCEPTED_WAIKE_LP_SHA,
        "sha_match": sha == ACCEPTED_WAIKE_LP_SHA,
        "zero_waike_source_changes": True,
        "surfaces_inspected": {
            "tauri_conf": str(lp / "apps/client/src-tauri/tauri.conf.json"),
            "App.tsx": str(lp / "apps/client/src/App.tsx"),
            "assessment": str(lp / "apps/client/src/components/assessment"),
            "hub_client": str(lp / "apps/client/src/lib/hub"),
            "offline_ts": str(lp / "apps/client/src/lib/offline"),
            "offline_rs": str(lp / "apps/client/src-tauri/src/offline.rs"),
            "services_hub": str(lp / "services/hub"),
            "migrations": str(lp / "services/hub/app/migrations"),
            "run_test_hub": str(lp / "scripts/run_test_hub.py"),
            "deviceos_real_tauri_e2e": str(lp / "scripts/deviceos_real_tauri_e2e.py"),
            "learner_instructor_offline_tests": [
                "tests/gate_a/test_learner_e2e.py",
                "tests/gate_a/test_instructor_e2e.py",
                "tests/gate_a/test_offline_restart.py",
                "tests/gate_d/test_learner_journey.py",
                "tests/gate_d/test_instructor_journey.py",
                "tests/gate_d/test_offline_cross_device.py",
            ],
        },
        "gui": {
            "product_name": product_name,
            "window_title": window_title,
            "tauri_v2": True,
            "webview_required_for_learner_depth": True,
            "headless_env_skips_webview": bool(
                "WAIKE_CI_HEADLESS_UI" in deviceos_launch and headless_skips_webview
            ),
            "headless_ack_only_insufficient_for_pass": True,
        },
        "hub": {
            "real_hub_service_present": (lp / "services/hub/app/main.py").is_file(),
            "run_test_hub_loopback_only": True,
            "mockHub_exists_for_tests_only": (lp / "apps/client/src/lib/hub/mockHub.ts").is_file(),
            "resolveHub_fail_closed_production": "School Hub not configured" in resolve_hub
            or "unavailable" in resolve_hub,
            "vite_hub_url_compile_time_only": "VITE_HUB_URL" in resolve_hub,
            "runtime_hub_url_override_from_deviceos_launch_context": has_runtime_hub_override,
            "production_binary_binds_real_hub_without_rebuild": has_runtime_hub_override,
        },
        "offline": {
            "native_encrypted_outbox": native_offline,
            "ack_requires_receipt": "persist_sync_ack" in offline_rs,
            "client_cannot_set_acknowledged_directly": "CLIENT_SETTABLE_STATUSES" in offline_rs,
        },
        "device_lab_implications": {
            "gui_window_launch_possible_without_product_change": True,
            "real_hub_process_can_run_as_sidecar_or_in_guest": True,
            "client_bind_to_real_hub_requires_vite_hub_url_or_runtime_override": True,
            "accepted_main_defect_if_runtime_override_absent": not has_runtime_hub_override,
            "recommended_smallest_product_fix": (
                "Honor Device OS launch-context hub_url / WAIKE_HUB_URL in resolveHub "
                "(or equivalent runtime config) so native builds can bind a real Hub "
                "without baking VITE_HUB_URL at compile time. Keep fail-closed; never "
                "auto-mock in production."
                if not has_runtime_hub_override
                else "NONE"
            ),
        },
        "forbidden_pass_surrogates": [
            "mockHub",
            "static_html",
            "api_only",
            "headless_ack_only",
            "xvfb_as_primary_when_weston_exists",
            "js_injection_as_learner_activity",
            "direct_db_edit_as_learner_activity",
        ],
    }
    path = out_dir / "WAIKE_GUI_HUB_CAPABILITY_MAP.json"
    path.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return doc


def _wayland_env_probe(session: Any) -> dict[str, Any]:
    r = _guest_sh(
        session,
        "set +e; "
        "echo XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}; "
        "ls /run/gunnchos-wayland/wayland-* 2>/dev/null | grep -v lock | head -3; "
        "pgrep -a weston | head -3; "
        "systemctl is-active gunnchos-weston.service 2>/dev/null || true; "
        "command -v weston-info || true; "
        "command -v wayland-info || true; "
        "command -v atspi-bus-launcher || true; "
        "echo PROBE_GUI_ENV_DONE",
        timeout_sec=30.0,
    )
    out = (r.get("stdout") or "") + (r.get("stderr") or "")
    sock = ""
    for line in out.splitlines():
        if "wayland-" in line and "lock" not in line:
            sock = Path(line.strip()).name
            break
    return {
        "ok": "PROBE_GUI_ENV_DONE" in out and ("weston" in out.lower() or "wayland-" in out),
        "wayland_display": sock or "wayland-0",
        "stdout_tail": out[-1500:],
    }


def prove_gui_session(session: Any, out_dir: Path) -> dict[str, Any]:
    """Reuse real Interactive Guest compositor (not Xvfb-primary)."""
    comp = _agent_call(session, "compositor_info", timeout_sec=20.0)
    wayland = _wayland_env_probe(session)
    # Prefer weston; record Xvfb presence but refuse as primary PASS surface.
    xvfb = _guest_sh(session, "pgrep -a Xvfb || true; command -v Xvfb || true", timeout_sec=15.0)
    xvfb_out = (xvfb.get("stdout") or "") + (xvfb.get("stderr") or "")
    doc = {
        "schema": "gunnchos.device_lab.waike_gui_session_provenance.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5",
        "compositor_info": comp,
        "wayland_probe": wayland,
        "xvfb_present": "Xvfb" in xvfb_out,
        "xvfb_used_as_primary_pass_surface": False,
        "primary_display": "interactive_guest_weston_wayland"
        if wayland.get("ok")
        else "compositor_missing_or_not_ready",
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SILICON_EXACT_EMULATION": False,
        "ok": bool(wayland.get("ok") or (comp.get("ok") and comp.get("compositor"))),
    }
    (out_dir / "WAIKE_GUI_SESSION_PROVENANCE.json").write_text(
        json.dumps(doc, indent=2, default=str) + "\n", encoding="utf-8"
    )
    return doc


def start_host_real_hub(lp_root: Path, ops_root: Path, work: Path) -> dict[str, Any]:
    """Real accepted-main Hub as guest-reachable host sidecar (no mockHub)."""
    work.mkdir(parents=True, exist_ok=True)
    venv = work / "hub_venv"
    db = work / "hub_device_lab.sqlite"
    log = work / "hub_sidecar.log"
    if db.exists():
        db.unlink()
    py = shutil.which("python3") or "python3"
    pip = venv / "bin" / "pip"
    hub_dir = lp_root / "services" / "hub"
    need_install = not (venv / "bin" / "python").is_file()
    if need_install:
        create = subprocess.run(
            [py, "-m", "venv", str(venv)],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if create.returncode != 0:
            return {
                "ok": False,
                "error": "venv_create_failed",
                "stderr_tail": (create.stderr or "")[-800:],
            }
    # Always ensure editable hub + Gate D deps (idempotent / fast if cached).
    install = subprocess.run(
        [
            str(pip),
            "install",
            "-q",
            "-e",
            str(hub_dir),
            "cryptography",
            "PyNaCl",
            "PyJWT",
            "httpx",
            "jsonschema",
        ],
        capture_output=True,
        text=True,
        timeout=420,
    )
    if install.returncode != 0:
        return {
            "ok": False,
            "error": "hub_pip_install_failed",
            "stderr_tail": (install.stderr or "")[-1200:],
        }
    env = os.environ.copy()
    env["WAIKE_ROOT"] = str(ops_root)
    env["WAIKE_SEED_TEST_FIXTURES"] = "1"
    env["WAIKE_ENV"] = "development"
    env["WAIKE_HUB_DB"] = str(db)
    # Bind all interfaces so QEMU guest can reach host via 10.0.2.2.
    # run_test_hub refuses non-loopback; use uvicorn directly against create_app.
    boot = f"""
import os, sys
from pathlib import Path
sys.path.insert(0, {str(hub_dir)!r})
os.environ['WAIKE_ROOT'] = {str(ops_root)!r}
os.environ['WAIKE_SEED_TEST_FIXTURES'] = '1'
os.environ['WAIKE_ENV'] = 'development'
import uvicorn
from app.main import HubConfig, create_app
app = create_app(
    HubConfig(production_auth_enabled=True, fixture_auth_enabled=False),
    db_path=Path({str(db)!r}),
    seed=True,
)
uvicorn.run(app, host='0.0.0.0', port={HUB_PORT}, log_level='warning')
"""
    boot_py = work / "boot_real_hub.py"
    boot_py.write_text(boot, encoding="utf-8")
    logf = open(log, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [str(venv / "bin" / "python"), str(boot_py)],
        stdout=logf,
        stderr=subprocess.STDOUT,
        env=env,
        cwd=str(hub_dir),
    )
    ready = False
    last_err = None
    for _ in range(60):
        try:
            with socket.create_connection(("127.0.0.1", HUB_PORT), timeout=1.0):
                ready = True
                break
        except OSError as exc:
            last_err = str(exc)
            if proc.poll() is not None:
                break
            time.sleep(0.5)
    health = None
    if ready:
        try:
            import urllib.request

            with urllib.request.urlopen(f"http://127.0.0.1:{HUB_PORT}/healthz", timeout=5) as resp:
                health = {"status": resp.status, "body": resp.read()[:400].decode("utf-8", "replace")}
        except Exception as exc:  # noqa: BLE001
            health = {"probe_error": str(exc)}
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{HUB_PORT}/version", timeout=5) as resp:
                    health = {"status": resp.status, "path": "/version", "body": resp.read()[:200].decode("utf-8", "replace")}
            except Exception as exc2:  # noqa: BLE001
                health = {"probe_error": str(exc), "version_error": str(exc2)}
    return {
        "ok": ready and proc.poll() is None,
        "mock": False,
        "stub": False,
        "static_fixture": False,
        "pid": proc.pid,
        "port": HUB_PORT,
        "bind": "0.0.0.0",
        "guest_url": HUB_GUEST_URL,
        "db_path": str(db),
        "log_path": str(log),
        "source_sha": ACCEPTED_WAIKE_LP_SHA,
        "entrypoint": "services/hub app.main.create_app seed=True production_auth",
        "health": health,
        "last_err": last_err,
        "proc": proc,
        "log_handle": logf,
    }


def guest_gui_launch(
    session: Any,
    *,
    journey_tag: str = "A",
    platform_role: str = "learner",
    profile: str = "student",
    deep_link: str = "waike://learn/home",
    hub_url: str | None = None,
) -> dict[str, Any]:
    """Launch authentic Tauri WITHOUT headless; keep process alive beyond IPC ack."""
    install_root = "/var/lib/gunnchos/waike-learning-os"
    ipc_dir = f"/tmp/waike-los-gui-j{journey_tag}"
    # Explicitly unset headless; do not pass --ci-headless-ui.
    script = f"""
import json, os, sys, time, uuid, signal
from pathlib import Path

install_root = Path({install_root!r})
os.environ['LEARNING_OS_INSTALL_ROOT'] = str(install_root)
os.environ['LEARNING_OS_APP_VERSION'] = {APP_VERSION!r}
os.environ['LEARNING_OS_PLATFORM_SHA'] = {ACCEPTED_WAIKE_LP_SHA!r}
os.environ.pop('WAIKE_CI_HEADLESS_UI', None)
os.environ.pop('CI_HEADLESS_UI', None)
os.environ['LEARNING_OS_CLEANUP_AFTER_ACK'] = '0'
os.environ['WAIKE_DEV_DB_KEY'] = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
os.environ['HOME'] = '/root'
os.environ['XDG_DATA_HOME'] = '/var/lib/gunnchos/waike-userdata'
os.environ['XDG_RUNTIME_DIR'] = '/run/gunnchos-wayland'
# Prefer real Interactive Guest compositor (weston). X11/XWayland fallback only.
os.environ.setdefault('GDK_BACKEND', 'wayland')
os.environ.setdefault('WEBKIT_DISABLE_COMPOSITING_MODE', '1')
# Stage verify key
_xdg = Path(os.environ['XDG_DATA_HOME']) / 'waike-learning-os'
_xdg.mkdir(parents=True, exist_ok=True)
for _k in [
    install_root / 'contracts/fixtures/keys/TEST_ONLY_ed25519_public.key',
    install_root / 'xdg/waike-learning-os/TEST_ONLY_ed25519_public.key',
    Path('/mnt/gdlgames/contracts/fixtures/keys/TEST_ONLY_ed25519_public.key'),
]:
    if _k.is_file():
        (_xdg / 'TEST_ONLY_ed25519_public.key').write_bytes(_k.read_bytes())
        (install_root / 'contracts/fixtures/keys').mkdir(parents=True, exist_ok=True)
        dest = install_root / 'contracts/fixtures/keys/TEST_ONLY_ed25519_public.key'
        dest.write_bytes(_k.read_bytes())
        break
# Discover wayland socket
wl = 'wayland-0'
for p in sorted(Path('/run/gunnchos-wayland').glob('wayland-*')):
    if p.name.endswith('.lock'):
        continue
    wl = p.name
    break
os.environ['WAYLAND_DISPLAY'] = wl
hub_url = {hub_url!r}
if hub_url:
    # Env-only until accepted-main allowlists hub_url in Device OS launch context.
    # Putting hub_url in context currently NACKs: unknown_context_field:hub_url.
    os.environ['WAIKE_HUB_URL'] = hub_url
    os.environ['VITE_HUB_URL'] = hub_url  # no-op for baked binary; evidence only

exe = install_root / 'bin' / 'waike-learning-os'
ipc = Path({ipc_dir!r})
ipc.mkdir(parents=True, exist_ok=True)
req_id = str(uuid.uuid4())
req = {{
    'protocol': 'gunnchos.learning_os.ipc.v1',
    'message_type': 'launch_context',
    'request_id': req_id,
    'bundle_id': {BUNDLE_ID!r},
    'deep_link': {{
        'uri': {deep_link!r},
        'canonical': {deep_link!r},
        'valid': True,
        'kind': 'learn',
        'path': 'home',
    }},
    'context': {{
        'profile': {profile!r},
        'mode': 'School',
        'platform_role': {platform_role!r},
        'bundle_id': {BUNDLE_ID!r},
        # Do NOT include hub_url until product allowlists it (NACK otherwise).
    }},
}}
req_path = ipc / f'request-{{req_id}}.json'
req_path.write_text(json.dumps(req, indent=2, sort_keys=True) + '\\n')
env = os.environ.copy()
env['LEARNING_OS_IPC_DIR'] = str(ipc)
env['LEARNING_OS_REQUEST_ID'] = req_id
# CRITICAL: do not set headless
env.pop('WAIKE_CI_HEADLESS_UI', None)
env.pop('CI_HEADLESS_UI', None)
log_path = Path('/tmp/waike_gui_{journey_tag}.log')
logf = open(log_path, 'w')
import subprocess
proc = subprocess.Popen(
    [
        str(exe),
        '--bundle-id', {BUNDLE_ID!r},
        '--deep-link', {deep_link!r},
        '--ipc-dir', str(ipc),
        '--request-id', req_id,
    ],
    cwd=str(install_root),
    env=env,
    stdout=logf,
    stderr=subprocess.STDOUT,
    start_new_session=True,
)
deadline = time.time() + 45
ack = None
while time.time() < deadline:
    ack_path = ipc / f'ack-{{req_id}}.json'
    if ack_path.is_file():
        try:
            ack = json.loads(ack_path.read_text())
        except Exception as e:
            ack = {{'parse_error': repr(e)}}
        break
    if proc.poll() is not None and not ack_path.is_file():
        break
    time.sleep(0.25)
alive_after_ack = proc.poll() is None
time.sleep(3.0)
alive_after_3s = proc.poll() is None
# Window / process evidence
ps = subprocess.run(
    ['bash', '-lc', f'ps -o pid,etime,cmd -p {{proc.pid}} || true; '
     f'pgrep -a waike-learning || true; '
     'pgrep -a WebKit || true; pgrep -a webkit || true'],
    capture_output=True, text=True, timeout=15,
)
atspi = subprocess.run(
    ['bash', '-lc', r'''python3 - <<'PY'
import json
try:
 import gi
 gi.require_version("Atspi", "2.0")
 from gi.repository import Atspi
 Atspi.init()
 desk = Atspi.get_desktop(0)
 names=[]
 for i in range(desk.get_child_count()):
  c=desk.get_child_at_index(i)
  try: names.append(c.get_name() or "")
  except Exception: pass
 print("ATSPI_NAMES", json.dumps(names))
except Exception as e:
 print("ATSPI_ERR", e)
PY'''],
    capture_output=True, text=True, timeout=20,
)
# Keep PID file for later stop
Path('/tmp/waike_gui_{journey_tag}.pid').write_text(str(proc.pid))
result = {{
    'path': 'gui_direct_no_headless',
    'headless': False,
    'xvfb_primary': False,
    'process_started': proc.pid is not None,
    'pid': proc.pid,
    'returncode_immediate': proc.poll(),
    'acknowledged': bool(isinstance(ack, dict) and (
        ack.get('ok') is True or str(ack.get('message_type') or '').lower() in {{'ack','ok','launch_ack'}}
    )),
    'ack': ack,
    'alive_beyond_ipc_ack': alive_after_ack,
    'alive_after_3s': alive_after_3s,
    'ps_tail': ((ps.stdout or '') + (ps.stderr or ''))[-1200:],
    'atspi_tail': ((atspi.stdout or '') + (atspi.stderr or ''))[-1200:],
    'window_title_expected': 'WAIKE Learning OS',
    'wayland_display': env.get('WAYLAND_DISPLAY'),
    'hub_url_env_set': bool(hub_url),
    'hub_url': hub_url,
    'executable': str(exe),
    'fixture_rejected': 'fixtures/learning_os' not in str(exe),
    'journey_tag': {journey_tag!r},
    'platform_role': {platform_role!r},
    'deep_link': {deep_link!r},
    'log_path': str(log_path),
}}
# Title presence via AT-SPI names
names_blob = (atspi.stdout or '') + (atspi.stderr or '')
result['webview_or_window_title_observed'] = (
    'WAIKE Learning OS' in names_blob or 'waike-learning' in (ps.stdout or '').lower()
)
result['launched_gui'] = bool(
    result['process_started'] and result['alive_beyond_ipc_ack'] and result['fixture_rejected']
)
print(json.dumps(result))
"""
    put = _b64_put(session, f"/var/tmp/waike_gui_launch_{journey_tag}.py", script.encode())
    run = _guest_sh(
        session,
        f"python3 /var/tmp/waike_gui_launch_{journey_tag}.py",
        timeout_sec=120.0,
    )
    out = run.get("stdout") or ""
    payload: dict[str, Any] = {
        "ok": False,
        "raw_stdout_tail": out[-2500:],
        "put_ok": bool(put.get("ok") or "PUT_OK" in str(put.get("stdout") or "")),
        "stderr_tail": (run.get("stderr") or "")[-800:],
    }
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            break
    payload["journey_tag"] = journey_tag
    return payload


def stop_gui_pid(session: Any, journey_tag: str) -> dict[str, Any]:
    r = _guest_sh(
        session,
        f"PID=$(cat /tmp/waike_gui_{journey_tag}.pid 2>/dev/null || true); "
        f"if [ -n \"$PID\" ]; then kill \"$PID\" 2>/dev/null || true; sleep 1; "
        f"kill -9 \"$PID\" 2>/dev/null || true; fi; "
        f"pkill -f waike-learning-os 2>/dev/null || true; echo STOPPED",
        timeout_sec=30.0,
    )
    return {"ok": "STOPPED" in ((r.get("stdout") or "") + (r.get("stderr") or "")), "raw": r}


def probe_hub_bind_from_gui(
    session: Any, *, hub_url: str
) -> dict[str, Any]:
    """Prove whether baked client can bind real Hub (read-only verification)."""
    # Guest curl proves hub reachability; AT-SPI looks for hub:http vs hub-unavailable.
    reach = _guest_sh(
        session,
        f"curl -fsS -o /tmp/hub_probe.txt -w '%{{http_code}}' --connect-timeout 3 "
        f"--max-time 8 {hub_url}/healthz || curl -fsS -o /tmp/hub_probe.txt -w '%{{http_code}}' "
        f"--connect-timeout 3 --max-time 8 {hub_url}/version || echo FAIL; "
        f"echo; head -c 200 /tmp/hub_probe.txt 2>/dev/null || true",
        timeout_sec=30.0,
    )
    atspi = _guest_sh(
        session,
        "python3 - <<'PY'\n"
        "import json\n"
        "try:\n"
        " import gi\n"
        " gi.require_version('Atspi','2.0')\n"
        " from gi.repository import Atspi\n"
        " Atspi.init()\n"
        " desk=Atspi.get_desktop(0)\n"
        " texts=[]\n"
        " def walk(n, depth=0):\n"
        "  if depth>6: return\n"
        "  try:\n"
        "   name=n.get_name() or ''\n"
        "   if name: texts.append(name)\n"
        "   for i in range(n.get_child_count()):\n"
        "    walk(n.get_child_at_index(i), depth+1)\n"
        "  except Exception:\n"
        "   return\n"
        " walk(desk)\n"
        " blob=' | '.join(texts)\n"
        " print('HAS_HUB_HTTP', 'hub:http' in blob.lower())\n"
        " print('HAS_HUB_MOCK', 'hub:mock' in blob.lower())\n"
        " print('HAS_UNAVAILABLE', 'hub-unavailable' in blob.lower() or 'School Hub not configured' in blob)\n"
        " print('HAS_BRAND', 'WAIKE Learning OS' in blob)\n"
        " print('TEXT_SAMPLE', blob[:1500])\n"
        "except Exception as e:\n"
        " print('ATSPI_ERR', e)\n"
        "PY",
        timeout_sec=40.0,
    )
    aout = (atspi.get("stdout") or "") + (atspi.get("stderr") or "")
    rout = (reach.get("stdout") or "") + (reach.get("stderr") or "")
    reachable = any(
        token in rout for token in ("200", "openapi", "FastAPI", "Swagger", "<!DOCTYPE", "html")
    ) and "FAIL" not in rout
    return {
        "hub_reachable_from_guest": reachable,
        "reach_tail": rout[-800:],
        "atspi_tail": aout[-1500:],
        "client_hub_http_chip_observed": "HAS_HUB_HTTP True" in aout,
        "client_hub_mock_chip_observed": "HAS_HUB_MOCK True" in aout,
        "client_hub_unavailable_observed": "HAS_UNAVAILABLE True" in aout,
        "brand_observed": "HAS_BRAND True" in aout,
        "mock_mode_used": False,
        "note": (
            "Accepted-main resolves Hub via compile-time VITE_HUB_URL only; "
            "WAIKE_HUB_URL env / launch-context hub_url are not honored yet."
        ),
    }


def attempt_waike_gui_hub_journey(
    repo_root: Path,
    *,
    work: Path | None = None,
    memory_mb: int = 4096,
    boot_timeout_s: int = 240,
) -> dict[str, Any]:
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    evidence = repo_root / "artifacts/device_lab_current_pin/waike"
    gui_dir = evidence / "gui_journey"
    gui_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Any] = {
        "schema": "gunnchos.device_lab.waike_gui_hub_journey_attempt.v1",
        "started_at_utc": _utc(),
        "prompt": "17G.5",
        "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SHIPPING_IMAGE": False,
        "SILICON_EXACT_EMULATION": False,
        "claim_boundary": CLAIM,
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        "prefer_fail_over_false_pass": True,
        "gui_evidence_dir": str(gui_dir.relative_to(repo_root)),
    }

    cap = write_capability_map(repo_root, gui_dir)
    out["capability_map"] = {
        "path": "artifacts/device_lab_current_pin/waike/gui_journey/WAIKE_GUI_HUB_CAPABILITY_MAP.json",
        "accepted_main_defect_if_runtime_override_absent": cap["device_lab_implications"][
            "accepted_main_defect_if_runtime_override_absent"
        ],
    }

    staging = evidence / "owner_bundle_stage"
    if staging.exists():
        shutil.rmtree(staging)
    bundle = stage_owner_waike_bundle(repo_root, staging)
    out["bundle"] = {k: bundle.get(k) for k in ("ok", "pin_ok", "arch_gap", "binary") if k in bundle}
    if not bundle.get("ok") or not bundle.get("pin_ok"):
        out["blocker"] = bundle.get("error") or "owner_bundle_or_pin_failed"
        out["finished_at_utc"] = _utc()
        return out

    preflight_static = run_runtime_target_preflight(
        repo_root,
        session=None,
        label=PREFERRED_LABEL,
        out_path=evidence / "RUNTIME_TARGET_PREFLIGHT.json",
    )
    out["RUNTIME_TARGET_PREFLIGHT_PASS"] = bool(
        preflight_static.get("RUNTIME_TARGET_PREFLIGHT_PASS")
    )
    if not out["RUNTIME_TARGET_PREFLIGHT_PASS"]:
        out["blocker"] = "RUNTIME_TARGET_PREFLIGHT_FAIL"
        out["finished_at_utc"] = _utc()
        return out

    free_before = shutil.disk_usage("/").free / (1024**3)
    out["FREE_GIB_BEFORE_QEMU"] = round(free_before, 2)
    if free_before < 25:
        out["blocker"] = "WAIKE_STORAGE_BLOCKED_BEFORE_QEMU"
        out["finished_at_utc"] = _utc()
        return out

    # Real Hub sidecar (host) — before QEMU so guest can reach 10.0.2.2:8787
    lp = resolve_waike_lp_checkout(repo_root)
    ops = repo_root.parent / "waike-research-ops"
    if not ops.is_dir():
        ops = Path("/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/waike-research-ops")
    hub_work = gui_dir / "hub_sidecar"
    hub = start_host_real_hub(lp, ops, hub_work)
    hub_proc = hub.pop("proc", None)
    hub_log = hub.pop("log_handle", None)
    out["real_hub"] = {k: v for k, v in hub.items() if k not in ("proc", "log_handle")}
    (gui_dir / "WAIKE_REAL_HUB_PROVENANCE.json").write_text(
        json.dumps(out["real_hub"], indent=2, default=str) + "\n", encoding="utf-8"
    )
    if not hub.get("ok"):
        out["blocker"] = "real_hub_sidecar_failed_to_start"
        out["finished_at_utc"] = _utc()
        if hub_proc:
            hub_proc.terminate()
        if hub_log:
            hub_log.close()
        return out

    work = work or (repo_root / "artifacts/wp011r/interactive_guest_session_waike")
    if work.exists():
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging)
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

    httpd = start_host_artifact_httpd(
        staging, port=8767, log_path=evidence / "host_artifact_httpd_waike.log"
    )
    ok_listen, listen_err = wait_host_artifact_httpd(8767, proc=httpd)
    out["httpd"] = {"ok": ok_listen, "error": listen_err, "port": 8767}
    if not ok_listen:
        out["blocker"] = f"host_artifact_httpd:{listen_err}"
        out["finished_at_utc"] = _utc()
        if hub_proc:
            hub_proc.terminate()
        if hub_log:
            hub_log.close()
        return out

    try:
        boot = boot_interactive_guest(
            repo_root, work, dual=True, boot_timeout_s=boot_timeout_s, memory_mb=memory_mb
        )
        session = boot.pop("_session", None)
        out["boot"] = {
            "ok": boot.get("ok"),
            "error": boot.get("error"),
            "pid": boot.get("pid"),
            "arch": boot.get("arch"),
        }
        if not boot.get("ok") or session is None:
            out["blocker"] = boot.get("error") or "interactive_guest_boot_failed"
            out["finished_at_utc"] = _utc()
            return out
        if not _wait_agent(session, tries=40, sleep_s=1.0):
            out["blocker"] = "guest_agent_not_ready"
            out["finished_at_utc"] = _utc()
            return out
        ping = _agent_call(session, "ping", timeout_sec=8.0)
        out["ping"] = {k: ping.get(k) for k in ("pong", "transport", "ok")}
        if not ping.get("pong") or ping.get("transport") == "host_stub":
            out["blocker"] = "guest_agent_not_real_virtio_serial"
            out["finished_at_utc"] = _utc()
            return out

        tauri_rt = ensure_tauri_aarch64_runtime(session)
        out["tauri_aarch64_runtime"] = {
            "ok": tauri_rt.get("ok"),
            "packages_requested": tauri_rt.get("packages_requested"),
        }
        # Let dpkg/apt settle before follow-on installs + live preflight.
        time.sleep(5.0)
        # Additive AT-SPI tools for GUI driving (not Xvfb-primary).
        atspi_pkg = _guest_sh(
            session,
            "export DEBIAN_FRONTEND=noninteractive; "
            "for i in 1 2 3 4 5; do "
            "  if fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then sleep 2; else break; fi; "
            "done; "
            "apt-get install -y -qq python3-gi gir1.2-atspi-2.0 at-spi2-core 2>&1 | tail -15; "
            "echo ATSPI_SETUP_DONE",
            timeout_sec=300.0,
        )
        out["atspi_setup"] = {
            "ok": "ATSPI_SETUP_DONE" in ((atspi_pkg.get("stdout") or "") + (atspi_pkg.get("stderr") or "")),
            "tail": ((atspi_pkg.get("stdout") or "") + (atspi_pkg.get("stderr") or ""))[-500:],
        }
        time.sleep(2.0)

        preflight_live = run_runtime_target_preflight(
            repo_root,
            session=session,
            label=PREFERRED_LABEL,
            out_path=evidence / "RUNTIME_TARGET_PREFLIGHT.json",
        )
        if not preflight_live.get("RUNTIME_TARGET_PREFLIGHT_PASS") and tauri_rt.get("ok"):
            time.sleep(3.0)
            preflight_live = run_runtime_target_preflight(
                repo_root,
                session=session,
                label=PREFERRED_LABEL,
                out_path=evidence / "RUNTIME_TARGET_PREFLIGHT.json",
            )
        out["runtime_target_preflight"] = {
            "pass": bool(preflight_live.get("RUNTIME_TARGET_PREFLIGHT_PASS")),
            "blockers": preflight_live.get("blockers"),
            "guest_summary": preflight_live.get("guest_summary"),
        }
        out["RUNTIME_TARGET_PREFLIGHT_PASS"] = bool(
            preflight_live.get("RUNTIME_TARGET_PREFLIGHT_PASS")
        )
        if not out["RUNTIME_TARGET_PREFLIGHT_PASS"]:
            out["blocker"] = (
                "RUNTIME_TARGET_PREFLIGHT_FAIL:"
                + ",".join(preflight_live.get("blockers") or ["unknown"])
            )
            out["finished_at_utc"] = _utc()
            return out

        session_prov = prove_gui_session(session, gui_dir)
        out["gui_session"] = {
            "ok": session_prov.get("ok"),
            "primary_display": session_prov.get("primary_display"),
            "xvfb_used_as_primary_pass_surface": False,
        }
        if not session_prov.get("ok"):
            out["blocker"] = "interactive_guest_compositor_not_ready_for_gui"
            out["finished_at_utc"] = _utc()
            return out

        fetched = fetch_bundle_into_guest(session, port=8767)
        out["fetch"] = {"ok": fetched.get("ok"), "via": fetched.get("via")}
        if not fetched.get("ok"):
            out["blocker"] = "guest_fetch_owner_bundle_failed"
            out["finished_at_utc"] = _utc()
            return out

        arch_gap = bool(bundle.get("arch_gap"))
        wrapped = maybe_enable_qemu_wrapper(session, arch_gap)
        out["qemu_wrapper"] = wrapped
        if not arch_gap:
            native = _guest_sh(
                session,
                "ROOT=/var/lib/gunnchos/waike-learning-os/bin; "
                "cp -a $ROOT/waike-learning-os.real $ROOT/waike-learning-os 2>/dev/null || true; "
                "chmod +x $ROOT/waike-learning-os $ROOT/waike-learning-os.real; "
                "file $ROOT/waike-learning-os; echo NATIVE_ELF_READY",
                timeout_sec=30.0,
            )
            out["native_elf_ready"] = {
                "ok": "NATIVE_ELF_READY"
                in ((native.get("stdout") or "") + (native.get("stderr") or ""))
            }

        out["binary_probe"] = probe_binary_exec(session)
        sha = (bundle.get("binary") or {}).get("artifact_sha256")
        out["matches_main_aarch64_glibc236"] = sha == MAIN_AARCH64_GLIBC236_SHA256

        # Journey A — real GUI
        journey_a = guest_gui_launch(
            session, journey_tag="A", hub_url=HUB_GUEST_URL, platform_role="learner"
        )
        out["journey_a_gui"] = journey_a
        fb_a = _agent_call(session, "framebuffer_capture", timeout_sec=60.0)
        out["framebuffer_a"] = {
            "ok": bool(fb_a.get("ok")),
            "bytes": fb_a.get("bytes") or fb_a.get("size"),
            "path": fb_a.get("path"),
        }
        bind = probe_hub_bind_from_gui(session, hub_url=HUB_GUEST_URL)
        out["hub_bind"] = bind
        (gui_dir / "WAIKE_REAL_HUB_BINDING.json").write_text(
            json.dumps(
                {
                    "generated_at_utc": _utc(),
                    "real_hub_running": True,
                    "mock_mode_used": False,
                    "client_bound_http": bool(bind.get("client_hub_http_chip_observed")),
                    "client_mock_observed": bool(bind.get("client_hub_mock_chip_observed")),
                    "client_unavailable_observed": bool(
                        bind.get("client_hub_unavailable_observed")
                    ),
                    "hub_reachable_from_guest": bool(bind.get("hub_reachable_from_guest")),
                    "defect": (
                        "accepted_main_lacks_runtime_hub_url_override"
                        if not bind.get("client_hub_http_chip_observed")
                        else None
                    ),
                    "detail": bind,
                },
                indent=2,
                default=str,
            )
            + "\n",
            encoding="utf-8",
        )

        window_doc = {
            "generated_at_utc": _utc(),
            "window_alive_beyond_ipc_ack": bool(journey_a.get("alive_beyond_ipc_ack")),
            "alive_after_3s": bool(journey_a.get("alive_after_3s")),
            "title_expected": "WAIKE Learning OS",
            "title_or_brand_observed": bool(
                journey_a.get("webview_or_window_title_observed")
                or bind.get("brand_observed")
            ),
            "headless": False,
            "pid": journey_a.get("pid"),
            "framebuffer_ok": bool(fb_a.get("ok")),
            "launched_gui": bool(journey_a.get("launched_gui")),
        }
        (gui_dir / "WAIKE_GUI_WINDOW_ALIVE.json").write_text(
            json.dumps(window_doc, indent=2) + "\n", encoding="utf-8"
        )

        # Learner / instructor / offline / recovery — honest classification
        learner = {
            "launch_gui": bool(journey_a.get("launched_gui")),
            "identity_role_context": True,  # platform_role in launch context
            "hub_login": False,
            "course": False,
            "lesson": False,
            "interaction": False,
            "assessment_submission": False,
            "persist_readback": False,
            "complete": False,
            "blocker": (
                "client_cannot_bind_real_hub_without_runtime_hub_url_override;"
                "GUI may show hub-unavailable; forbid mockHub"
                if not bind.get("client_hub_http_chip_observed")
                else "gui_learner_depth_not_fully_exercised"
            ),
        }
        (gui_dir / "WAIKE_LEARNER_GUI_JOURNEY.json").write_text(
            json.dumps({"generated_at_utc": _utc(), **learner}, indent=2) + "\n",
            encoding="utf-8",
        )

        stop_gui_pid(session, "A")
        # Role boundary via Device OS platform_role (GUI relaunch)
        instructor = guest_gui_launch(
            session,
            journey_tag="I",
            hub_url=HUB_GUEST_URL,
            platform_role="instructor",
            profile="educator",
            deep_link="waike://learn/home",  # instruct kind not allowlisted on accepted-main
        )
        out["instructor_gui"] = {
            "launched_gui": instructor.get("launched_gui"),
            "platform_role": "instructor",
            "alive_beyond_ipc_ack": instructor.get("alive_beyond_ipc_ack"),
        }
        role_doc = {
            "generated_at_utc": _utc(),
            "ok": bool(journey_a.get("launched_gui") and instructor.get("launched_gui")),
            "learner_platform_role": "learner",
            "instructor_platform_role": "instructor",
            "frontend_only_role_fake": False,
            "hub_authorized_instructor_actions": False,
            "note": "Role boundary via Device OS launch context; hub-authorized staff actions blocked until client binds Hub.",
        }
        (gui_dir / "WAIKE_ROLE_BOUNDARY_GUI.json").write_text(
            json.dumps(role_doc, indent=2) + "\n", encoding="utf-8"
        )
        stop_gui_pid(session, "I")

        offline_doc = {
            "generated_at_utc": _utc(),
            "exercised": False,
            "native_architecture_present_on_accepted_main": True,
            "reason": "requires_http_hub_bound_client_for_lease_outbox_sync_ack",
        }
        (gui_dir / "WAIKE_OFFLINE_RECONNECT_GUI.json").write_text(
            json.dumps(offline_doc, indent=2) + "\n", encoding="utf-8"
        )
        recovery_doc = {
            "generated_at_utc": _utc(),
            "exercised": False,
            "reason": "controlled_failure_injection_requires_bound_hub_learner_surface",
        }
        (gui_dir / "WAIKE_CONTROLLED_FAILURE_RECOVERY.json").write_text(
            json.dumps(recovery_doc, indent=2) + "\n", encoding="utf-8"
        )

        # Journey B repeatability (GUI relaunch)
        journey_b = guest_gui_launch(
            session, journey_tag="B", hub_url=HUB_GUEST_URL, platform_role="learner"
        )
        out["journey_b_gui"] = {
            "launched_gui": journey_b.get("launched_gui"),
            "alive_beyond_ipc_ack": journey_b.get("alive_beyond_ipc_ack"),
        }
        stop_gui_pid(session, "B")
        repeat = {
            "generated_at_utc": _utc(),
            "journey_a": bool(journey_a.get("launched_gui")),
            "journey_b": bool(journey_b.get("launched_gui")),
            "pass": bool(journey_a.get("launched_gui") and journey_b.get("launched_gui")),
            "hub_bound_journeys": False,
        }
        (gui_dir / "WAIKE_JOURNEY_A_B_REPEATABILITY.json").write_text(
            json.dumps(repeat, indent=2) + "\n", encoding="utf-8"
        )

        # Also retain headless IPC contrast (not used for PASS)
        out["headless_contrast_a"] = guest_device_os_launch(session, journey_tag="H")
        out["role_boundary_headless_contrast"] = role_boundary_probe(session)

        product_defect = bool(
            cap["device_lab_implications"]["accepted_main_defect_if_runtime_override_absent"]
        ) and not bool(bind.get("client_hub_http_chip_observed"))

        defect = {
            "generated_at_utc": _utc(),
            "decision": "DRAFT_WAIKE_PRODUCT_PR"
            if product_defect
            else ("DEVICE_OS_FIX_ON_134" if not journey_a.get("launched_gui") else "NONE"),
            "accepted_main_defective_for_device_lab_hub_bind": product_defect,
            "reason": (
                "Accepted-main Tauri client binds Hub only via compile-time VITE_HUB_URL; "
                "production binary has none; no runtime override from Device OS launch "
                "context / WAIKE_HUB_URL. Real Hub sidecar runs and is guest-reachable, "
                "but GUI cannot authenticate/learn against it without a product fix. "
                "Zero WAIKE source changes in this Device OS attempt."
                if product_defect
                else "See journey blockers"
            ),
            "smallest_product_fix": cap["device_lab_implications"][
                "recommended_smallest_product_fix"
            ],
            "waike_gate_remains_false_until_owner_merge_refreeze": True,
        }
        (gui_dir / "WAIKE_DEFECT_DECISION.json").write_text(
            json.dumps(defect, indent=2) + "\n", encoding="utf-8"
        )

        gui_ok = bool(journey_a.get("launched_gui") and journey_b.get("launched_gui"))
        hub_bound = bool(bind.get("client_hub_http_chip_observed")) and not bool(
            bind.get("client_hub_mock_chip_observed")
        )
        and_ok = all(
            [
                bool(bundle.get("ok")),
                bool(bundle.get("pin_ok")),
                bool(fetched.get("ok")),
                bool(out.get("matches_main_aarch64_glibc236")),
                bool(out.get("RUNTIME_TARGET_PREFLIGHT_PASS")),
                bool(session_prov.get("ok")),
                gui_ok,
                bool(hub.get("ok")),
                hub_bound,
                bool(learner.get("complete")),
                bool(repeat.get("pass")),
                not product_defect,
            ]
        )
        out["WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"] = bool(and_ok)
        if not and_ok:
            if product_defect:
                out["blocker"] = (
                    "accepted_main_no_runtime_hub_url_override;"
                    "real_hub_sidecar_ok_but_client_cannot_bind;"
                    "need_draft_waike_product_pr_then_owner_merge_refreeze"
                )
            elif not gui_ok:
                out["blocker"] = (
                    "gui_window_not_alive_beyond_ipc_ack:"
                    + str(journey_a.get("ack") or journey_a.get("raw_stdout_tail") or "unknown")
                )[:500]
            else:
                out["blocker"] = "waike_gui_hub_and_gate_incomplete"

        verdict = {
            "generated_at_utc": _utc(),
            "prompt": "17G.5",
            "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": bool(and_ok),
            "verdict": "PASS" if and_ok else "FAIL",
            "blocker": None if and_ok else out.get("blocker"),
            "gui_window_alive": gui_ok,
            "real_hub_running": bool(hub.get("ok")),
            "client_bound_real_hub": hub_bound,
            "mock_hub_used": False,
            "xvfb_primary_pass": False,
            "headless_ack_only_pass": False,
            "defect_decision": defect.get("decision"),
            "RUNTIME_TARGET_PREFLIGHT_PASS": bool(out.get("RUNTIME_TARGET_PREFLIGHT_PASS")),
        }
        (gui_dir / "WAIKE_GUI_HUB_VERDICT.json").write_text(
            json.dumps(verdict, indent=2) + "\n", encoding="utf-8"
        )
        out["verdict"] = verdict
        out["finished_at_utc"] = _utc()
        return out
    finally:
        try:
            httpd.terminate()
        except Exception:
            pass
        if hub_proc is not None:
            try:
                hub_proc.terminate()
                hub_proc.wait(timeout=5)
            except Exception:
                try:
                    hub_proc.kill()
                except Exception:
                    pass
        if hub_log is not None:
            try:
                hub_log.close()
            except Exception:
                pass
        pid_path = work / "qemu.pid"
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                os.kill(pid, 15)
                time.sleep(2)
            except OSError:
                pass
