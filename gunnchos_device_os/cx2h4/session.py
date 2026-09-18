"""CX2H.4 session — journey rebind + provider deploy."""

from __future__ import annotations

import json
import shlex
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from gunnchos_device_os.cx2h4.paths import cx2h4_lab_root, ensure_lab_tree, repo_root_from_here
from gunnchos_device_os.cx2h4.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, scp_to_guest, ssh_exec


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2h4_lab_root(repo)
    for candidate in (
        Path("/tmp/cx2h4-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h3-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h2-graphical/ssh/id_ed25519"),
        lab / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2h3_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2h2_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2h_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2g_linux_lab" / "ssh" / "id_ed25519",
    ):
        if candidate.is_file():
            return candidate, DEFAULT_SSH_PORT
    return Path(ensure_ssh_keypair(lab)["private"]), DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 180):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def ensure_accepted_ssh_key(repo: Path) -> Path:
    """Point lab ssh dirs at the guest-accepted CX key (never invent a new key)."""
    good = None
    for candidate in (
        Path("/tmp/cx2h3-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h4-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2h2-graphical/ssh/id_ed25519"),
        Path("/tmp/cx2g-graphical/ssh/id_ed25519"),
    ):
        if candidate.is_file():
            good = candidate
            break
    if good is None:
        # Fall back to any existing lab key that works — do not generate here.
        for lab in ("cx2h3_linux_lab", "cx2h2_linux_lab", "cx2h_linux_lab", "cx2g_linux_lab"):
            p = repo / "os_build" / lab / "ssh" / "id_ed25519"
            if p.is_file():
                good = p
                break
    if good is None:
        raise FileNotFoundError("CX2H4_ACCEPTED_SSH_KEY_MISSING")
    pub = Path(str(good) + ".pub")
    if not pub.is_file():
        pub = good.with_name(good.name + ".pub")
    for lab in ("cx2h4_linux_lab", "cx2h3_linux_lab", "cx2h2_linux_lab", "cx2h_linux_lab", "cx2g_linux_lab"):
        dest_dir = repo / "os_build" / lab / "ssh"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "id_ed25519"
        # Replace mismatched generated keys with symlink to accepted key.
        try:
            if dest.is_symlink() or not dest.exists() or dest.resolve() != good.resolve():
                if dest.exists() or dest.is_symlink():
                    dest.unlink()
                dest.symlink_to(good)
            dest_pub = dest_dir / "id_ed25519.pub"
            if pub.is_file() and (dest_pub.is_symlink() or not dest_pub.exists() or dest_pub.resolve() != pub.resolve()):
                if dest_pub.exists() or dest_pub.is_symlink():
                    dest_pub.unlink()
                dest_pub.symlink_to(pub)
        except OSError:
            continue
    return good


def journey_provenance_rebind(repo: Path, monitor: Path | None = None, captures: Path | None = None) -> Dict[str, Any]:
    """Rebind J1/J2/J3/J5/J7 DIGITAL_PASS; keep J6 HUMAN_VALIDATION_PENDING."""
    ensure_lab_tree(repo)
    try:
        ensure_accepted_ssh_key(repo)
    except FileNotFoundError as exc:
        return {
            "ok": False,
            "CX2H4_JOURNEY_REBIND_PASS": False,
            "blocker": str(exc),
        }
    out: Dict[str, Any] = {"ok": False, "CX2H4_JOURNEY_REBIND_PASS": False}
    sources = {
        "cx2h3": repo / "artifacts" / "complete_experience" / "cx2h3" / "CX2H3_TOKENS.json",
        "cx2h2": repo / "artifacts" / "complete_experience" / "cx2h2" / "CX2H2_TOKENS.json",
        "cx2h": repo / "artifacts" / "complete_experience" / "cx2h" / "CX2H_TOKENS.json",
    }
    toks: Dict[str, Dict[str, Any]] = {}
    for name, path in sources.items():
        if path.is_file():
            toks[name] = json.loads(path.read_text())
        else:
            toks[name] = {}

    def cls(*keys: str) -> str:
        for t in (toks["cx2h3"], toks["cx2h2"], toks["cx2h"]):
            for k in keys:
                v = t.get(k)
                if v:
                    return str(v)
        return "BLOCKED"

    j1 = cls("J1_CLASS")
    j2 = cls("J2_CLASS")
    j3 = cls("J3_CLASS")
    j5 = cls("J5_CLASS")
    j7 = cls("J7_CLASS")
    j6 = "HUMAN_VALIDATION_PENDING"

    required = "REAL_USER_JOURNEY_DIGITAL_PASS"
    retained = all(x == required for x in (j1, j2, j3, j5, j7)) and j6 == "HUMAN_VALIDATION_PENDING"

    # Artifact existence checks (fail-closed if missing)
    artifact_checks = {
        "j1": (repo / "artifacts/complete_experience/cx2h2/CX2H2_J1_JOURNEY.json").is_file(),
        "j7": (repo / "artifacts/complete_experience/cx2h2/CX2H2_J7_JOURNEY.json").is_file(),
        "j3": (repo / "artifacts/complete_experience/cx2h/CX2H_TOKENS.json").is_file(),
        "j2": (repo / "artifacts/complete_experience/cx2h3/CX2H3_J2_JOURNEY.json").is_file(),
        "j5": (repo / "artifacts/complete_experience/cx2h3/CX2H3_J5_JOURNEY.json").is_file(),
    }

    live: Dict[str, Any] = {}
    live_ok = True
    if monitor is not None:
        from gunnchos_device_os.cx2h.portals import repair_and_prove_portals
        from gunnchos_device_os.cx2h.session import re_prove_shell_prereqs

        caps = captures or Path("/tmp/cx2h4-graphical/captures")
        caps.mkdir(parents=True, exist_ok=True)
        try:
            live_shell = re_prove_shell_prereqs(repo, monitor, caps)
        except Exception as exc:
            live_shell = {"ok": False, "CX2H_SHELL_PREREQ_PASS": False, "blocker": f"re_prove_exception:{exc}"}
        try:
            live_portals = repair_and_prove_portals(repo)
        except Exception as exc:
            live_portals = {"CX2H_XDG_PORTAL_SESSION_PASS": False, "blocker": f"portals_exception:{exc}"}
        live = {
            "shell": {k: live_shell.get(k) for k in live_shell if str(k).startswith("CX2") or k in ("ok", "blocker")},
            "portals": {"CX2H_XDG_PORTAL_SESSION_PASS": live_portals.get("CX2H_XDG_PORTAL_SESSION_PASS")},
        }
        live_ok = bool(live_shell.get("CX2H_SHELL_PREREQ_PASS") and live_portals.get("CX2H_XDG_PORTAL_SESSION_PASS"))

    uname = _ssh(repo, "uname -a", timeout=30)
    weston = _ssh(repo, "pgrep -af weston | head -3", timeout=30)
    live_linux = uname.returncode == 0 and "Linux" in (uname.stdout or "")

    ok = bool(retained and all(artifact_checks.values()) and live_linux and live_ok)
    out.update(
        {
            "ok": ok,
            "CX2H4_JOURNEY_REBIND_PASS": ok,
            "J1_CLASS": j1 if j1 == required else "BLOCKED",
            "J2_CLASS": j2 if j2 == required else "BLOCKED",
            "J3_CLASS": j3 if j3 == required else "BLOCKED",
            "J5_CLASS": j5 if j5 == required else "BLOCKED",
            "J7_CLASS": j7 if j7 == required else "BLOCKED",
            "J6_CLASS": j6,
            "J4_CLASS_PRIOR": toks["cx2h3"].get("J4_CLASS") or toks["cx2h2"].get("J4_CLASS") or "BLOCKED",
            "artifact_checks": artifact_checks,
            "live": {
                "uname": (uname.stdout or "")[:200],
                "weston": (weston.stdout or "")[:300],
                **live,
            },
            "branch_tip_expected": "070923b010c393ab4395a72120840b7cfd355ec3",
            "sources": {k: str(v) for k, v in sources.items()},
            "blocker": None if ok else "CX2H4_JOURNEY_REBIND_REGRESSION",
        }
    )
    return out


def deploy_cx2h4_provider(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    script = lab / "scripts" / "cx2h4_provider.py"
    if not script.is_file():
        return {"ok": False, "blocker": "CX2H4_SCRIPT_MISSING"}
    _ssh(
        repo,
        "sudo mkdir -p /var/lib/cx2h4/bin /var/lib/cx2h4/logs /var/lib/cx2h2/vault/files; "
        "sudo chown -R gunnchos:gunnchos /var/lib/cx2h4 /var/lib/cx2h2",
        timeout=60,
    )
    key, port = _key_port(repo)
    scp_to_guest(key, port, script, "/var/lib/cx2h4/bin/cx2h4_provider.py")
    # Also ensure cx2h3 browser helpers remain available for CDP reuse
    cdp = repo / "os_build" / "cx2h3_linux_lab" / "scripts" / "cx2h3_cdp_eval.py"
    if cdp.is_file():
        scp_to_guest(key, port, cdp, "/var/lib/cx2h4/bin/cx2h3_cdp_eval.py")
        scp_to_guest(key, port, cdp, "/var/lib/cx2h3/bin/cx2h3_cdp_eval.py")

    unit = """[Unit]
Description=CX2H4 P0 Closure Provider
After=network.target

[Service]
Type=simple
User=gunnchos
Environment=XDG_RUNTIME_DIR=/run/cx2g-wayland
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2g-wayland/bus
Environment=HOME=/home/gunnchos
Environment=CX2H4_ROOT=/var/lib/cx2h4
Environment=CX2H4_VAULT_ROOT=/var/lib/cx2h2/vault/files
ExecStart=/usr/bin/python3 /var/lib/cx2h4/bin/cx2h4_provider.py
Restart=on-failure

[Install]
WantedBy=default.target
"""
    _ssh(
        repo,
        "cat > /tmp/cx2h4.service <<'EOF'\n"
        + unit
        + "EOF\n"
        "sudo mv /tmp/cx2h4.service /etc/systemd/system/cx2h4.service; "
        "sudo systemctl daemon-reload; "
        "sudo systemctl restart cx2h4.service; "
        # Ensure prior providers still up for Writer/browser continuity
        "sudo systemctl restart cx2h3.service 2>/dev/null || true; "
        "sudo systemctl restart cx2h2-vault.service 2>/dev/null || true; "
        "sleep 2; curl -sf http://127.0.0.1:8769/api/health || true",
        timeout=120,
    )
    # Ensure calc/impress packages present (Writer already used)
    pkgs = _ssh(
        repo,
        "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
        "libreoffice-calc libreoffice-impress 2>/dev/null | tail -3; "
        "libreoffice --version; dpkg -l | grep -E 'libreoffice-(calc|impress|writer)' | awk '{print $2,$3}'",
        timeout=600,
    )
    health = _ssh(repo, "curl -sf http://127.0.0.1:8769/api/health", timeout=30)
    ok = health.returncode == 0 and "cx2h4-provider" in (health.stdout or "")
    return {
        "ok": ok,
        "health": (health.stdout or "")[-400:],
        "pkgs": (pkgs.stdout or "")[-800:],
        "blocker": None if ok else "CX2H4_PROVIDER_API",
    }


def provider_api(repo: Path, path: str, method: str = "GET", body: str = "", *, timeout: int = 180) -> Dict[str, Any]:
    if method.upper() == "GET":
        cmd = f"curl -sf http://127.0.0.1:8769{path}"
    else:
        cmd = (
            f"curl -sf -X {method} http://127.0.0.1:8769{path} "
            f"-H 'Content-Type: application/json' -d {shlex.quote(body)}"
        )
    try:
        r = _ssh(repo, cmd, timeout=timeout)
    except Exception as exc:
        return {"ok": False, "error": f"ssh_timeout_or_error:{exc}"}
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {"ok": False, "error": "bad_json", "stdout": (r.stdout or "")[-500:], "stderr": (r.stderr or "")[-300:]}


def cdp_eval(repo: Path, expression: str, *, port: int = 9334) -> Dict[str, Any]:
    """CDP evaluate against CX2H4 chromium (9334) or fall back to shell chromium (9333)."""
    expr_q = shlex.quote(expression)
    # Prefer dedicated script with port override via env if available
    cmd = (
        f"python3 /var/lib/cx2h4/bin/cx2h3_cdp_eval.py {expr_q} 2>/dev/null || "
        f"python3 /var/lib/cx2h3/bin/cx2h3_cdp_eval.py {expr_q}"
    )
    # Patch: cx2h3_cdp_eval hardcodes 9333 — for 9334 use inline python
    if port != 9333:
        inline = f"""
import json,urllib.request
tabs=json.loads(urllib.request.urlopen('http://127.0.0.1:{port}/json/list',timeout=5).read())
print(json.dumps({{'ok':bool(tabs),'tabs':len(tabs),'title': (tabs[0].get('title') if tabs else None)}}))
"""
        r = _ssh(repo, f"python3 -c {shlex.quote(inline)}", timeout=30)
        try:
            meta = json.loads(r.stdout or "{}")
        except Exception:
            meta = {"ok": False}
        # Full evaluate via temporary port rewrite of script
        cmd = (
            f"python3 -c {shlex.quote(_cdp_eval_inline(expression, port))}"
        )
    r = _ssh(repo, cmd, timeout=60)
    try:
        return json.loads(r.stdout or "{}")
    except Exception:
        return {"ok": False, "raw": (r.stdout or "")[-500:]}


def _cdp_eval_inline(expression: str, port: int) -> str:
    # Compact CDP evaluate (same protocol as cx2h3_cdp_eval)
    return f"""
import base64,json,os,socket,struct,urllib.request
expr={expression!r}
tabs=json.loads(urllib.request.urlopen('http://127.0.0.1:{port}/json/list',timeout=5).read())
page=next((t for t in tabs if t.get('type')=='page' and t.get('webSocketDebuggerUrl')),None)
assert page
u=page['webSocketDebuggerUrl'].replace('ws://','')
hostport,path=u.split('/',1); host,port_s=hostport.split(':'); port=int(port_s); path='/'+path
key=base64.b64encode(os.urandom(16)).decode()
req=(f'GET {{path}} HTTP/1.1\\r\\nHost: {{hostport}}\\r\\nUpgrade: websocket\\r\\nConnection: Upgrade\\r\\nSec-WebSocket-Key: {{key}}\\r\\nSec-WebSocket-Version: 13\\r\\n\\r\\n').encode()
s=socket.create_connection((host,port),timeout=10); s.sendall(req); s.recv(4096)
def send(obj):
    data=json.dumps(obj).encode(); mask=os.urandom(4); ln=len(data)
    hdr=bytes([0x81,0x80|ln]) if ln<126 else bytes([0x81,0x80|126])+struct.pack('!H',ln)
    s.sendall(hdr+mask+bytes(b^mask[i%4] for i,b in enumerate(data)))
def recv():
    hdr=s.recv(2); ln=hdr[1]&0x7F
    if ln==126: ln=struct.unpack('!H',s.recv(2))[0]
    data=b''
    while len(data)<ln:
        data+=s.recv(ln-len(data))
    return data
send({{'id':1,'method':'Runtime.enable'}}); recv()
send({{'id':2,'method':'Runtime.evaluate','params':{{'expression':expr,'awaitPromise':True,'returnByValue':True}}}})
msg=json.loads(recv().decode())
print(json.dumps({{'ok':True,'result':msg.get('result',{{}}).get('result',{{}}).get('value')}}))
"""
