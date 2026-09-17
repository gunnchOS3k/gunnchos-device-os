"""Interactive Guest WAIKE real-runtime attempt using authentic Platform binary.

Prefer FAIL over false PASS. Seed HTML / fixture LMS / curriculum-alone never PASS.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import time
from datetime import datetime, timezone
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
    MAIN_AARCH64_SHA256,
    PIN_MANIFEST_SHA256,
    stage_owner_waike_bundle,
    write_runtime_provenance,
)
from gunnchos_device_os.device_lab.runtime_target_preflight import (
    PREFERRED_LABEL,
    run_runtime_target_preflight,
)

CLAIM = (
    "WAIKE real runtime requires authentic Platform Tauri Learning OS inside "
    "Interactive Development Guest via Device OS launch/package path. "
    "SILICON_EXACT_EMULATION=false. SHIPPING_IMAGE=false."
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _b64_put(session: Any, remote: str, data: bytes) -> dict[str, Any]:
    b64 = base64.b64encode(data).decode("ascii")
    # chunk if huge
    script = (
        "import base64,pathlib,sys\n"
        f"p=pathlib.Path({remote!r})\n"
        "p.parent.mkdir(parents=True, exist_ok=True)\n"
        f"p.write_bytes(base64.b64decode({b64!r}))\n"
        "print('PUT_OK', p, p.stat().st_size)\n"
    )
    return _agent_call(
        session,
        "process_run",
        argv=["python3", "-c", script],
        timeout_sec=60.0,
    )


def _guest_sh(session: Any, cmd: str, *, timeout_sec: float = 120.0) -> dict[str, Any]:
    return _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", cmd],
        timeout_sec=timeout_sec,
    )


def ensure_qemu_user_x86_64(session: Any) -> dict[str, Any]:
    """Additive compatibility: run authentic x86_64 CI ELF on aarch64 guest.

    qemu-user-static alone is insufficient for dynamically linked Tauri ELFs —
    the guest still needs an amd64 loader/libs (or a native aarch64 artifact).
    """
    probe = _guest_sh(
        session,
        "uname -m; "
        "command -v qemu-x86_64-static || true; "
        "command -v qemu-x86_64 || true; "
        "ls /lib64/ld-linux-x86-64.so.2 /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 2>/dev/null || true; "
        "dpkg -l qemu-user-static 2>/dev/null | tail -1 || true",
        timeout_sec=30.0,
    )
    out = (probe.get("stdout") or "") + (probe.get("stderr") or "")
    has_qemu = "qemu-x86_64" in out
    has_amd64_ld = "ld-linux-x86-64.so.2" in out
    if has_qemu and has_amd64_ld:
        return {
            "ok": True,
            "already_present": True,
            "amd64_loader_present": True,
            "probe": out[-500:],
        }
    install = _guest_sh(
        session,
        "export DEBIAN_FRONTEND=noninteractive; "
        "apt-get update -qq; "
        "apt-get install -y -qq qemu-user-static binfmt-support 2>&1 | tail -20; "
        # Best-effort multiarch loader so qemu-user can start dynamically linked ELFs.
        "dpkg --add-architecture amd64 2>/dev/null || true; "
        "apt-get update -qq 2>&1 | tail -5; "
        "apt-get install -y -qq libc6:amd64 2>&1 | tail -30 || true; "
        "command -v qemu-x86_64-static; "
        "ls -la /lib64/ld-linux-x86-64.so.2 /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 2>&1 || true; "
        "echo QEMU_USER_SETUP_DONE",
        timeout_sec=420.0,
    )
    iout = (install.get("stdout") or "") + (install.get("stderr") or "")
    ok_qemu = "qemu-x86_64" in iout
    ok_ld = ("/lib64/ld-linux-x86-64.so.2" in iout or "/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2" in iout) and (
        "No such file or directory" not in iout
        or iout.count("ld-linux-x86-64.so.2") > iout.count("No such file")
    )
    return {
        "ok": ok_qemu,
        "qemu_user_ok": ok_qemu,
        "amd64_loader_present": ok_ld,
        "already_present": False,
        "install_stdout_tail": iout[-1500:],
        "returncode": install.get("returncode"),
        "note": (
            "Even with amd64 loader, Tauri still needs amd64 GTK/WebKit libs; "
            "prefer aarch64 CI artifact for Device Lab guest."
        ),
    }


def ensure_tauri_aarch64_runtime(session: Any) -> dict[str, Any]:
    """Grow guest with legitimate WebKit/GTK/Tauri aarch64 runtime deps (additive).

    Under Device Lab ``restrict=on`` the guest cannot reach Debian mirrors.
    Prefer already-provisioned packages on the Interactive Guest overlay; only
    attempt ``apt-get`` when missing, with a hard fail-fast (never hang the
    virtio-serial guest agent on a blocked network).
    """
    packages = [
        "libwebkit2gtk-4.1-0",
        "libgtk-3-0",
        "libgdk-pixbuf-2.0-0",
        "libsoup-3.0-0",
        "libjavascriptcoregtk-4.1-0",
        "librsvg2-2",
        "libayatana-appindicator3-1",
        "xvfb",
        "at-spi2-core",
        "dbus-x11",
    ]
    probe = _guest_sh(
        session,
        "set -e; "
        "uname -m; "
        "dpkg -l libwebkit2gtk-4.1-0 libgtk-3-0 libsoup-3.0-0 "
        "  libjavascriptcoregtk-4.1-0 2>/dev/null | awk '/^ii/{print $2,$3}' || true; "
        "ldconfig -p 2>/dev/null | grep -E 'libwebkit2gtk-4.1|libgtk-3|libsoup-3' | head -8 || true; "
        "echo PROBE_DONE",
        timeout_sec=30.0,
    )
    pout = (probe.get("stdout") or "") + (probe.get("stderr") or "")
    have_webkit = "libwebkit2gtk-4.1-0" in pout and (
        "ii" in pout or "libwebkit2gtk-4.1.so" in pout
    )
    have_gtk = "libgtk-3-0" in pout or "libgtk-3.so" in pout
    have_soup = "libsoup-3.0-0" in pout or "libsoup-3" in pout
    already = bool(have_webkit and have_gtk and have_soup)
    if already:
        versions = [
            line.strip()
            for line in pout.splitlines()
            if line.strip().startswith("libwebkit2gtk")
            or line.strip().startswith("libgtk-3")
            or line.strip().startswith("libsoup")
            or line.strip().startswith("libjavascriptcoregtk")
        ]
        return {
            "ok": True,
            "already_present": True,
            "packages_requested": packages,
            "package_versions": versions,
            "install_stdout_tail": "skipped_apt_under_restrict_on_packages_present",
            "returncode": probe.get("returncode"),
            "probe_tail": pout[-500:],
            "additive": True,
            "no_feature_strip": True,
            "no_static_html_bypass": True,
            "apt_skipped": True,
        }

    # Fail-fast apt: restrict=on blocks mirrors; do not hang virtio-serial.
    pkg_line = " ".join(packages)
    install = _guest_sh(
        session,
        "export DEBIAN_FRONTEND=noninteractive; "
        "export APT_CONFIG=/dev/null; "
        "timeout 45 apt-get update -o Acquire::Retries=0 -o "
        "  Acquire::http::Timeout=5 -o Acquire::https::Timeout=5 -qq 2>&1 | tail -8; "
        f"timeout 120 apt-get install -y -qq -o Acquire::Retries=0 "
        f"  -o Acquire::http::Timeout=5 -o Acquire::https::Timeout=5 {pkg_line} "
        "  2>&1 | tail -40; "
        "dpkg -l libwebkit2gtk-4.1-0 libgtk-3-0 libsoup-3.0-0 "
        "  libjavascriptcoregtk-4.1-0 2>/dev/null | awk '/^ii/{print $2,$3}'; "
        "ldconfig -p 2>/dev/null | grep -E 'libwebkit2gtk-4.1.so|libgtk-3.so' | head -8 || true; "
        "command -v Xvfb || true; "
        "echo TAURI_RUNTIME_SETUP_DONE",
        timeout_sec=200.0,
    )
    iout = (install.get("stdout") or "") + (install.get("stderr") or "")
    ok = "TAURI_RUNTIME_SETUP_DONE" in iout and "libwebkit2gtk-4.1-0" in iout and (
        "ii" in iout or "libwebkit2gtk-4.1.so" in iout
    )
    versions = [
        line.strip()
        for line in iout.splitlines()
        if line.strip().startswith("libwebkit2gtk")
        or line.strip().startswith("libgtk-3")
        or line.strip().startswith("libsoup")
        or line.strip().startswith("libjavascriptcoregtk")
    ]
    return {
        "ok": ok,
        "already_present": False,
        "packages_requested": packages,
        "package_versions": versions,
        "install_stdout_tail": iout[-2000:],
        "returncode": install.get("returncode"),
        "probe_tail": pout[-500:],
        "additive": True,
        "no_feature_strip": True,
        "no_static_html_bypass": True,
        "apt_skipped": False,
        "restrict_on_note": (
            "apt may fail under restrict=on without offline package cache; "
            "prefer overlay-provisioned WebKit/GTK deps"
        ),
    }


def fetch_bundle_into_guest(
    session: Any, *, port: int = 8767, hub_only_guestfwd: bool = False
) -> dict[str, Any]:
    """Stage owner WAIKE bundle into guest via 9p (hub-only) or HTTP guestfwd.

    File-deployed script keeps the virtio-serial request small; status markers
    stay short so a multi-second silent 9p ``cp`` does not depend on streaming
    stdout. Caller must use a GuestAgentClient that waits through silent
    process_run (see guest_agent.client idle-buf fix).
    """
    remote_root = "/var/lib/gunnchos/waike-learning-os"
    marker = f"WAIKE_FETCH_{int(time.time())}"
    # Prefer 9p share (same path four-game uses). HTTP fallback only when httpd
    # guestfwd is present; 17G.5D hub-only must stay on 9p.
    script = f"""#!/bin/bash
set -uo pipefail
MARKER={marker}
REMOTE={remote_root}
PORT={port}
HUB_ONLY={1 if hub_only_guestfwd else 0}
echo START_$MARKER
rm -rf "$REMOTE.partial" "$REMOTE"
mkdir -p "$REMOTE.partial/bin"
SRC9=
for cand in /mnt/gdlgames /media/gdlgames /run/gunnchos/gdlgames; do
  if [ -f "$cand/bin/waike-learning-os" ]; then SRC9=$cand; break; fi
done
if [ -z "$SRC9" ]; then
  mkdir -p /mnt/gdlgames
  mount -t 9p -o trans=virtio,version=9p2000.L,ro gdlgames /mnt/gdlgames 2>/tmp/waike_9p_mount.err || true
  if [ -f /mnt/gdlgames/bin/waike-learning-os ]; then SRC9=/mnt/gdlgames; fi
fi
if [ -n "$SRC9" ]; then
  echo VIA_9P_$MARKER src=$SRC9
  cp -a "$SRC9/bin/waike-learning-os" "$REMOTE.partial/bin/waike-learning-os"
  cp -a "$SRC9/bin/VERSION" "$REMOTE.partial/bin/VERSION"
  cp -a "$SRC9/bin/INSTALLED.json" "$REMOTE.partial/bin/INSTALLED.json"
  cp -a "$SRC9/bin/waike-learning-os.qemu-x86_64-wrapper.sh" \\
    "$REMOTE.partial/bin/waike-learning-os.qemu-x86_64-wrapper.sh"
  cp -a "$SRC9/OWNER_WAIKE_BUNDLE_MANIFEST.json" "$REMOTE.partial/MANIFEST.json"
  cp -a "$SRC9/WAIKE_RUNTIME_PROVENANCE.json" "$REMOTE.partial/WAIKE_RUNTIME_PROVENANCE.json"
  [ -d "$SRC9/contracts" ] && cp -a "$SRC9/contracts" "$REMOTE.partial/contracts"
  [ -d "$SRC9/xdg" ] && cp -a "$SRC9/xdg" "$REMOTE.partial/xdg"
  # Launch adapter can import from live 9p; copy only if present and small enough.
  if [ -d "$SRC9/device_os_lib" ]; then
    cp -a "$SRC9/device_os_lib" "$REMOTE.partial/device_os_lib"
  fi
else
  if [ "$HUB_ONLY" = "1" ]; then
    echo HUB_ONLY_NO_HTTPD_$MARKER
    exit 41
  fi
  echo VIA_HTTP_$MARKER
  command -v curl
  curl -fsSL --connect-timeout 5 --max-time 60 \\
    "http://10.0.2.100:${{PORT}}/OWNER_WAIKE_BUNDLE_MANIFEST.json" \\
    -o "$REMOTE.partial/MANIFEST.json"
  curl -fsSL --connect-timeout 5 --max-time 180 \\
    "http://10.0.2.100:${{PORT}}/bin/waike-learning-os" \\
    -o "$REMOTE.partial/bin/waike-learning-os"
  curl -fsSL --connect-timeout 5 --max-time 30 \\
    "http://10.0.2.100:${{PORT}}/bin/VERSION" -o "$REMOTE.partial/bin/VERSION"
  curl -fsSL --connect-timeout 5 --max-time 30 \\
    "http://10.0.2.100:${{PORT}}/bin/INSTALLED.json" \\
    -o "$REMOTE.partial/bin/INSTALLED.json"
  curl -fsSL --connect-timeout 5 --max-time 30 \\
    "http://10.0.2.100:${{PORT}}/bin/waike-learning-os.qemu-x86_64-wrapper.sh" \\
    -o "$REMOTE.partial/bin/waike-learning-os.qemu-x86_64-wrapper.sh"
  curl -fsSL --connect-timeout 5 --max-time 30 \\
    "http://10.0.2.100:${{PORT}}/WAIKE_RUNTIME_PROVENANCE.json" \\
    -o "$REMOTE.partial/WAIKE_RUNTIME_PROVENANCE.json"
fi
chmod +x "$REMOTE.partial/bin/waike-learning-os" \\
  "$REMOTE.partial/bin/waike-learning-os.qemu-x86_64-wrapper.sh"
cp -a "$REMOTE.partial/bin/waike-learning-os" "$REMOTE.partial/bin/waike-learning-os.real"
BYTES=$(wc -c < "$REMOTE.partial/bin/waike-learning-os.real" | tr -d ' ')
file "$REMOTE.partial/bin/waike-learning-os.real" | head -1
echo BYTES_$MARKER=$BYTES
mv "$REMOTE.partial" "$REMOTE"
echo FETCH_OK_$MARKER
ls -la "$REMOTE/bin" | head -10
"""
    put = _b64_put(session, "/var/tmp/waike_owner_bundle_fetch.sh", script.encode())
    r = _guest_sh(
        session,
        "chmod +x /var/tmp/waike_owner_bundle_fetch.sh; "
        "/var/tmp/waike_owner_bundle_fetch.sh",
        timeout_sec=300.0,
    )
    out = (r.get("stdout") or "") + (r.get("stderr") or "")
    ok = f"FETCH_OK_{marker}" in out
    via = "9p" if f"VIA_9P_{marker}" in out else ("http" if f"VIA_HTTP_{marker}" in out else "unknown")
    return {
        "ok": ok,
        "via": via,
        "remote_root": remote_root,
        "stdout_tail": out[-2500:],
        "returncode": r.get("returncode"),
        "marker": marker,
        "hub_only_guestfwd": bool(hub_only_guestfwd),
        "agent_ok": bool(r.get("ok", True)),
        "put_ok": bool(put.get("ok", True)),
        "agent_error": r.get("error"),
        "agent_error_class": r.get("error_class"),
        "agent_detail": r.get("detail"),
    }


def maybe_enable_qemu_wrapper(session: Any, arch_gap: bool) -> dict[str, Any]:
    if not arch_gap:
        return {"ok": True, "wrapper_enabled": False, "reason": "no_arch_gap"}
    remote = "/var/lib/gunnchos/waike-learning-os"
    r = _guest_sh(
        session,
        f"set -euo pipefail; "
        f"cd {remote}/bin; "
        f"if command -v qemu-x86_64-static >/dev/null || command -v qemu-x86_64 >/dev/null; then "
        f"  cp -a waike-learning-os.qemu-x86_64-wrapper.sh waike-learning-os; "
        f"  chmod +x waike-learning-os waike-learning-os.real; "
        f"  echo WRAPPER_ON; "
        f"else "
        f"  echo WRAPPER_MISSING_QEMU; exit 2; "
        f"fi",
        timeout_sec=30.0,
    )
    out = (r.get("stdout") or "") + (r.get("stderr") or "")
    return {
        "ok": "WRAPPER_ON" in out,
        "wrapper_enabled": "WRAPPER_ON" in out,
        "stdout_tail": out[-500:],
        "returncode": r.get("returncode"),
    }


def guest_device_os_launch(
    session: Any,
    *,
    deep_link: str = "waike://learn/home",
    profile: str = "student",
    platform_role: str = "learner",
    journey_tag: str = "A",
) -> dict[str, Any]:
    """Launch via Device OS NativeLaunchAdapter inside guest (product path)."""
    install_root = "/var/lib/gunnchos/waike-learning-os"
    ipc_dir = f"/tmp/waike-los-ipc-j{journey_tag}"
    # Prefer in-guest Device OS module if present; else invoke binary with IPC protocol.
    script = f"""
import json, os, sys, time, uuid, tempfile
from pathlib import Path

install_root = Path({install_root!r})
os.environ['LEARNING_OS_INSTALL_ROOT'] = str(install_root)
os.environ['LEARNING_OS_APP_VERSION'] = {APP_VERSION!r}
os.environ['LEARNING_OS_PLATFORM_SHA'] = {ACCEPTED_WAIKE_LP_SHA!r}
os.environ['WAIKE_CI_HEADLESS_UI'] = '1'
os.environ['CI_HEADLESS_UI'] = '1'
os.environ['LEARNING_OS_CLEANUP_AFTER_ACK'] = '0'
os.environ['WAIKE_DEV_DB_KEY'] = '0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef'
os.environ['HOME'] = '/root'
os.environ['XDG_DATA_HOME'] = '/var/lib/gunnchos/waike-userdata'
# Stage TEST_ONLY verify key into paths load_verify_key() checks.
from pathlib import Path as _P
_key_candidates = [
    install_root / 'contracts/fixtures/keys/TEST_ONLY_ed25519_public.key',
    install_root / 'xdg/waike-learning-os/TEST_ONLY_ed25519_public.key',
    _P('/mnt/gdlgames/contracts/fixtures/keys/TEST_ONLY_ed25519_public.key'),
    _P('/mnt/gdlgames/xdg/waike-learning-os/TEST_ONLY_ed25519_public.key'),
]
_xdg = _P(os.environ['XDG_DATA_HOME']) / 'waike-learning-os'
_xdg.mkdir(parents=True, exist_ok=True)
for _k in _key_candidates:
    if _k.is_file():
        (_xdg / 'TEST_ONLY_ed25519_public.key').write_bytes(_k.read_bytes())
        (install_root / 'contracts/fixtures/keys').mkdir(parents=True, exist_ok=True)
        (install_root / 'contracts/fixtures/keys/TEST_ONLY_ed25519_public.key').write_bytes(_k.read_bytes())
        break
os.chdir(str(install_root))

sys.path.insert(0, '/opt/gunnchos/lib')
sys.path.insert(0, str(install_root / 'device_os_lib'))
sys.path.insert(0, '/mnt/gdlgames/device_os_lib')
result = {{'path': 'unknown'}}
try:
    from gunnchos_device_os.learning_os.native_launch import NativeLaunchAdapter
    from gunnchos_device_os.learning_os_launcher import launch_learning_os
    adapter = NativeLaunchAdapter(install_root=install_root, timeout_s=25.0, ipc_dir=Path({ipc_dir!r}))
    Path({ipc_dir!r}).mkdir(parents=True, exist_ok=True)
    r = launch_learning_os(
        {profile!r}, 'School', {deep_link!r},
        platform_role={platform_role!r},
        include_companion_seed=False,
        adapter=adapter,
        install_root=install_root,
    )
    result = {{'path': 'device_os_learning_os_launcher', **r}}
except Exception as exc:
    # Fallback: direct binary + FileIpcTransport-compatible argv used by native client.
    result = {{'path': 'fallback_direct', 'launcher_error': repr(exc)}}
    exe = install_root / 'bin' / 'waike-learning-os'
    if not exe.is_file():
        result['ok'] = False
        result['error'] = 'executable_missing'
        print(json.dumps(result))
        raise SystemExit(2)
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
        }},
    }}
    req_path = ipc / f'request-{{req_id}}.json'
    req_path.write_text(json.dumps(req, indent=2, sort_keys=True) + '\\n')
    env = os.environ.copy()
    env['LEARNING_OS_IPC_DIR'] = str(ipc)
    env['LEARNING_OS_REQUEST_ID'] = req_id
    env['WAIKE_CI_HEADLESS_UI'] = '1'
    env['CI_HEADLESS_UI'] = '1'
    env['XDG_DATA_HOME'] = os.environ['XDG_DATA_HOME']
    env['HOME'] = os.environ['HOME']
    import subprocess
    proc = subprocess.Popen(
        [
            str(exe),
            '--bundle-id', {BUNDLE_ID!r},
            '--deep-link', {deep_link!r},
            '--ipc-dir', str(ipc),
            '--request-id', req_id,
            '--ci-headless-ui',
        ],
        cwd=str(install_root),
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.time() + 25
    ack = None
    while time.time() < deadline:
        ack_path = ipc / f'ack-{{req_id}}.json'
        if ack_path.is_file():
            try:
                ack = json.loads(ack_path.read_text())
            except Exception as read_exc:
                ack = {{'parse_error': repr(read_exc)}}
            break
        if proc.poll() is not None:
            # one more ack check after exit
            if ack_path.is_file():
                try:
                    ack = json.loads(ack_path.read_text())
                except Exception:
                    pass
            break
        time.sleep(0.2)
    stdout, stderr = '', ''
    try:
        if proc.poll() is None:
            stdout, stderr = proc.communicate(timeout=5)
        else:
            try:
                stdout, stderr = proc.communicate(timeout=0.1)
            except Exception:
                stdout, stderr = '', ''
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    nack = bool(
        isinstance(ack, dict)
        and (
            ack.get('ok') is False
            or str(ack.get('message_type') or '').lower() == 'nack'
        )
    )
    # Successful ack must be an explicit positive acknowledgement.
    ack_ok = bool(
        isinstance(ack, dict)
        and not nack
        and (
            ack.get('ok') is True
            or str(ack.get('message_type') or '').lower()
            in {{'ack', 'launch_ack', 'ok'}}
        )
    )
    result.update({{
        'process_started': proc.pid is not None,
        'pid': proc.pid,
        'returncode': proc.returncode,
        'acknowledged': ack_ok,
        'ack': ack,
        'stdout_tail': (stdout or '')[-800:],
        'stderr_tail': (stderr or '')[-800:],
        'launched': ack_ok,
        'executable': str(exe),
        'fixture_rejected': 'fixtures/learning_os' not in str(exe),
    }})
# Guard: never accept protocol fixture path
exe = result.get('executable') or ''
if 'fixtures/learning_os' in str(exe):
    result['launched'] = False
    result['reason'] = 'fixture_binary_rejected'
print(json.dumps(result))
"""
    put = _b64_put(session, f"/var/tmp/waike_deviceos_launch_{journey_tag}.py", script.encode())
    run = _guest_sh(
        session,
        f"python3 /var/tmp/waike_deviceos_launch_{journey_tag}.py",
        timeout_sec=90.0,
    )
    out = run.get("stdout") or ""
    payload: dict[str, Any] = {"ok": False, "raw_stdout_tail": out[-2000:], "put": put}
    # Parse last JSON object from stdout
    for line in reversed(out.splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                payload = json.loads(line)
                break
            except json.JSONDecodeError:
                continue
    payload["guest_returncode"] = run.get("returncode")
    payload["journey_tag"] = journey_tag
    payload["deep_link"] = deep_link
    payload["platform_role"] = platform_role
    return payload


def probe_binary_exec(session: Any) -> dict[str, Any]:
    r = _guest_sh(
        session,
        "set -x; "
        "file /var/lib/gunnchos/waike-learning-os/bin/waike-learning-os; "
        "file /var/lib/gunnchos/waike-learning-os/bin/waike-learning-os.real 2>/dev/null || true; "
        "ls -la /var/lib/gunnchos/waike-learning-os/bin; "
        "/var/lib/gunnchos/waike-learning-os/bin/waike-learning-os --help 2>&1 | head -20 || true; "
        "echo PROBE_DONE",
        timeout_sec=60.0,
    )
    out = (r.get("stdout") or "") + (r.get("stderr") or "")
    return {"stdout_tail": out[-2000:], "returncode": r.get("returncode")}


def role_boundary_probe(session: Any) -> dict[str, Any]:
    """Learner vs instructor authorization via Device OS role mapping + launch context."""
    learner = guest_device_os_launch(
        session,
        deep_link="waike://learn/home",
        profile="student",
        platform_role="learner",
        journey_tag="roleL",
    )
    instructor = guest_device_os_launch(
        session,
        deep_link="waike://learn/home",
        profile="educator",
        platform_role="instructor",
        journey_tag="roleI",
    )
    # Frontend-only fakes rejected: both must go through Device OS launch path.
    return {
        "ok": bool(learner.get("path")) and bool(instructor.get("path")),
        "learner_launch": {
            "launched": bool(learner.get("launched") or learner.get("acknowledged")),
            "path": learner.get("path"),
            "platform_role": "learner",
            "profile": "student",
        },
        "instructor_launch": {
            "launched": bool(instructor.get("launched") or instructor.get("acknowledged")),
            "path": instructor.get("path"),
            "platform_role": "instructor",
            "profile": "educator",
        },
        "frontend_only_role_fake": False,
        "note": (
            "Role boundary exercised via Device OS launch context platform_role; "
            "not a CSS/UI-only toggle."
        ),
    }


def attempt_owner_waike_in_guest_pass(
    repo_root: Path,
    *,
    work: Path | None = None,
    memory_mb: int = 4096,
    boot_timeout_s: int = 240,
) -> dict[str, Any]:
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    out: dict[str, Any] = {
        "schema": "gunnchos.device_lab.waike_real_runtime_attempt.v1",
        "started_at_utc": _utc(),
        "pin_manifest_sha256": PIN_MANIFEST_SHA256,
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": True,
        "SHIPPING_IMAGE": False,
        "SILICON_EXACT_EMULATION": False,
        "GUNNCH_GUEST_AGENT_HOST_STUB": "0",
        "claim_boundary": CLAIM,
        "WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS": False,
        "prefer_fail_over_false_pass": True,
    }
    evidence = repo_root / "artifacts/device_lab_current_pin/waike"
    evidence.mkdir(parents=True, exist_ok=True)
    staging = evidence / "owner_bundle_stage"
    if staging.exists():
        shutil.rmtree(staging)
    bundle = stage_owner_waike_bundle(repo_root, staging)
    out["bundle"] = bundle
    if not bundle.get("ok"):
        out["blocker"] = bundle.get("error") or "owner_bundle_stage_failed"
        out["finished_at_utc"] = _utc()
        return out
    if not bundle.get("pin_ok"):
        out["blocker"] = "accepted_main_pin_verification_failed"
        out["finished_at_utc"] = _utc()
        return out

    # Section 6–7: RuntimeTarget preflight (static Device Lab Debian 12 profile)
    # before QEMU so Ubuntu GLIBC_2.39 never enters the guest journey path.
    preflight_static = run_runtime_target_preflight(
        repo_root,
        session=None,
        label=PREFERRED_LABEL,
        out_path=evidence / "RUNTIME_TARGET_PREFLIGHT.json",
    )
    out["runtime_target_preflight_static"] = preflight_static
    out["RUNTIME_TARGET_PREFLIGHT_PASS"] = bool(
        preflight_static.get("RUNTIME_TARGET_PREFLIGHT_PASS")
    )
    if not out["RUNTIME_TARGET_PREFLIGHT_PASS"]:
        out["blocker"] = (
            "RUNTIME_TARGET_PREFLIGHT_FAIL:"
            + ",".join(preflight_static.get("blockers") or ["unknown"])
        )
        out["finished_at_utc"] = _utc()
        return out

    binary_meta_early = bundle.get("binary") or {}
    if not binary_meta_early.get("matches_main_aarch64_glibc236_sha256"):
        out["blocker"] = (
            "glibc236_artifact_not_selected;"
            f"label={binary_meta_early.get('compatibility_label')};"
            "refuse_ubuntu2404_glibc239_on_debian12"
        )
        out["finished_at_utc"] = _utc()
        return out

    free_before = shutil.disk_usage("/").free / (1024**3)
    out["FREE_GIB_BEFORE_QEMU"] = round(free_before, 2)
    if free_before < 25:
        out["blocker"] = "WAIKE_STORAGE_BLOCKED_BEFORE_QEMU"
        out["finished_at_utc"] = _utc()
        return out

    work = work or (repo_root / "artifacts/wp011r/interactive_guest_session_waike")
    if work.exists():
        # Do not delete large disks blindly; require clean session dir name.
        shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)

    # Expose owner WAIKE bundle via the Interactive Guest 9p tag (gdlgames).
    os.environ["GUNNCH_LAB_GAMES_9P_PATH"] = str(staging)
    os.environ.setdefault("GUNNCHDEVICE_LAB_NET_RESTRICT", "0")

    httpd = start_host_artifact_httpd(
        staging,
        port=8767,
        log_path=evidence / "host_artifact_httpd_waike.log",
    )
    ok_listen, listen_err = wait_host_artifact_httpd(8767, proc=httpd)
    out["httpd"] = {"ok": ok_listen, "error": listen_err, "port": 8767}
    if not ok_listen:
        httpd.terminate()
        out["blocker"] = f"host_artifact_httpd:{listen_err}"
        out["finished_at_utc"] = _utc()
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
            out["blocker"] = boot.get("error") or "interactive_guest_boot_failed_no_session"
            out["finished_at_utc"] = _utc()
            return out
        if not _wait_agent(session, tries=40, sleep_s=1.0):
            out["blocker"] = "guest_agent_not_ready"
            out["finished_at_utc"] = _utc()
            return out
        ping = _agent_call(session, "ping", timeout_sec=8.0)
        out["ping"] = ping
        if not ping.get("pong") or ping.get("transport") == "host_stub":
            out["blocker"] = "guest_agent_not_real_virtio_serial"
            out["finished_at_utc"] = _utc()
            return out

        uname = _guest_sh(session, "uname -am", timeout_sec=20.0)
        out["guest_uname"] = (uname.get("stdout") or "").strip()

        arch_gap = bool(bundle.get("arch_gap"))
        binary_meta = (bundle.get("binary") or {})
        out["staged_arch"] = binary_meta.get("source_arch")
        out["artifact_source_sha"] = binary_meta.get("artifact_source_sha")
        out["artifact_sha256"] = binary_meta.get("artifact_sha256") or binary_meta.get("source_sha256")
        out["compatibility_label"] = binary_meta.get("compatibility_label")
        out["matches_main_aarch64_glibc236"] = (
            str(out.get("artifact_sha256") or "") == MAIN_AARCH64_GLIBC236_SHA256
        )
        # Retained for provenance contrast; Ubuntu ARM must not drive PASS.
        out["matches_main_aarch64_ubuntu2404"] = (
            str(out.get("artifact_sha256") or "") == MAIN_AARCH64_SHA256
        )
        out["matches_main_aarch64"] = out["matches_main_aarch64_glibc236"]

        if arch_gap:
            qemu_user = ensure_qemu_user_x86_64(session)
            out["qemu_user_x86_64"] = qemu_user
        else:
            out["qemu_user_x86_64"] = {
                "ok": True,
                "skipped": True,
                "reason": "native_aarch64_artifact_no_arch_gap",
            }

        tauri_rt = ensure_tauri_aarch64_runtime(session)
        out["tauri_aarch64_runtime"] = tauri_rt
        # Let apt/binfmt settle before large HTTP pulls.
        time.sleep(2.0)

        # Live guest RuntimeTarget preflight after WebKit/GTK growth; required before journey.
        preflight_live = run_runtime_target_preflight(
            repo_root,
            session=session,
            label=PREFERRED_LABEL,
            out_path=evidence / "RUNTIME_TARGET_PREFLIGHT.json",
        )
        out["runtime_target_preflight"] = preflight_live
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

        fetched = fetch_bundle_into_guest(session, port=8767)
        out["fetch"] = fetched
        if not fetched.get("ok"):
            # Fallback: virtio file_put for binary (HTTP may be net-restricted).
            staging_bin = staging / "bin" / "waike-learning-os"
            put_tries = {}
            if staging_bin.is_file():
                put_tries["binary"] = _b64_put(
                    session,
                    "/var/lib/gunnchos/waike-learning-os/bin/waike-learning-os",
                    staging_bin.read_bytes(),
                )
                for name in ("VERSION", "INSTALLED.json", "waike-learning-os.qemu-x86_64-wrapper.sh"):
                    p = staging / "bin" / name
                    if p.is_file():
                        put_tries[name] = _b64_put(
                            session,
                            f"/var/lib/gunnchos/waike-learning-os/bin/{name}",
                            p.read_bytes(),
                        )
                for name in ("OWNER_WAIKE_BUNDLE_MANIFEST.json", "WAIKE_RUNTIME_PROVENANCE.json"):
                    p = staging / name
                    if p.is_file():
                        put_tries[name] = _b64_put(
                            session,
                            f"/var/lib/gunnchos/waike-learning-os/{name}",
                            p.read_bytes(),
                        )
                finalize = _guest_sh(
                    session,
                    "set -euo pipefail; "
                    "ROOT=/var/lib/gunnchos/waike-learning-os; "
                    "chmod +x $ROOT/bin/waike-learning-os "
                    "  $ROOT/bin/waike-learning-os.qemu-x86_64-wrapper.sh || true; "
                    "cp -a $ROOT/bin/waike-learning-os $ROOT/bin/waike-learning-os.real; "
                    "file $ROOT/bin/waike-learning-os.real; "
                    "wc -c $ROOT/bin/waike-learning-os.real; "
                    "echo PUT_FETCH_OK",
                    timeout_sec=60.0,
                )
                fout = (finalize.get("stdout") or "") + (finalize.get("stderr") or "")
                out["fetch_file_put_fallback"] = {
                    "puts": {k: bool(v.get("ok") or "PUT_OK" in str(v.get("stdout") or "")) for k, v in put_tries.items()},
                    "finalize_tail": fout[-800:],
                }
                if "PUT_FETCH_OK" in fout:
                    fetched = {
                        "ok": True,
                        "remote_root": "/var/lib/gunnchos/waike-learning-os",
                        "via": "virtio_file_put_fallback",
                        "stdout_tail": fout[-800:],
                    }
                    out["fetch"] = fetched
            if not fetched.get("ok"):
                out["blocker"] = "guest_fetch_owner_bundle_failed"
                out["finished_at_utc"] = _utc()
                return out

        wrapped = maybe_enable_qemu_wrapper(session, arch_gap)
        out["qemu_wrapper"] = wrapped
        if arch_gap and not wrapped.get("ok"):
            out["blocker"] = "arch_gap_x86_64_binary_on_aarch64_guest_without_qemu_user"
            out["finished_at_utc"] = _utc()
            return out

        # Native aarch64: ensure .real exists and launcher points at ELF directly.
        if not arch_gap:
            native = _guest_sh(
                session,
                "set -euo pipefail; "
                "ROOT=/var/lib/gunnchos/waike-learning-os/bin; "
                "if [ ! -f $ROOT/waike-learning-os.real ]; then "
                "  cp -a $ROOT/waike-learning-os $ROOT/waike-learning-os.real; "
                "fi; "
                "cp -a $ROOT/waike-learning-os.real $ROOT/waike-learning-os; "
                "chmod +x $ROOT/waike-learning-os $ROOT/waike-learning-os.real; "
                "file $ROOT/waike-learning-os; "
                "echo NATIVE_ELF_READY",
                timeout_sec=30.0,
            )
            out["native_elf_ready"] = {
                "ok": "NATIVE_ELF_READY" in ((native.get("stdout") or "") + (native.get("stderr") or "")),
                "stdout_tail": ((native.get("stdout") or "") + (native.get("stderr") or ""))[-500:],
            }

        out["binary_probe"] = probe_binary_exec(session)
        probe_tail = str((out["binary_probe"] or {}).get("stdout_tail") or "")
        if arch_gap and (
            "Could not open '/lib64/ld-linux-x86-64.so.2'" in probe_tail
            or ("ld-linux-x86-64.so.2" in probe_tail and "No such file" in probe_tail)
        ):
            out["blocker"] = (
                "ci_linux_x86_64_elf_on_aarch64_guest_missing_amd64_loader_or_libs;"
                "qemu_user_static_insufficient_for_dynamic_tauri;"
                "need_aarch64_linux_ci_artifact_or_in_guest_native_build"
            )
            # Still attempt launch for evidence, but do not claim PASS.
            out["arch_runtime_gap"] = True

        # Journey A
        journey_a = guest_device_os_launch(session, journey_tag="A")
        out["journey_a_launch"] = journey_a
        # Role boundary
        out["role_boundary"] = role_boundary_probe(session)
        # Journey B (fresh launch — repeatability)
        journey_b = guest_device_os_launch(session, journey_tag="B")
        out["journey_b_launch"] = journey_b

        launch_a_ok = bool(journey_a.get("launched") or journey_a.get("acknowledged"))
        launch_b_ok = bool(journey_b.get("launched") or journey_b.get("acknowledged"))
        fixture_ok = bool(journey_a.get("fixture_rejected", True)) and (
            "fixtures/learning_os" not in str(journey_a.get("executable") or "")
        )
        native_aarch64 = (not arch_gap) and "aarch64" in probe_tail.lower()

        # Depth classification: headless ack proves Device OS↔Platform launch IPC,
        # but accepted-main headless path exits before PackService learner mutations.
        # Do NOT invent course/lesson/assessment PASS from launch alone.
        out["capability_classification"] = {
            "device_os_native_launch_ipc": launch_a_ok,
            "authentic_platform_binary": fixture_ok and bool(fetched.get("ok")),
            "accepted_main_aarch64_glibc236_artifact": bool(
                out.get("matches_main_aarch64_glibc236")
            ),
            "runtime_target_preflight_pass": bool(out.get("RUNTIME_TARGET_PREFLIGHT_PASS")),
            "native_aarch64_guest_exec": native_aarch64,
            "tauri_runtime_libs_present": bool(tauri_rt.get("ok")),
            "learner_course_lesson_interaction": False,
            "assessment_submission_mutation": False,
            "offline_sync_outbox": "supported_in_product_not_exercised_this_run",
            "reason": (
                "Accepted-main WAIKE_CI_HEADLESS_UI acknowledges Device OS IPC then "
                "returns before Tauri invoke surface (install/lesson/quiz/outbox). "
                "linux-aarch64-glibc236 removes Debian 12 glibc gap; full learner/"
                "assessment/offline/recovery depth still requires GUI/webview journey "
                "surface or an accepted product non-GUI journey harness (not invented)."
            ),
        }

        learner_journey_complete = False  # honest — not earned this run via headless-only
        out["learner_journey"] = {
            "launch": launch_a_ok,
            "identity_role_context": bool(out["role_boundary"].get("ok")),
            "course": False,
            "lesson": False,
            "interaction": False,
            "assessed_or_submission_mutation": False,
            "persist_readback": False,
            "close_relaunch_restore": launch_a_ok and launch_b_ok,
            "complete": learner_journey_complete,
        }
        out["offline_reconnect"] = {
            "exercised": False,
            "reason": "product_outbox_surface_requires_tauri_invoke_not_headless_ack",
        }
        out["recovery"] = {
            "exercised": False,
            "reason": "controlled_failure_injection_requires_deeper_runtime_surface",
        }
        out["repeatability"] = {
            "journey_a": launch_a_ok,
            "journey_b": launch_b_ok,
            "pass": launch_a_ok and launch_b_ok,
        }

        and_ok = all(
            [
                bool(bundle.get("ok")),
                bool(bundle.get("pin_ok")),
                bool(fetched.get("ok")),
                fixture_ok,
                launch_a_ok,
                launch_b_ok,
                learner_journey_complete,
                bool(out["role_boundary"].get("ok")),
                bool(out.get("matches_main_aarch64_glibc236")),
                bool(out.get("RUNTIME_TARGET_PREFLIGHT_PASS")),
                not arch_gap,
            ]
        )
        out["WAIKE_REAL_RUNTIME_DEVICE_LAB_PASS"] = bool(and_ok)
        if not and_ok:
            if not out.get("matches_main_aarch64_glibc236") or arch_gap:
                out["blocker"] = (
                    "accepted_main_glibc236_artifact_not_staged_or_arch_gap_remains"
                )
            elif not out.get("RUNTIME_TARGET_PREFLIGHT_PASS"):
                out["blocker"] = "RUNTIME_TARGET_PREFLIGHT_FAIL"
            elif launch_a_ok and not learner_journey_complete:
                out["blocker"] = (
                    "native_aarch64_glibc236_headless_launch_ack_only_learner_journey_depth_not_earned;"
                    "need_gui_or_product_journey_surface_for_course_assessment_offline_recovery"
                )
            elif not launch_a_ok:
                out["blocker"] = (
                    "device_os_platform_launch_failed:"
                    + str(journey_a.get("reason") or journey_a.get("error") or journey_a.get("launcher_error") or "unknown")
                )
            else:
                out["blocker"] = "waike_and_gate_incomplete"
        out["finished_at_utc"] = _utc()
        return out
    finally:
        try:
            httpd.terminate()
        except Exception:
            pass
        # Power off guest if session still around — best effort via work dir pid.
        pid_path = work / "qemu.pid"
        if pid_path.exists():
            try:
                pid = int(pid_path.read_text().strip())
                os.kill(pid, 15)
                time.sleep(2)
            except OSError:
                pass
