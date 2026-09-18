"""Host-side HTTPS + SMTP/IMAP providers for CX2H.3 (stoppable for genuine offline)."""

from __future__ import annotations

import json
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2h3.paths import cx2h3_lab_root, ensure_lab_tree, repo_root_from_here

HTTPS_PORT = 18443
SMTP_PORT = 1587
IMAP_PORT = 1143
HTTPS_ROOT = Path("/tmp/cx2h3-https")
MAIL_ROOT = Path("/tmp/cx2h3-mail")
GUEST_HOST = "10.0.2.2"  # QEMU SLIRP gateway to host
HTTPS_HOSTNAME = "cx2h3.test"


def _openssl() -> str:
    return shutil.which("openssl") or "openssl"


def ensure_tls_materials(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    https = lab / "https"
    https.mkdir(parents=True, exist_ok=True)
    ca_key = https / "ca.key"
    ca_crt = https / "ca.crt"
    server_key = https / "server.key"
    server_crt = https / "server.crt"
    result: Dict[str, Any] = {"ok": False, "ca_crt": str(ca_crt), "server_crt": str(server_crt)}
    openssl = _openssl()
    if not ca_key.is_file() or not ca_crt.is_file():
        subprocess.run(
            [openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes", "-keyout", str(ca_key),
             "-out", str(ca_crt), "-days", "3650", "-subj", "/CN=CX2H3 Lab CA"],
            check=True, capture_output=True, text=True,
        )
    if not server_key.is_file() or not server_crt.is_file():
        csr = https / "server.csr"
        conf = https / "server.cnf"
        conf.write_text(
            f"""[req]
distinguished_name=req_distinguished_name
req_extensions=v3_req
prompt=no
[req_distinguished_name]
CN={HTTPS_HOSTNAME}
[v3_req]
subjectAltName=@alt_names
[alt_names]
DNS.1={HTTPS_HOSTNAME}
DNS.2=localhost
IP.1=127.0.0.1
IP.2=10.0.2.2
"""
        )
        subprocess.run(
            [openssl, "req", "-new", "-newkey", "rsa:2048", "-nodes", "-keyout", str(server_key),
             "-out", str(csr), "-config", str(conf)],
            check=True, capture_output=True, text=True,
        )
        subprocess.run(
            [openssl, "x509", "-req", "-in", str(csr), "-CA", str(ca_crt), "-CAkey", str(ca_key),
             "-CAcreateserial", "-out", str(server_crt), "-days", "825", "-extensions", "v3_req",
             "-extfile", str(conf)],
            check=True, capture_output=True, text=True,
        )
    result["ok"] = ca_crt.is_file() and server_crt.is_file() and server_key.is_file()
    result["ca_fingerprint"] = subprocess.run(
        [openssl, "x509", "-in", str(ca_crt), "-noout", "-fingerprint", "-sha256"],
        capture_output=True, text=True,
    ).stdout.strip()
    return result


def _pidfile_alive(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        pid = int(path.read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def start_https(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    tls = ensure_tls_materials(repo)
    if not tls.get("ok"):
        return {"ok": False, "blocker": "CX2H3_TLS_MATERIALS", "tls": tls}
    HTTPS_ROOT.mkdir(parents=True, exist_ok=True)
    script = lab / "scripts" / "cx2h3_host_https.py"
    env = os.environ.copy()
    env.update(
        {
            "CX2H3_HTTPS_BIND": "0.0.0.0",
            "CX2H3_HTTPS_PORT": str(HTTPS_PORT),
            "CX2H3_HTTPS_ROOT": str(HTTPS_ROOT),
            "CX2H3_HTTPS_CERT": str(lab / "https" / "server.crt"),
            "CX2H3_HTTPS_KEY": str(lab / "https" / "server.key"),
        }
    )
    if _pidfile_alive(HTTPS_ROOT / "server.pid"):
        return {"ok": True, "reused": True, "port": HTTPS_PORT, "tls": tls, "url": f"https://{HTTPS_HOSTNAME}:{HTTPS_PORT}/"}
    log = HTTPS_ROOT / "server.stdout.log"
    proc = subprocess.Popen(
        ["python3", str(script)],
        env=env,
        stdout=log.open("w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.time() + 15
    while time.time() < deadline:
        if (HTTPS_ROOT / "manifest.json").is_file() and _pidfile_alive(HTTPS_ROOT / "server.pid"):
            break
        time.sleep(0.3)
    ok = _pidfile_alive(HTTPS_ROOT / "server.pid")
    man = {}
    if (HTTPS_ROOT / "manifest.json").is_file():
        man = json.loads((HTTPS_ROOT / "manifest.json").read_text())
    return {
        "ok": ok,
        "pid": proc.pid,
        "port": HTTPS_PORT,
        "bind": "0.0.0.0",
        "guest_url": f"https://{HTTPS_HOSTNAME}:{HTTPS_PORT}/",
        "guest_host": GUEST_HOST,
        "hostname": HTTPS_HOSTNAME,
        "tls": tls,
        "manifest": man,
        "ignore_certificate_errors": False,
        "blocker": None if ok else "CX2H3_HTTPS_START_FAILED",
    }


def start_mail(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    MAIL_ROOT.mkdir(parents=True, exist_ok=True)
    script = lab / "scripts" / "cx2h3_host_mail.py"
    env = os.environ.copy()
    env.update(
        {
            "CX2H3_MAIL_BIND": "0.0.0.0",
            "CX2H3_SMTP_PORT": str(SMTP_PORT),
            "CX2H3_IMAP_PORT": str(IMAP_PORT),
            "CX2H3_MAIL_ROOT": str(MAIL_ROOT),
        }
    )
    if _pidfile_alive(MAIL_ROOT / "server.pid"):
        return {
            "ok": True,
            "reused": True,
            "smtp_port": SMTP_PORT,
            "imap_port": IMAP_PORT,
            "guest_host": GUEST_HOST,
            "accounts": ["sender@cx2h3.test", "recipient@cx2h3.test"],
        }
    log = MAIL_ROOT / "server.stdout.log"
    proc = subprocess.Popen(
        ["python3", str(script)],
        env=env,
        stdout=log.open("w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.time() + 15
    while time.time() < deadline:
        if _pidfile_alive(MAIL_ROOT / "server.pid"):
            break
        time.sleep(0.3)
    ok = _pidfile_alive(MAIL_ROOT / "server.pid")
    return {
        "ok": ok,
        "pid": proc.pid,
        "smtp_port": SMTP_PORT,
        "imap_port": IMAP_PORT,
        "guest_host": GUEST_HOST,
        "accounts": {
            "sender": {"email": "sender@cx2h3.test", "password": "cx2h3-sender-pass"},
            "recipient": {"email": "recipient@cx2h3.test", "password": "cx2h3-recipient-pass"},
        },
        "json_fixture": False,
        "blocker": None if ok else "CX2H3_MAIL_START_FAILED",
    }


def stop_https() -> Dict[str, Any]:
    return _stop_pidfile(HTTPS_ROOT / "server.pid", "https")


def stop_mail() -> Dict[str, Any]:
    return _stop_pidfile(MAIL_ROOT / "server.pid", "mail")


def stop_smtp_only() -> Dict[str, Any]:
    """Controlled failure: stop entire mail stack then restart IMAP-only is complex;
    instead signal mail server to pause SMTP by stopping whole mail and noting mode.
    For harness: kill mail, start imap-only stub — simplified: stop mail (both)."""
    return stop_mail()


def _stop_pidfile(pidfile: Path, label: str) -> Dict[str, Any]:
    if not pidfile.is_file():
        return {"ok": True, "label": label, "already_stopped": True}
    try:
        pid = int(pidfile.read_text().strip())
        os.kill(pid, signal.SIGTERM)
        deadline = time.time() + 10
        while time.time() < deadline:
            try:
                os.kill(pid, 0)
                time.sleep(0.2)
            except OSError:
                break
        try:
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        pidfile.unlink(missing_ok=True)
        return {"ok": True, "label": label, "stopped_pid": pid}
    except Exception as e:
        return {"ok": False, "label": label, "error": str(e)}


def https_stats() -> Dict[str, Any]:
    try:
        import urllib.request

        ctx = __import__("ssl").create_default_context()
        # local verify with our CA when possible — for host stats use insecure to localhost IP
        ctx.check_hostname = False
        ctx.verify_mode = __import__("ssl").CERT_NONE
        with urllib.request.urlopen(f"https://127.0.0.1:{HTTPS_PORT}/api/stats", context=ctx, timeout=5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}


def mail_smtp_accepts() -> list:
    path = MAIL_ROOT / "smtp_accepts.json"
    if not path.is_file():
        return []
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def probe_ports_reachable(host: str = "127.0.0.1") -> Dict[str, Any]:
    import socket

    out = {}
    for name, port in (("https", HTTPS_PORT), ("smtp", SMTP_PORT), ("imap", IMAP_PORT)):
        s = socket.socket()
        s.settimeout(2)
        try:
            s.connect((host, port))
            out[name] = True
        except OSError:
            out[name] = False
        finally:
            s.close()
    return out
