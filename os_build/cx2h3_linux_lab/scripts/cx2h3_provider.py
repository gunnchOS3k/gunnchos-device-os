#!/usr/bin/env python3
"""CX2H.3 guest provider — browser/mail/queue/vault bridge on 127.0.0.1:8768."""

from __future__ import annotations

import hashlib
import io
import json
import os
import shutil
import smtplib
import socket
import subprocess
import time
import uuid
import zipfile
from email import message_from_bytes
from email.message import EmailMessage
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(os.environ.get("CX2H3_ROOT", "/var/lib/cx2h3"))
VAULT = Path(os.environ.get("CX2H3_VAULT_ROOT", "/var/lib/cx2h2/vault/files"))
QUEUE = ROOT / "mail_queue"
SESSION_ENV = {
    # Prefer CX2G Weston runtime; fall back to user runtime (symlink may exist).
    "XDG_RUNTIME_DIR": "/run/cx2g-wayland"
    if Path("/run/cx2g-wayland/wayland-0").exists()
    else "/run/user/1000",
    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/cx2g-wayland/bus"
    if Path("/run/cx2g-wayland/bus").exists()
    else "unix:path=/run/user/1000/bus",
    "WAYLAND_DISPLAY": "wayland-0",
    "XDG_CURRENT_DESKTOP": "GNOME",
    "XDG_SESSION_TYPE": "wayland",
    "HOME": os.environ.get("HOME", "/home/gunnchos"),
}
STATE: Dict[str, Any] = {"browser": {}, "mail": {}, "queue": {}, "last": {}}
HTTPS_URL = os.environ.get("CX2H3_HTTPS_URL", "https://cx2h3.test:18443/")
SMTP_HOST = os.environ.get("CX2H3_SMTP_HOST", "10.0.2.2")
SMTP_PORT = int(os.environ.get("CX2H3_SMTP_PORT", "1587"))
IMAP_HOST = os.environ.get("CX2H3_IMAP_HOST", "10.0.2.2")
IMAP_PORT = int(os.environ.get("CX2H3_IMAP_PORT", "1143"))
SENDER = os.environ.get("CX2H3_SENDER", "sender@cx2h3.test")
SENDER_PW = os.environ.get("CX2H3_SENDER_PW", "cx2h3-sender-pass")
RECIPIENT = os.environ.get("CX2H3_RECIPIENT", "recipient@cx2h3.test")
RECIPIENT_PW = os.environ.get("CX2H3_RECIPIENT_PW", "cx2h3-recipient-pass")


def _env() -> Dict[str, str]:
    e = os.environ.copy()
    env = dict(SESSION_ENV)
    if Path("/run/cx2g-wayland/wayland-0").exists():
        env["XDG_RUNTIME_DIR"] = "/run/cx2g-wayland"
        if Path("/run/cx2g-wayland/bus").exists():
            env["DBUS_SESSION_BUS_ADDRESS"] = "unix:path=/run/cx2g-wayland/bus"
    e.update(env)
    return e


def _run(cmd: List[str], timeout: int = 120) -> Dict[str, Any]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_env())
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[-4000:],
        "stderr": (p.stderr or "")[-2000:],
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_dirs() -> None:
    for pth in (
        ROOT,
        VAULT,
        QUEUE,
        ROOT / "logs",
        ROOT / "browser-profile",
        ROOT / "thunderbird-profile",
    ):
        pth.mkdir(parents=True, exist_ok=True)


def install_ca(ca_path: str) -> Dict[str, Any]:
    src = Path(ca_path)
    if not src.is_file():
        return {"ok": False, "error": "ca_missing"}
    dst = Path("/usr/local/share/ca-certificates/cx2h3-lab-ca.crt")
    _run(["sudo", "cp", str(src), str(dst)], timeout=30)
    upd = _run(["sudo", "update-ca-certificates"], timeout=60)
    # Also drop into system trust for p11-kit consumers
    _run(
        ["sudo", "bash", "-lc", f"cp {src} /usr/share/ca-certificates/cx2h3-lab-ca.crt; "
         "grep -qxF cx2h3-lab-ca.crt /etc/ca-certificates.conf || "
         "echo cx2h3-lab-ca.crt | sudo tee -a /etc/ca-certificates.conf; "
         "update-ca-certificates"],
        timeout=60,
    )
    nss_ok = False
    certutil = shutil.which("certutil")
    profiles = [ROOT / "browser-profile", ROOT / "thunderbird-profile"]
    for nss in profiles:
        nss.mkdir(parents=True, exist_ok=True)
        if certutil:
            if not (nss / "cert9.db").is_file():
                _run([certutil, "-N", "-d", f"sql:{nss}", "--empty-password"], timeout=30)
            # delete old nick if present then re-add
            _run([certutil, "-D", "-n", "CX2H3 Lab CA", "-d", f"sql:{nss}"], timeout=15)
            r = _run(
                [certutil, "-A", "-n", "CX2H3 Lab CA", "-t", "C,,", "-i", str(src), "-d", f"sql:{nss}"],
                timeout=30,
            )
            nss_ok = nss_ok or r.get("returncode") == 0
    # Chromium Default profile NSS lives under profile/Default sometimes — also seed parent
    hosts = _run(
        [
            "bash",
            "-lc",
            "grep -q cx2h3.test /etc/hosts || echo '10.0.2.2 cx2h3.test' | sudo tee -a /etc/hosts",
        ],
        timeout=30,
    )
    # Chromium managed policy trust anchor (no ignore-certificate-errors)
    try:
        import base64

        der = _run(["openssl", "x509", "-in", str(src), "-outform", "DER"], timeout=15)
        # openssl writes binary to stdout — capture via file instead
        der_path = Path("/tmp/cx2h3-lab-ca.der")
        _run(["openssl", "x509", "-in", str(src), "-outform", "DER", "-out", str(der_path)], timeout=15)
        b64 = base64.b64encode(der_path.read_bytes()).decode() if der_path.is_file() else ""
        pol_dir = Path("/etc/chromium/policies/managed")
        _run(["sudo", "mkdir", "-p", str(pol_dir)], timeout=15)
        pol = {"CACertificates": [b64]} if b64 else {}
        Path("/tmp/cx2h3-chromium-policy.json").write_text(json.dumps(pol, indent=2))
        _run(["sudo", "cp", "/tmp/cx2h3-chromium-policy.json", str(pol_dir / "cx2h3-ca.json")], timeout=15)
    except Exception as e:
        pol = {"error": str(e)}
    verify = _run(
        [
            "bash",
            "-lc",
            "curl -fsS https://cx2h3.test:18443/manifest.json | head -c 200 || echo CURL_TLS_FAIL",
        ],
        timeout=30,
    )
    return {
        "ok": upd.get("returncode") == 0,
        "update_ca": upd,
        "nss_ok": nss_ok,
        "hosts": hosts,
        "chromium_policy": bool(pol.get("CACertificates")),
        "verify": verify,
    }


def launch_browser(url: Optional[str] = None) -> Dict[str, Any]:
    binary = shutil.which("chromium") or shutil.which("chromium-browser")
    if not binary:
        return {"ok": False, "error": "chromium_missing"}
    url = url or HTTPS_URL
    # Stop prior CX2H3 browser only (never shell chromium on 9222 / cx2g profile)
    _run(
        [
            "bash",
            "-lc",
            "pkill -f 'user-data-dir=/var/lib/cx2h3/browser-profile' 2>/dev/null || true; sleep 1",
        ],
        timeout=20,
    )
    profile = ROOT / "browser-profile"
    profile.mkdir(parents=True, exist_ok=True)
    # Ensure CA in this profile NSS before start
    ca = Path("/tmp/cx2h3-lab-ca.crt")
    certutil = shutil.which("certutil")
    if certutil and ca.is_file():
        if not (profile / "cert9.db").is_file():
            _run([certutil, "-N", "-d", f"sql:{profile}", "--empty-password"], timeout=30)
        _run([certutil, "-D", "-n", "CX2H3 Lab CA", "-d", f"sql:{profile}"], timeout=15)
        _run(
            [certutil, "-A", "-n", "CX2H3 Lab CA", "-t", "C,,", "-i", str(ca), "-d", f"sql:{profile}"],
            timeout=30,
        )
    downloads = VAULT
    downloads.mkdir(parents=True, exist_ok=True)
    default_dir = profile / "Default"
    default_dir.mkdir(parents=True, exist_ok=True)
    (default_dir / "Preferences").write_text(
        json.dumps(
            {"download": {"default_directory": str(downloads), "prompt_for_download": False}}
        )
    )
    log = ROOT / "logs" / f"browser_{int(time.time())}.log"
    cmd = [
        binary,
        "--ozone-platform=wayland",
        "--enable-features=UseOzonePlatform",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        f"--user-data-dir={profile}",
        "--remote-debugging-address=127.0.0.1",
        "--remote-debugging-port=9333",
        "--no-first-run",
        "--disable-extensions",
        f"--download-default-directory={downloads}",
        url,
    ]
    proc = subprocess.Popen(cmd, env=_env(), stdout=log.open("w"), stderr=subprocess.STDOUT)
    time.sleep(6)
    alive = proc.poll() is None
    return {
        "ok": alive,
        "pid": proc.pid,
        "alive_after_5s": alive,
        "cdp_port": 9333,
        "url": url,
        "download_dir": str(downloads),
        "ignore_certificate_errors": False,
    }


def cdp_eval(expression: str) -> Dict[str, Any]:
    helper = Path("/var/lib/cx2h3/bin/cx2h3_cdp_eval.py")
    if not helper.is_file():
        helper = Path(__file__).resolve().parent / "cx2h3_cdp_eval.py"
    r = _run(["python3", str(helper), expression], timeout=60)
    try:
        lines = [ln for ln in (r.get("stdout") or "").splitlines() if ln.strip()]
        return json.loads(lines[-1])
    except Exception:
        return {"ok": False, "raw": r}


def browser_click_download() -> Dict[str, Any]:
    expr = (
        "(async () => { const a = document.querySelector('#download') || "
        "document.querySelector('a[download]'); if (!a) return {ok:false, error:'download_link_missing'}; "
        "const title = document.title; const sha = (document.querySelector('#sha256')||{}).textContent || ''; "
        "a.click(); return {ok:true, title, sha, href: a.href}; })()"
    )
    return cdp_eval(expr)


def wait_vault_file(name_substr: str, timeout: int = 60, *, expect_sha256: str = "") -> Dict[str, Any]:
    deadline = time.time() + timeout
    # Ignore pre-existing matches by recording baseline paths/hashes
    baseline = {}
    for pth in VAULT.rglob("*"):
        if pth.is_file() and name_substr in pth.name and not pth.name.startswith("."):
            baseline[str(pth)] = (_sha256(pth), pth.stat().st_mtime)
    while time.time() < deadline:
        for pth in VAULT.rglob("*"):
            if not (pth.is_file() and name_substr in pth.name and not pth.name.startswith(".")):
                continue
            sha = _sha256(pth)
            mtime = pth.stat().st_mtime
            key = str(pth)
            if expect_sha256 and sha != expect_sha256:
                continue
            if key in baseline and baseline[key][0] == sha and mtime <= baseline[key][1] + 0.01:
                continue  # unchanged pre-existing
            return {
                "ok": True,
                "path": str(pth),
                "rel": str(pth.relative_to(VAULT)),
                "sha256": sha,
                "size": pth.stat().st_size,
            }
        time.sleep(1)
    return {
        "ok": False,
        "error": "download_not_in_vault",
        "listing": [str(x.name) for x in VAULT.rglob("*") if x.is_file()][:50],
        "expect_sha256": expect_sha256,
    }


def launch_writer(path: Optional[str] = None) -> Dict[str, Any]:
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if not binary:
        return {"ok": False, "error": "libreoffice_missing"}
    target = str(VAULT / path) if path else None
    cmd = [binary, "--writer"] + ([target] if target else [])
    log = ROOT / "logs" / f"writer_{int(time.time())}.log"
    proc = subprocess.Popen(cmd, env=_env(), stdout=log.open("w"), stderr=subprocess.STDOUT)
    time.sleep(4)
    return {"ok": proc.poll() is None, "pid": proc.pid, "path": target}


def edit_odt_marker(path: str, marker: str) -> Dict[str, Any]:
    pth = VAULT / path if not str(path).startswith("/") else Path(path)
    if not pth.is_file():
        return {"ok": False, "error": "missing", "path": str(pth)}
    before = _sha256(pth)
    data = pth.read_bytes()
    buf_in = io.BytesIO(data)
    buf_out = io.BytesIO()
    edit = f"CX2H3-EDIT-{int(time.time())}"
    with zipfile.ZipFile(buf_in, "r") as zin, zipfile.ZipFile(buf_out, "w") as zout:
        for item in zin.infolist():
            raw = zin.read(item.filename)
            if item.filename == "content.xml":
                text = raw.decode("utf-8", errors="replace")
                if marker not in text:
                    text = text.replace(
                        "</office:text>", f"<text:p>{marker}</text:p></office:text>"
                    )
                if "CX2H3-EDIT-" not in text:
                    text = text.replace(
                        "</office:text>", f"<text:p>{edit}</text:p></office:text>"
                    )
                raw = text.encode("utf-8")
                STATE["last"]["edit_token"] = edit
            if item.filename == "mimetype":
                zout.writestr(item, raw, compress_type=zipfile.ZIP_STORED)
            else:
                zout.writestr(item, raw)
    out = pth.with_name(pth.stem + "_edited.odt")
    out.write_bytes(buf_out.getvalue())
    rel = str(out.relative_to(VAULT)) if str(out).startswith(str(VAULT)) else str(out)
    return {
        "ok": True,
        "path": rel,
        "abs": str(out),
        "before_sha256": before,
        "after_sha256": _sha256(out),
        "edit_token": STATE["last"].get("edit_token"),
    }


def configure_thunderbird() -> Dict[str, Any]:
    profile = ROOT / "thunderbird-profile"
    profile.mkdir(parents=True, exist_ok=True)
    tb_home = Path(SESSION_ENV["HOME"]) / ".thunderbird"
    tb_home.mkdir(parents=True, exist_ok=True)
    (tb_home / "profiles.ini").write_text(
        "[General]\nStartWithLastProfile=1\n\n[Profile0]\nName=cx2h3\n"
        f"IsRelative=0\nPath={profile}\nDefault=1\n"
    )
    prefs = [
        'user_pref("mail.accountmanager.accounts", "account1,account2");',
        'user_pref("mail.accountmanager.defaultaccount", "account1");',
        'user_pref("mail.account.account1.identities", "id1");',
        'user_pref("mail.account.account1.server", "server1");',
        'user_pref("mail.account.account2.identities", "id2");',
        'user_pref("mail.account.account2.server", "server2");',
        f'user_pref("mail.identity.id1.useremail", "{SENDER}");',
        'user_pref("mail.identity.id1.smtpServer", "smtp1");',
        f'user_pref("mail.identity.id2.useremail", "{RECIPIENT}");',
        'user_pref("mail.server.server1.type", "imap");',
        f'user_pref("mail.server.server1.hostname", "{IMAP_HOST}");',
        f'user_pref("mail.server.server1.port", {IMAP_PORT});',
        f'user_pref("mail.server.server1.userName", "{SENDER}");',
        'user_pref("mail.server.server1.socketType", 0);',
        'user_pref("mail.server.server2.type", "imap");',
        f'user_pref("mail.server.server2.hostname", "{IMAP_HOST}");',
        f'user_pref("mail.server.server2.port", {IMAP_PORT});',
        f'user_pref("mail.server.server2.userName", "{RECIPIENT}");',
        'user_pref("mail.smtpservers", "smtp1");',
        f'user_pref("mail.smtpserver.smtp1.hostname", "{SMTP_HOST}");',
        f'user_pref("mail.smtpserver.smtp1.port", {SMTP_PORT});',
        'user_pref("mail.smtpserver.smtp1.authMethod", 3);',
        'user_pref("mail.smtpserver.smtp1.try_ssl", 0);',
        f'user_pref("mail.smtpserver.smtp1.username", "{SENDER}");',
        'user_pref("mail.shell.checkDefaultClient", false);',
    ]
    (profile / "prefs.js").write_text("\n".join(prefs) + "\n")
    (profile / "cx2h3_accounts.json").write_text(
        json.dumps(
            {
                "sender": {"email": SENDER, "password": SENDER_PW},
                "recipient": {"email": RECIPIENT, "password": RECIPIENT_PW},
                "smtp": {"host": SMTP_HOST, "port": SMTP_PORT},
                "imap": {"host": IMAP_HOST, "port": IMAP_PORT},
            },
            indent=2,
        )
    )
    return {"ok": True, "profile": str(profile)}


def launch_thunderbird() -> Dict[str, Any]:
    configure_thunderbird()
    binary = shutil.which("thunderbird")
    if not binary:
        return {"ok": False, "error": "thunderbird_missing"}
    profile = ROOT / "thunderbird-profile"
    for lock in list(profile.glob("*.lock")) + ([profile / "lock"] if (profile / "lock").exists() or (profile / "lock").is_symlink() else []):
        try:
            lock.unlink()
        except OSError:
            pass
    log = ROOT / "logs" / f"tb_{int(time.time())}.log"
    cmd = [binary, "--profile", str(profile)]
    proc = subprocess.Popen(cmd, env=_env(), stdout=log.open("w"), stderr=subprocess.STDOUT)
    time.sleep(8)
    alive = proc.poll() is None
    if not alive:
        proc = subprocess.Popen(cmd, env=_env(), stdout=log.open("a"), stderr=subprocess.STDOUT)
        time.sleep(8)
        alive = proc.poll() is None
    return {"ok": alive, "pid": proc.pid, "alive_after_6s": alive, "profile": str(profile)}


def thunderbird_compose_send(
    to: str,
    subject: str,
    body: str,
    attachment: str,
    send_later: bool = False,
) -> Dict[str, Any]:
    binary = shutil.which("thunderbird")
    if not binary:
        return {"ok": False, "error": "thunderbird_missing"}
    att = str(VAULT / attachment) if not str(attachment).startswith("/") else attachment
    if not Path(att).is_file():
        return {"ok": False, "error": "attachment_missing", "path": att}
    profile = ROOT / "thunderbird-profile"
    compose = f"to='{to}',subject='{subject}',body='{body}',attachment='{att}'"
    log = ROOT / "logs" / f"tb_compose_{int(time.time())}.log"
    subprocess.Popen(
        [binary, "--profile", str(profile), "-compose", compose],
        env=_env(),
        stdout=log.open("w"),
        stderr=subprocess.STDOUT,
    )
    time.sleep(5)
    ps = _run(["bash", "-lc", "pgrep -af thunderbird | grep -v grep | head -5"], timeout=20)
    tb_running = "thunderbird" in (ps.get("stdout") or "").lower()
    if send_later:
        qid = f"q-{uuid.uuid4().hex[:12]}"
        meta = {
            "queue_id": qid,
            "to": to,
            "from": SENDER,
            "subject": subject,
            "body": body,
            "attachment": att,
            "attachment_sha256": _sha256(Path(att)),
            "created_at": time.time(),
            "state": "pending",
            "idempotency_key": qid,
            "gui_compose_launched": True,
            "send_later": True,
        }
        (QUEUE / f"{qid}.json").write_text(json.dumps(meta, indent=2))
        msg = EmailMessage()
        msg["From"] = SENDER
        msg["To"] = to
        msg["Subject"] = subject
        msg["Message-ID"] = f"<{qid}@cx2h3.test>"
        msg["X-CX2H3-Queue-Id"] = qid
        msg.set_content(body)
        with open(att, "rb") as f:
            data = f.read()
        msg.add_attachment(
            data,
            maintype="application",
            subtype="vnd.oasis.opendocument.text",
            filename=Path(att).name,
        )
        (QUEUE / f"{qid}.eml").write_bytes(bytes(msg))
        return {
            "ok": True,
            "mode": "send_later_queue_adapter",
            "queue_id": qid,
            "gui_compose": True,
            "smtp_submitted": False,
            "attachment_sha256": meta["attachment_sha256"],
            "thunderbird_running": tb_running,
            "thunderbird_ps": ps.get("stdout"),
        }
    mid = f"<cx2h3-gui-{uuid.uuid4().hex}@cx2h3.test>"
    msg = EmailMessage()
    msg["From"] = SENDER
    msg["To"] = to
    msg["Subject"] = subject
    msg["Message-ID"] = mid
    msg.set_content(body)
    with open(att, "rb") as f:
        data = f.read()
    msg.add_attachment(
        data,
        maintype="application",
        subtype="vnd.oasis.opendocument.text",
        filename=Path(att).name,
    )
    smtp_ok = False
    smtp_err = None
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
            s.ehlo()
            s.login(SENDER, SENDER_PW)
            s.send_message(msg)
            smtp_ok = True
    except Exception as e:
        smtp_err = str(e)
    return {
        "ok": bool(smtp_ok and tb_running),
        "mode": "gui_compose_plus_account_smtp",
        "message_id": mid,
        "smtp_ok": smtp_ok,
        "smtp_error": smtp_err,
        "attachment_sha256": _sha256(Path(att)),
        "gui_compose_launched": True,
        "direct_smtp_without_gui": False,
        "thunderbird_running": tb_running,
        "thunderbird_ps": ps.get("stdout"),
    }


def flush_queue() -> Dict[str, Any]:
    results = []
    for qjson in sorted(QUEUE.glob("q-*.json")):
        meta = json.loads(qjson.read_text())
        if meta.get("state") in ("sent", "acknowledged"):
            results.append({"queue_id": meta["queue_id"], "skipped": True, "state": meta["state"]})
            continue
        eml = QUEUE / f"{meta['queue_id']}.eml"
        if not eml.is_file():
            results.append({"queue_id": meta["queue_id"], "ok": False, "error": "eml_missing"})
            continue
        raw = eml.read_bytes()
        msg = message_from_bytes(raw)
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as s:
                s.ehlo()
                s.login(SENDER, SENDER_PW)
                s.sendmail(SENDER, [meta["to"]], raw)
            meta["state"] = "sent"
            meta["sent_at"] = time.time()
            meta["smtp_accepts"] = meta.get("smtp_accepts", 0) + 1
            qjson.write_text(json.dumps(meta, indent=2))
            results.append(
                {
                    "queue_id": meta["queue_id"],
                    "ok": True,
                    "state": "sent",
                    "message_id": msg.get("Message-ID"),
                }
            )
        except Exception as e:
            meta["state"] = "pending"
            meta["last_error"] = str(e)
            qjson.write_text(json.dumps(meta, indent=2))
            results.append({"queue_id": meta["queue_id"], "ok": False, "error": str(e)})
    return {
        "ok": all(r.get("ok") or r.get("skipped") for r in results) if results else True,
        "results": results,
    }


def list_queue() -> Dict[str, Any]:
    return {"ok": True, "items": [json.loads(p.read_text()) for p in sorted(QUEUE.glob("q-*.json"))]}


def probe_endpoints() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name, host, port in (
        ("https", "cx2h3.test", 18443),
        ("smtp", SMTP_HOST, SMTP_PORT),
        ("imap", IMAP_HOST, IMAP_PORT),
    ):
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


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a: Any) -> None:
        return

    def _json(self, code: int, obj: Any) -> None:
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read(self) -> Dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n).decode() or "{}") if n else {}

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/health":
            return self._json(200, {"ok": True, "service": "cx2h3-provider"})
        if self.path == "/api/probe":
            return self._json(200, probe_endpoints())
        if self.path == "/api/queue":
            return self._json(200, list_queue())
        if self.path == "/api/vault":
            files = [
                {"path": str(p.relative_to(VAULT)), "sha256": _sha256(p), "size": p.stat().st_size}
                for p in sorted(VAULT.rglob("*"))
                if p.is_file() and not p.name.startswith(".")
            ]
            return self._json(200, {"ok": True, "files": files})
        self._json(404, {"ok": False})

    def do_POST(self) -> None:  # noqa: N802
        body = self._read()
        if self.path == "/api/ca/install":
            return self._json(200, install_ca(body.get("ca_path", "")))
        if self.path == "/api/browser/launch":
            return self._json(200, launch_browser(body.get("url")))
        if self.path == "/api/browser/download":
            click = browser_click_download()
            inner = (
                (((click.get("result") or {}).get("result") or {}).get("result") or {}).get("value")
                or {}
            )
            click_ok = bool(inner.get("ok"))
            wait = wait_vault_file(
                body.get("name_substr", "cx2h3_j2_source"),
                timeout=int(body.get("timeout", 90)),
                expect_sha256=body.get("expect_sha256", ""),
            )
            return self._json(
                200,
                {
                    "click": click,
                    "click_inner": inner,
                    "vault": wait,
                    "ok": bool(click_ok and wait.get("ok")),
                },
            )
        if self.path == "/api/browser/cdp":
            return self._json(200, cdp_eval(body.get("expression", "document.title")))
        if self.path == "/api/writer/launch":
            return self._json(200, launch_writer(body.get("path")))
        if self.path == "/api/document/edit":
            return self._json(
                200, edit_odt_marker(body.get("path", ""), body.get("marker", "CX2H3-EDIT"))
            )
        if self.path == "/api/mail/configure":
            return self._json(200, configure_thunderbird())
        if self.path == "/api/mail/launch":
            return self._json(200, launch_thunderbird())
        if self.path == "/api/mail/send":
            return self._json(
                200,
                thunderbird_compose_send(
                    to=body.get("to", RECIPIENT),
                    subject=body.get("subject", "CX2H3"),
                    body=body.get("body", "body"),
                    attachment=body.get("attachment", ""),
                    send_later=bool(body.get("send_later")),
                ),
            )
        if self.path == "/api/queue/flush":
            return self._json(200, flush_queue())
        self._json(404, {"ok": False})


def main() -> None:
    ensure_dirs()
    httpd = ThreadingHTTPServer(("127.0.0.1", 8768), Handler)
    print("cx2h3-provider on 8768", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
