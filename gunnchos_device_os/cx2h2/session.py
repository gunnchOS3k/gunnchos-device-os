"""CX2H.2 session helpers — shell prereq reuse + vault provider deploy."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any, Dict, Tuple

from gunnchos_device_os.cx2h.portals import SESSION_ENV, repair_and_prove_portals
from gunnchos_device_os.cx2h.session import re_prove_shell_prereqs as cx2h_re_prove
from gunnchos_device_os.cx2h2.paths import cx2h2_lab_root, ensure_lab_tree
from gunnchos_device_os.cx2h2.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, scp_to_guest, ssh_exec


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2h2_lab_root(repo)
    # Prefer runtime-copied key
    for candidate in (
        lab / "ssh" / "id_ed25519",
        Path("/tmp/cx2h2-graphical/ssh/id_ed25519"),
        repo / "os_build" / "cx2h_linux_lab" / "ssh" / "id_ed25519",
        repo / "os_build" / "cx2g_linux_lab" / "ssh" / "id_ed25519",
    ):
        if candidate.is_file():
            return candidate, DEFAULT_SSH_PORT
    key = Path(ensure_ssh_keypair(lab)["private"])
    return key, DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 180):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def re_prove_shell_and_j3_tokens(repo: Path, monitor: Path, captures: Path) -> Dict[str, Any]:
    """Re-prove CX2G shell + assert prior J3 digital pass tokens from evidence (no redo)."""
    ensure_lab_tree(repo)
    # Reuse CX2H shell prereq path (same guest stack)
    # Point keys: cx2h session uses cx2h lab keys — ensure symlink/copy into cx2h2 already done by qemu start
    # Temporarily ensure cx2h lab ssh exists for cx2h_re_prove
    from gunnchos_device_os.cx2h.paths import cx2h_lab_root

    hlab = cx2h_lab_root(repo)
    hlab_ssh = hlab / "ssh"
    hlab_ssh.mkdir(parents=True, exist_ok=True)
    src_key, _ = _key_port(repo)
    for name in ("id_ed25519", "id_ed25519.pub"):
        src = src_key.parent / name
        dst = hlab_ssh / name
        if src.is_file() and not dst.is_file():
            try:
                dst.write_bytes(src.read_bytes())
                if name == "id_ed25519":
                    dst.chmod(0o600)
            except OSError:
                pass

    prereq = cx2h_re_prove(repo, monitor, captures)
    portals = repair_and_prove_portals(repo)

    # Load prior J3 class from CX2H evidence (authoritative 1B truth) — do not redo Flatpak lifecycle
    j3_class = "BLOCKED"
    prior = repo / "artifacts" / "complete_experience" / "cx2h" / "CX2H_TOKENS.json"
    if prior.is_file():
        import json

        try:
            tok = json.loads(prior.read_text())
            j3_class = tok.get("J3_CLASS") or "BLOCKED"
        except Exception:
            pass

    ok = bool(
        prereq.get("CX2H_SHELL_PREREQ_PASS")
        and portals.get("CX2H_XDG_PORTAL_SESSION_PASS")
        and j3_class == "REAL_USER_JOURNEY_DIGITAL_PASS"
    )
    return {
        "ok": ok,
        "prereq": prereq,
        "portals": portals,
        "J3_CLASS": j3_class,
        "CX2H_SHELL_PREREQ_PASS": bool(prereq.get("CX2H_SHELL_PREREQ_PASS")),
        "CX2H_CHROMIUM_RUNTIME_PASS": bool(prereq.get("CX2H_CHROMIUM_RUNTIME_PASS")),
        "CX2H_WAYLAND_SURFACE_PASS": bool(prereq.get("CX2H_WAYLAND_SURFACE_PASS")),
        "CX2H_GUNNCH_SHELL_RENDER_PASS": bool(prereq.get("CX2H_GUNNCH_SHELL_RENDER_PASS")),
        "CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS": bool(prereq.get("CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS")),
        "CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS": bool(prereq.get("CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS")),
        "CX2H_REAL_APP_CENTER_WINDOW": bool(prereq.get("CX2H_REAL_APP_CENTER_WINDOW")),
        "CX2H_XDG_PORTAL_SESSION_PASS": bool(portals.get("CX2H_XDG_PORTAL_SESSION_PASS")),
        "blocker": None
        if ok
        else (
            prereq.get("blocker")
            or portals.get("blocker")
            or ("CX2H2_J3_REGRESSION" if j3_class != "REAL_USER_JOURNEY_DIGITAL_PASS" else "CX2H2_SHELL_PREREQ")
        ),
        "SESSION_ENV_note": SESSION_ENV[:80],
    }


def deploy_vault_provider(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    script = lab / "scripts" / "cx2h2_vault_provider.py"
    if not script.is_file():
        return {"ok": False, "blocker": "CX2H2_VAULT_PROVIDER_SCRIPT_MISSING"}
    _ssh(repo, "sudo mkdir -p /var/lib/cx2h2/bin /var/lib/cx2h2/vault /var/spool/cx2h2-print; "
         "sudo chown -R gunnchos:gunnchos /var/lib/cx2h2 /var/spool/cx2h2-print", timeout=60)
    key, port = _key_port(repo)
    scp_to_guest(key, port, script, "/var/lib/cx2h2/bin/cx2h2_vault_provider.py")
    seed = lab / "scripts" / "cx2h2_seed_lo_accel.py"
    if seed.is_file():
        scp_to_guest(key, port, seed, "/var/lib/cx2h2/bin/cx2h2_seed_lo_accel.py")
    export_pdf = lab / "scripts" / "cx2h2_lo_export_pdf.py"
    if export_pdf.is_file():
        scp_to_guest(key, port, export_pdf, "/var/lib/cx2h2/bin/cx2h2_lo_export_pdf.py")
    unit = """[Unit]
Description=CX2H2 Vault Care Writer Print Provider
After=network.target

[Service]
Type=simple
User=gunnchos
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
Environment=CX2H2_VAULT_ROOT=/var/lib/cx2h2/vault
Environment=CX2H2_PRINT_SPOOL=/var/spool/cx2h2-print
Environment=HOME=/home/gunnchos
ExecStart=/usr/bin/python3 /var/lib/cx2h2/bin/cx2h2_vault_provider.py
Restart=on-failure

[Install]
WantedBy=default.target
"""
    _ssh(
        repo,
        "cat > /tmp/cx2h2-vault.service <<'EOF'\n"
        + unit
        + "EOF\n"
        "sudo mv /tmp/cx2h2-vault.service /etc/systemd/system/cx2h2-vault.service; "
        "sudo systemctl daemon-reload; "
        "sudo systemctl restart cx2h2-vault.service; "
        "sleep 1; "
        "curl -sf http://127.0.0.1:8767/api/health || true",
        timeout=90,
    )
    health = _ssh(repo, "curl -sf http://127.0.0.1:8767/api/health", timeout=30)
    ok = health.returncode == 0 and "cx2h2-vault" in (health.stdout or "")
    return {"ok": ok, "health": (health.stdout or "")[-500:], "blocker": None if ok else "CX2H2_VAULT_PROVIDER_API"}


def restart_shell_for_persistence(repo: Path) -> Dict[str, Any]:
    from gunnchos_device_os.cx2h.session import restart_shell_for_persistence as _r

    return _r(repo)


def provider_api(repo: Path, path: str, method: str = "GET", body: str = "") -> Dict[str, Any]:
    import json
    import shlex

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
        return {"ok": False, "raw": (r.stdout or "")[-2000:], "stderr": (r.stderr or "")[-500:]}
