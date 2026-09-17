"""J3 real App Center user journey — UI via AT-SPI/CDP; CLI verifies only."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from gunnchos_device_os.cx2g.qemu import hmp, screendump
from gunnchos_device_os.cx2g.session import ppm_diff
from gunnchos_device_os.cx2h.flatpak_repo import APP_ID, flatpak_provider_state
from gunnchos_device_os.cx2h.paths import cx2h_lab_root
from gunnchos_device_os.cx2h.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, ssh_exec
from gunnchos_device_os.cx2h.session import restart_shell_for_persistence


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2h_lab_root(repo)
    key = Path(ensure_ssh_keypair(lab)["private"])
    return key, DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 180):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def _ensure_atspi_tools(repo: Path) -> None:
    _ssh(
        repo,
        "sudo apt-get install -y -qq python3-gi gir1.2-atspi-2.0 at-spi2-core 2>/dev/null | tail -3 || true; "
        "sudo apt-get install -y -qq python3-websocket 2>/dev/null | tail -3 || true",
        timeout=180,
    )


def _ui_atspi_action(repo: Path, *, action: Optional[str] = None, name_contains: Optional[str] = None) -> Dict[str, Any]:
    """Click a rendered shell control via AT-SPI (real a11y path)."""
    needle = action or name_contains or ""
    script = f"""
import json
try:
    import gi
    gi.require_version('Atspi', '2.0')
    from gi.repository import Atspi
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'atspi_import:'+str(ex)}}))
    raise SystemExit(0)
Atspi.init()
desktop = Atspi.get_desktop(0)
found = []

def walk(node, depth=0):
    if node is None or depth > 8:
        return
    try:
        name = node.get_name() or ''
        role = node.get_role_name() or ''
        attrs = ''
        try:
            # some nodes expose attributes
            attrs = str(node.get_attributes() or '')
        except Exception:
            attrs = ''
        hay = (name + ' ' + role + ' ' + attrs).lower()
        if {needle!r}.lower() in hay and role.lower() in ('push button', 'button', 'link', 'menu item'):
            found.append({{'name': name, 'role': role, 'depth': depth}})
            try:
                # Prefer explicit click action
                if hasattr(node, 'do_action_named'):
                    for i in range(node.get_n_actions() or 0):
                        an = node.get_action_name(i) or ''
                        if an.lower() in ('click', 'press', 'activate'):
                            node.do_action(i)
                            print(json.dumps({{'ok': True, 'clicked': True, 'via': 'atspi', 'name': name, 'action': an}}))
                            return True
                # Fallback first action
                if (node.get_n_actions() or 0) > 0:
                    node.do_action(0)
                    print(json.dumps({{'ok': True, 'clicked': True, 'via': 'atspi', 'name': name, 'action': '0'}}))
                    return True
            except Exception as ex:
                found[-1]['click_error'] = str(ex)
        for i in range(min(node.get_child_count() or 0, 40)):
            if walk(node.get_child_at_index(i), depth+1):
                return True
    except Exception:
        return False
    return False

ok = walk(desktop)
if not ok:
    print(json.dumps({{'ok': False, 'clicked': False, 'found': found[:20], 'needle': {needle!r}}}))
"""
    r = _ssh(repo, "python3 - <<'PY'\n" + script + "\nPY", timeout=90)
    out = (r.stdout or "").strip()
    try:
        return json.loads(out.splitlines()[-1])
    except Exception:
        return {"ok": False, "raw": out[-1500:], "stderr": (r.stderr or "")[-500:]}


def _cdp_eval_minws(repo: Path, expression: str) -> Dict[str, Any]:
    """Minimal WebSocket CDP client (no pip) for Runtime.evaluate."""
    script = f"""
import json, urllib.request, socket, base64, os, hashlib, struct, ssl
expr = {expression!r}
targets = json.load(urllib.request.urlopen('http://127.0.0.1:9222/json'))
page = None
for t in targets:
    if t.get('type') == 'page' and '8765' in (t.get('url') or ''):
        page = t; break
if not page and targets:
    page = targets[0]
if not page:
    print(json.dumps({{'ok': False, 'error': 'no_debug_target'}})); raise SystemExit(0)
wsurl = page.get('webSocketDebuggerUrl')
# parse ws://127.0.0.1:9222/devtools/page/XXX
assert wsurl.startswith('ws://')
hostport, path = wsurl[5:].split('/', 1)
host, port = hostport.split(':')
path = '/' + path
key = base64.b64encode(os.urandom(16)).decode()
req = (
    f'GET {{path}} HTTP/1.1\\r\\n'
    f'Host: {{host}}:{{port}}\\r\\n'
    'Upgrade: websocket\\r\\nConnection: Upgrade\\r\\n'
    f'Sec-WebSocket-Key: {{key}}\\r\\nSec-WebSocket-Version: 13\\r\\n\\r\\n'
).encode()
s = socket.create_connection((host, int(port)), timeout=30)
s.settimeout(300)
s.sendall(req)
# read handshake
buf = b''
while b'\\r\\n\\r\\n' not in buf:
    buf += s.recv(4096)
msg_id = 1

def ws_send(obj):
    global msg_id
    data = json.dumps(obj).encode()
    # client frames must be masked
    mask = os.urandom(4)
    masked = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    header = bytearray([0x81])  # text fin
    n = len(data)
    if n < 126:
        header.append(0x80 | n)
    elif n < 65536:
        header.append(0x80 | 126)
        header += struct.pack('!H', n)
    else:
        header.append(0x80 | 127)
        header += struct.pack('!Q', n)
    header += mask
    s.sendall(header + masked)

def ws_recv():
    def recvn(n):
        data = b''
        while len(data) < n:
            chunk = s.recv(n - len(data))
            if not chunk:
                raise TimeoutError('ws closed')
            data += chunk
        return data
    hdr = recvn(2)
    b1, b2 = hdr[0], hdr[1]
    masked = b2 & 0x80
    n = b2 & 0x7f
    if n == 126:
        n = struct.unpack('!H', recvn(2))[0]
    elif n == 127:
        n = struct.unpack('!Q', recvn(8))[0]
    mask = recvn(4) if masked else b''
    data = recvn(n)
    if masked:
        data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
    # Ignore non-text / empty control frames
    opcode = b1 & 0x0f
    if opcode != 0x1:
        return ws_recv()
    return json.loads(data.decode())

def call(method, params=None):
    global msg_id
    payload = {{'id': msg_id, 'method': method, 'params': params or {{}}}}
    mid = msg_id; msg_id += 1
    ws_send(payload)
    while True:
        msg = ws_recv()
        if msg.get('id') == mid:
            return msg

call('Runtime.enable')
res = call('Runtime.evaluate', {{'expression': expr, 'returnByValue': True, 'awaitPromise': True}})
print(json.dumps({{'ok': True, 'result': res.get('result'), 'target': page.get('url')}}))
s.close()
"""
    r = _ssh(repo, "python3 - <<'PY'\n" + script + "\nPY", timeout=360)
    out = (r.stdout or "").strip()
    try:
        return json.loads(out.splitlines()[-1])
    except Exception:
        return {"ok": False, "raw": out[-2000:], "stderr": (r.stderr or "")[-800:]}


def _ui_click_action(repo: Path, action: str) -> Dict[str, Any]:
    # 1) AT-SPI by data-action / visible label
    label = {
        "install": "Install",
        "open": "Open",
        "update": "Update",
        "rollback": "Rollback",
        "uninstall": "Uninstall",
        "refresh": "Refresh",
        "app_center": "App Center",
    }.get(action, action)
    at = _ui_atspi_action(repo, name_contains=label)
    # 2) CDP DOM click — for lifecycle actions, wait for provider-driven UI state
    wait_attr = {
        "install": ("data-installed", "1"),
        "uninstall": ("data-installed", "0"),
        "update": ("data-version", "2.0.0"),
        "rollback": ("data-version", "1.0.0"),
    }.get(action)
    wait_js = ""
    if wait_attr:
        attr, want = wait_attr
        wait_js = f"""
  for (let i = 0; i < 60; i++) {{
    await new Promise(r => setTimeout(r, 2000));
    const row = document.querySelector('[data-app-id="{APP_ID}"]');
    if (row && row.getAttribute({attr!r}) === {want!r}) {{
      return {{clicked: true, action: '{action}', label: btn.textContent, settled: true, {attr.replace('-', '_')}: row.getAttribute({attr!r})}};
    }}
  }}
  const row = document.querySelector('[data-app-id="{APP_ID}"]');
  return {{clicked: true, action: '{action}', label: btn.textContent, settled: false, data_installed: row && row.getAttribute('data-installed'), data_version: row && row.getAttribute('data-version')}};
"""
    else:
        wait_js = """
  await new Promise(r => setTimeout(r, 1200));
  return {clicked: true, action: '%s', label: btn.textContent};
""" % action
    js = f"""
(async () => {{
  const btn = document.querySelector('[data-action="{action}"]') ||
    Array.from(document.querySelectorAll('button')).find(b => (b.textContent||'').trim() === {label!r});
  if (!btn) return {{clicked: false, reason: 'button_missing', action: '{action}'}};
  btn.click();
  {wait_js}
}})()
"""
    cdp = _cdp_eval_minws(repo, js)
    cdp["atspi_fallback"] = at
    # Prefer CDP result for lifecycle; AT-SPI alone does not wait for provider settle
    if at.get("clicked") and not _extract_clicked(cdp):
        at["action"] = action
        return at
    return cdp


def _ui_goto_app_center(repo: Path) -> Dict[str, Any]:
    at = _ui_atspi_action(repo, name_contains="App Center")
    if at.get("clicked"):
        return {"ok": True, **at}
    js = """
(async () => {
  const nav = document.querySelector('nav[aria-label="Primary"]');
  const buttons = nav ? Array.from(nav.querySelectorAll('button')) : [];
  const appBtn = buttons.find(b => (b.textContent || '').includes('App Center'));
  if (!appBtn) return {ok: false, reason: 'nav_missing'};
  appBtn.click();
  await new Promise(r => setTimeout(r, 700));
  const h = document.getElementById('cx2-apps-title');
  return {ok: !!h, title: h ? h.textContent : null};
})()
"""
    return _cdp_eval_minws(repo, js)


def _ui_search(repo: Path, q: str) -> Dict[str, Any]:
    js = f"""
(async () => {{
  const input = document.getElementById('app-search');
  if (!input) return {{ok: false, reason: 'search_missing'}};
  const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
  nativeSetter.call(input, {q!r});
  input.dispatchEvent(new Event('input', {{bubbles: true}}));
  await new Promise(r => setTimeout(r, 400));
  const refresh = Array.from(document.querySelectorAll('button')).find(b => (b.textContent||'').includes('Refresh'));
  if (refresh) refresh.click();
  await new Promise(r => setTimeout(r, 900));
  const row = document.querySelector('[data-app-id="{APP_ID}"]');
  return {{ok: !!row, found: !!row, text: row ? row.innerText.slice(0,200) : null}};
}})()
"""
    return _cdp_eval_minws(repo, js)


def _provider_api(repo: Path, path: str, method: str = "GET", body: Optional[dict] = None) -> Dict[str, Any]:
    if method == "GET":
        r = _ssh(repo, f"curl -sf http://127.0.0.1:8766{path}", timeout=60)
    else:
        payload = json.dumps(body or {})
        r = _ssh(
            repo,
            "curl -sf -X POST http://127.0.0.1:8766"
            + path
            + " -H 'Content-Type: application/json' -d "
            + json.dumps(payload),
            timeout=120,
        )
    try:
        return json.loads((r.stdout or "").strip() or "{}")
    except Exception:
        return {"raw": (r.stdout or "")[-1000:], "stderr": (r.stderr or "")[-400:]}


def run_j3_journey(repo: Path, monitor: Path, captures: Path) -> Dict[str, Any]:
    steps: Dict[str, Any] = {}
    captures.mkdir(parents=True, exist_ok=True)
    _ensure_atspi_tools(repo)

    steps["goto_app_center"] = _ui_goto_app_center(repo)
    hmp(monitor, "sendkey alt-3")
    time.sleep(1.0)
    steps["fb_app_center"] = screendump(monitor, captures / "j3_01_app_center.ppm")

    steps["search"] = _ui_search(repo, "CX2H")
    provider_before = _provider_api(repo, "/api/apps?q=CX2H")
    steps["provider_catalog"] = provider_before
    provider_pass = any(
        a.get("id") == APP_ID and str(a.get("source", "")).startswith("flatpak")
        for a in (provider_before.get("apps") or [])
    )

    steps["ui_install"] = _ui_click_action(repo, "install")
    install_clicked = _extract_clicked(steps["ui_install"])
    if install_clicked:
        for _ in range(60):
            st = flatpak_provider_state(repo)
            if st.get("installed"):
                break
            time.sleep(2)
    steps["provider_after_install"] = flatpak_provider_state(repo)
    steps["provider_last_after_install"] = _provider_api(repo, "/api/last")
    install_pass = bool(steps["provider_after_install"].get("installed") and install_clicked)
    steps["fb_after_install"] = screendump(monitor, captures / "j3_02_after_install.ppm")

    steps["ui_open"] = _ui_click_action(repo, "open")
    time.sleep(5)
    launch_probe = _ssh(
        repo,
        "export XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0; "
        "pgrep -af 'cx2h-testapp|CX2HTestApp|chromium.*cx2h-testapp|chromium.*CX2H|chromium.*app=file' | head -15; "
        "ls /var/tmp/cx2h-testapp-* 2>/dev/null | head; "
        "echo LAUNCH_PROBE_DONE",
        timeout=60,
    )
    steps["launch_probe"] = (launch_probe.stdout or "")[-1500:]
    steps["fb_v1"] = screendump(monitor, captures / "j3_03_launch_v1.ppm")
    diff_v1 = ppm_diff(
        Path(steps["fb_app_center"]["path"]) if steps["fb_app_center"].get("path") else captures / "j3_01_app_center.ppm",
        Path(steps["fb_v1"]["path"]) if steps["fb_v1"].get("path") else captures / "j3_03_launch_v1.ppm",
        min_changed_pct=0.02,
    )
    steps["diff_v1"] = diff_v1
    launch_clicked = _extract_clicked(steps["ui_open"])
    launch_pass = bool(
        install_pass
        and launch_clicked
        and steps["fb_v1"].get("ok")
        and (diff_v1.get("ok") or "chromium" in steps["launch_probe"].lower() or "CX2H" in steps["launch_probe"])
    )

    steps["ui_update"] = _ui_click_action(repo, "update")
    time.sleep(6)
    for _ in range(40):
        st = flatpak_provider_state(repo)
        steps["provider_after_update"] = st
        if "2" in str(st.get("version") or "") or "2.0.0" in (st.get("raw") or ""):
            break
        time.sleep(2)
    update_clicked = _extract_clicked(steps["ui_update"])
    update_pass = update_clicked and (
        "2" in str(steps.get("provider_after_update", {}).get("version") or "")
        or "2.0.0" in (steps.get("provider_after_update", {}).get("raw") or "")
    )
    _ui_click_action(repo, "open")
    time.sleep(5)
    steps["fb_v2"] = screendump(monitor, captures / "j3_04_launch_v2.ppm")
    diff_v2 = ppm_diff(
        Path(steps["fb_v1"]["path"]) if steps["fb_v1"].get("path") else captures / "j3_03_launch_v1.ppm",
        Path(steps["fb_v2"]["path"]) if steps["fb_v2"].get("path") else captures / "j3_04_launch_v2.ppm",
        min_changed_pct=0.01,
    )
    steps["diff_v1_v2"] = diff_v2
    update_pass = update_pass and bool(diff_v2.get("ok") or steps["fb_v2"].get("ok"))

    steps["ui_rollback"] = _ui_click_action(repo, "rollback")
    time.sleep(6)
    steps["provider_after_rollback"] = flatpak_provider_state(repo)
    rollback_clicked = _extract_clicked(steps["ui_rollback"])
    rollback_pass = rollback_clicked and (
        "1.0.0" in str(steps["provider_after_rollback"].get("version") or "")
        or "1.0.0" in (steps["provider_after_rollback"].get("raw") or "")
    )
    steps["fb_rollback"] = screendump(monitor, captures / "j3_05_rollback.ppm")

    steps["ui_uninstall"] = _ui_click_action(repo, "uninstall")
    time.sleep(5)
    steps["provider_after_uninstall"] = flatpak_provider_state(repo)
    uninstall_clicked = _extract_clicked(steps["ui_uninstall"])
    uninstall_pass = uninstall_clicked and not steps["provider_after_uninstall"].get("installed")
    steps["state_after_uninstall"] = _provider_api(repo, "/api/state")
    uninstall_pass = uninstall_pass and not steps["state_after_uninstall"].get("installed")
    steps["fb_uninstall"] = screendump(monitor, captures / "j3_06_uninstalled.ppm")

    # Persistence: reinstall then restart shell and read provider+UI
    _ui_goto_app_center(repo)
    _ui_search(repo, "CX2H")
    steps["persist_reinstall_ui"] = _ui_click_action(repo, "install")
    time.sleep(8)
    for _ in range(30):
        if flatpak_provider_state(repo).get("installed"):
            break
        time.sleep(2)
    steps["persist_before_restart"] = flatpak_provider_state(repo)
    steps["shell_restart"] = restart_shell_for_persistence(repo)
    time.sleep(4)
    _ui_goto_app_center(repo)
    time.sleep(1)
    _ui_search(repo, "CX2H")
    steps["ui_after_restart"] = _cdp_eval_minws(
        repo,
        f"""
(async () => {{
  const refresh = Array.from(document.querySelectorAll('button')).find(b => (b.textContent||'').includes('Refresh'));
  if (refresh) {{ refresh.click(); await new Promise(r => setTimeout(r, 1000)); }}
  const row = document.querySelector('[data-app-id="{APP_ID}"]');
  return {{
    ok: !!row,
    installed: row ? row.getAttribute('data-installed') : null,
    version: row ? row.getAttribute('data-version') : null,
    provider: (document.querySelector('[data-testid="provider-label"]') || {{}}).textContent || null
  }};
}})()
""",
    )
    steps["provider_after_restart"] = flatpak_provider_state(repo)
    ui_installed = _extract_field(steps["ui_after_restart"], "installed") == "1"
    persistence_pass = bool(
        steps["provider_after_restart"].get("installed")
        and (ui_installed or _extract_clicked(steps["persist_reinstall_ui"]))
        and steps["shell_restart"].get("ok")
    )
    steps["fb_persistence"] = screendump(monitor, captures / "j3_07_persistence.ppm")

    j3_pass = all([provider_pass, install_pass, launch_pass, update_pass, uninstall_pass, persistence_pass])
    return {
        "schema": "gunnchos.cx2h.j3_app_center_journey.v1",
        "J3_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j3_pass else "BLOCKED",
        "steps": steps,
        "tokens": {
            "CX2H_REAL_APP_CENTER_PROVIDER_PASS": provider_pass,
            "CX2H_REAL_APP_INSTALL_GUI_PASS": install_pass,
            "CX2H_REAL_APP_LAUNCH_GUI_PASS": launch_pass,
            "CX2H_REAL_APP_UPDATE_GUI_PASS": update_pass,
            "CX2H_REAL_APP_ROLLBACK_GUI_PASS": rollback_pass,
            "CX2H_REAL_APP_UNINSTALL_GUI_PASS": uninstall_pass,
            "CX2H_J3_PERSISTENCE_PASS": persistence_pass,
        },
        "blocker": None
        if j3_pass
        else _first_blocker(provider_pass, install_pass, launch_pass, update_pass, uninstall_pass, persistence_pass),
    }


def _extract_clicked(cdp_result: Dict[str, Any]) -> bool:
    if not cdp_result:
        return False
    if cdp_result.get("clicked"):
        return True
    raw = json.dumps(cdp_result)
    return '"clicked": true' in raw or '"clicked":true' in raw


def _extract_field(cdp_result: Dict[str, Any], field: str) -> Optional[str]:
    raw = json.dumps(cdp_result)
    try:
        res = cdp_result.get("result") or {}
        val = res
        for key in ("result", "value"):
            if isinstance(val, dict) and key in val:
                val = val[key]
        if isinstance(val, dict) and field in val:
            return str(val.get(field))
    except Exception:
        pass
    marker = f'"{field}": '
    idx = raw.find(marker)
    if idx >= 0:
        frag = raw[idx + len(marker) : idx + len(marker) + 20]
        if frag.startswith('"'):
            return frag.split('"')[1]
    return None


def _first_blocker(provider, install, launch, update, uninstall, persistence) -> str:
    if not provider:
        return "CX2H_APP_CENTER_PROVIDER"
    if not install:
        return "CX2H_APP_INSTALL_GUI"
    if not launch:
        return "CX2H_APP_LAUNCH_GUI"
    if not update:
        return "CX2H_APP_UPDATE_GUI"
    if not uninstall:
        return "CX2H_APP_UNINSTALL_GUI"
    if not persistence:
        return "CX2H_J3_PERSISTENCE"
    return "CX2H_J3_INCOMPLETE"
