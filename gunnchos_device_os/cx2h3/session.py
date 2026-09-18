"""CX2H.3 session helpers — prereq rebind + provider deploy."""

from __future__ import annotations

import json
import shlex
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from gunnchos_device_os.cx2h3.host_providers import ensure_tls_materials
from gunnchos_device_os.cx2h3.paths import cx2h3_lab_root, ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h3.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, scp_to_guest, ssh_exec


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2h3_lab_root(repo)
    for candidate in (
        lab / "ssh" / "id_ed25519",
        Path("/tmp/cx2h3-graphical/ssh/id_ed25519"),
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


def prerequisite_rebind(repo: Path, monitor: Path | None = None, captures: Path | None = None) -> Dict[str, Any]:
    """Compact provenance check — retain J1/J3/J7; ensure live Weston/shell when monitor given."""
    ensure_lab_tree(repo)
    out: Dict[str, Any] = {"ok": False, "CX2H3_PREREQUISITE_PASS": False}
    cx2h2 = repo / "artifacts" / "complete_experience" / "cx2h2" / "CX2H2_TOKENS.json"
    cx2h = repo / "artifacts" / "complete_experience" / "cx2h" / "CX2H_TOKENS.json"
    tok2: Dict[str, Any] = {}
    tokh: Dict[str, Any] = {}
    if cx2h2.is_file():
        tok2 = json.loads(cx2h2.read_text())
    if cx2h.is_file():
        tokh = json.loads(cx2h.read_text())
    j1 = tok2.get("J1_CLASS") == "REAL_USER_JOURNEY_DIGITAL_PASS"
    j7 = tok2.get("J7_CLASS") == "REAL_USER_JOURNEY_DIGITAL_PASS"
    j3 = (tok2.get("J3_CLASS") or tokh.get("J3_CLASS")) == "REAL_USER_JOURNEY_DIGITAL_PASS"
    shell = bool(tok2.get("CX2H_SHELL_PREREQ_PASS") or tokh.get("CX2H_SHELL_PREREQ_PASS"))
    portals = bool(tok2.get("CX2H_XDG_PORTAL_SESSION_PASS") or tokh.get("CX2H_XDG_PORTAL_SESSION_PASS"))
    writer = bool(tok2.get("CX2H2_REAL_WRITER_GUI_PASS"))
    vault = bool(tok2.get("CX2H2_REAL_VAULT_FILE_PASS"))
    live_shell: Dict[str, Any] = {}
    if monitor is not None:
        from gunnchos_device_os.cx2h.portals import repair_and_prove_portals
        from gunnchos_device_os.cx2h.session import re_prove_shell_prereqs

        caps = captures or Path("/tmp/cx2h3-graphical/captures")
        caps.mkdir(parents=True, exist_ok=True)
        live_shell = re_prove_shell_prereqs(repo, monitor, caps)
        live_portals = repair_and_prove_portals(repo)
        shell = bool(live_shell.get("CX2H_SHELL_PREREQ_PASS"))
        portals = bool(live_portals.get("CX2H_XDG_PORTAL_SESSION_PASS"))
        out["live_shell"] = {k: live_shell.get(k) for k in live_shell if str(k).startswith("CX2")}
        out["live_portals"] = {
            "CX2H_XDG_PORTAL_SESSION_PASS": live_portals.get("CX2H_XDG_PORTAL_SESSION_PASS")
        }
    # Live guest probe
    uname = _ssh(repo, "uname -a", timeout=30)
    weston = _ssh(repo, "pgrep -af weston | head -3", timeout=30)
    shell_p = _ssh(repo, "pgrep -af 'chromium.*8765|gunnch' | head -5", timeout=30)
    live_linux = uname.returncode == 0 and "Linux" in (uname.stdout or "")
    ok = bool(j1 and j3 and j7 and shell and portals and writer and vault and live_linux)
    out.update(
        {
            "ok": ok,
            "CX2H3_PREREQUISITE_PASS": ok,
            "J1_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j1 else "BLOCKED",
            "J3_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j3 else "BLOCKED",
            "J7_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS" if j7 else "BLOCKED",
            "CX2H_SHELL_PREREQ_PASS": shell,
            "CX2H_XDG_PORTAL_SESSION_PASS": portals,
            "CX2H2_REAL_WRITER_GUI_PASS": writer,
            "CX2H2_REAL_VAULT_FILE_PASS": vault,
            "live": {
                "uname": (uname.stdout or "")[:200],
                "weston": (weston.stdout or "")[:300],
                "shell": (shell_p.stdout or "")[:400],
            },
            "sources": {"cx2h2_tokens": str(cx2h2), "cx2h_tokens": str(cx2h)},
            "blocker": None if ok else "CX2H3_PREREQUISITE_REGRESSION",
        }
    )
    return out


def deploy_cx2h3_provider(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    scripts = [
        lab / "scripts" / "cx2h3_provider.py",
        lab / "scripts" / "cx2h3_cdp_eval.py",
    ]
    for s in scripts:
        if not s.is_file():
            return {"ok": False, "blocker": f"CX2H3_SCRIPT_MISSING:{s.name}"}
    # Also deploy cx2h2 vault provider for Writer/Vault continuity
    v2 = repo / "os_build" / "cx2h2_linux_lab" / "scripts" / "cx2h2_vault_provider.py"
    _ssh(
        repo,
        "sudo mkdir -p /var/lib/cx2h3/bin /var/lib/cx2h3/mail_queue /var/lib/cx2h2/vault/files; "
        "sudo chown -R gunnchos:gunnchos /var/lib/cx2h3 /var/lib/cx2h2",
        timeout=60,
    )
    key, port = _key_port(repo)
    for s in scripts:
        scp_to_guest(key, port, s, f"/var/lib/cx2h3/bin/{s.name}")
    if v2.is_file():
        scp_to_guest(key, port, v2, "/var/lib/cx2h2/bin/cx2h2_vault_provider.py")
    tls = ensure_tls_materials(repo)
    ca = lab / "https" / "ca.crt"
    if ca.is_file():
        scp_to_guest(key, port, ca, "/tmp/cx2h3-lab-ca.crt")
    # packages
    pkgs = _ssh(
        repo,
        "sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "
        "thunderbird libnss3-tools curl ca-certificates 2>/dev/null | tail -5; "
        "command -v thunderbird; command -v chromium; command -v certutil",
        timeout=600,
    )
    unit = """[Unit]
Description=CX2H3 Browser Mail Offline Provider
After=network.target

[Service]
Type=simple
User=gunnchos
Environment=XDG_RUNTIME_DIR=/run/cx2g-wayland
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2g-wayland/bus
Environment=HOME=/home/gunnchos
Environment=CX2H3_ROOT=/var/lib/cx2h3
Environment=CX2H3_VAULT_ROOT=/var/lib/cx2h2/vault/files
Environment=CX2H3_HTTPS_URL=https://cx2h3.test:18443/
Environment=CX2H3_SMTP_HOST=10.0.2.2
Environment=CX2H3_SMTP_PORT=1587
Environment=CX2H3_IMAP_HOST=10.0.2.2
Environment=CX2H3_IMAP_PORT=1143
ExecStart=/usr/bin/python3 /var/lib/cx2h3/bin/cx2h3_provider.py
Restart=on-failure

[Install]
WantedBy=default.target
"""
    _ssh(
        repo,
        "cat > /tmp/cx2h3.service <<'EOF'\n"
        + unit
        + "EOF\n"
        "sudo mv /tmp/cx2h3.service /etc/systemd/system/cx2h3.service; "
        "sudo systemctl daemon-reload; "
        "sudo systemctl restart cx2h3.service; "
        "sleep 1; curl -sf http://127.0.0.1:8768/api/health || true",
        timeout=90,
    )
    # ensure vault provider too
    _ssh(
        repo,
        "sudo systemctl restart cx2h2-vault.service 2>/dev/null || true; "
        "sleep 1; curl -sf http://127.0.0.1:8767/api/health || true",
        timeout=60,
    )
    if ca.is_file():
        _ssh(
            repo,
            "curl -sf -X POST http://127.0.0.1:8768/api/ca/install "
            "-H 'Content-Type: application/json' "
            "-d '{\"ca_path\":\"/tmp/cx2h3-lab-ca.crt\"}'",
            timeout=90,
        )
    health = _ssh(repo, "curl -sf http://127.0.0.1:8768/api/health", timeout=30)
    ok = health.returncode == 0 and "cx2h3-provider" in (health.stdout or "")
    return {
        "ok": ok,
        "health": (health.stdout or "")[-500:],
        "pkgs": (pkgs.stdout or "")[-800:],
        "tls": tls,
        "blocker": None if ok else "CX2H3_PROVIDER_API",
    }


def provider_api(repo: Path, path: str, method: str = "GET", body: str = "") -> Dict[str, Any]:
    if method.upper() == "GET":
        cmd = f"curl -sf http://127.0.0.1:8768{path}"
    else:
        cmd = (
            f"curl -sf -X {method} http://127.0.0.1:8768{path} "
            f"-H 'Content-Type: application/json' -d {shlex.quote(body)}"
        )
    r = _ssh(repo, cmd, timeout=180)
    try:
        return json.loads((r.stdout or "").strip() or "{}")
    except Exception:
        return {"ok": False, "raw": (r.stdout or "")[-2000:], "stderr": (r.stderr or "")[-500:]}


def vault2_api(repo: Path, path: str, method: str = "GET", body: str = "") -> Dict[str, Any]:
    if method.upper() == "GET":
        cmd = f"curl -sf http://127.0.0.1:8767{path}"
    else:
        cmd = (
            f"curl -sf -X {method} http://127.0.0.1:8767{path} "
            f"-H 'Content-Type: application/json' -d {shlex.quote(body)}"
        )
    r = _ssh(repo, cmd, timeout=120)
    try:
        return json.loads((r.stdout or "").strip() or "{}")
    except Exception:
        return {"ok": False, "raw": (r.stdout or "")[-2000:]}


def restart_shell_for_persistence(repo: Path) -> Dict[str, Any]:
    from gunnchos_device_os.cx2h.session import restart_shell_for_persistence as _r

    return _r(repo)
