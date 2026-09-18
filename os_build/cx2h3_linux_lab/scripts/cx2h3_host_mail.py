#!/usr/bin/env python3
"""Real SMTP + IMAP provider for CX2H.3 — two accounts, attachments, logs, offline-stoppable."""

from __future__ import annotations

import argparse
import email
import hashlib
import json
import os
import socket
import ssl
import threading
import time
import uuid
from email.policy import default
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

HOST = os.environ.get("CX2H3_MAIL_BIND", "0.0.0.0")
SMTP_PORT = int(os.environ.get("CX2H3_SMTP_PORT", "1587"))
IMAP_PORT = int(os.environ.get("CX2H3_IMAP_PORT", "1143"))
ROOT = Path(os.environ.get("CX2H3_MAIL_ROOT", "/tmp/cx2h3-mail"))

ACCOUNTS = {
    "sender@cx2h3.test": {"password": "cx2h3-sender-pass", "mailbox": "sender"},
    "recipient@cx2h3.test": {"password": "cx2h3-recipient-pass", "mailbox": "recipient"},
}

LOCK = threading.Lock()
LOG: List[Dict[str, Any]] = []
SMTP_ACCEPTS: List[Dict[str, Any]] = []


def _log(event: str, **kw: Any) -> None:
    LOG.append({"ts": time.time(), "event": event, **kw})
    (ROOT / "server.log").write_text(json.dumps(LOG[-200:], indent=2))


def _mbox(user: str) -> Path:
    box = ROOT / "mailboxes" / ACCOUNTS[user]["mailbox"]
    for sub in ("INBOX", "Sent", "cur", "new", "tmp"):
        (box / sub).mkdir(parents=True, exist_ok=True)
    # Maildir-like under INBOX/Sent
    for folder in ("INBOX", "Sent"):
        for sub in ("cur", "new", "tmp"):
            (box / folder / sub).mkdir(parents=True, exist_ok=True)
    return box


def _list_msgs(user: str, folder: str) -> List[Path]:
    box = _mbox(user)
    files = sorted((box / folder / "new").glob("*")) + sorted((box / folder / "cur").glob("*"))
    return [p for p in files if p.is_file()]


def _store_message(user: str, folder: str, raw: bytes, *, flags: str = "") -> Dict[str, Any]:
    box = _mbox(user)
    uid = int(time.time() * 1000) % 10_000_000 + len(_list_msgs(user, folder)) + 1
    name = f"{uid}.cx2h3{flags}"
    path = box / folder / "new" / name
    path.write_bytes(raw)
    meta = {
        "uid": uid,
        "path": str(path),
        "size": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "folder": folder,
        "user": user,
        "message_id": None,
    }
    try:
        msg = email.message_from_bytes(raw, policy=default)
        meta["message_id"] = msg.get("Message-ID")
        meta["subject"] = msg.get("Subject")
        meta["from"] = msg.get("From")
        meta["to"] = msg.get("To")
    except Exception:
        pass
    (box / folder / f"{uid}.meta.json").write_text(json.dumps(meta, indent=2))
    return meta


def _deliver_smtp(raw: bytes, mailfrom: str, rcpts: List[str]) -> Dict[str, Any]:
    msg = email.message_from_bytes(raw, policy=default)
    if not msg.get("Message-ID"):
        mid = f"<cx2h3-{uuid.uuid4().hex}@cx2h3.test>"
        # prepend Message-ID
        raw = f"Message-ID: {mid}\r\n".encode() + raw
        msg = email.message_from_bytes(raw, policy=default)
    results = []
    # Store in sender Sent if known
    sender = None
    for acct in ACCOUNTS:
        if mailfrom.lower().find(acct.split("@")[0]) >= 0 or mailfrom.lower() == acct:
            sender = acct
            break
    if sender is None and mailfrom.lower() in ACCOUNTS:
        sender = mailfrom.lower()
    # Prefer explicit From header match
    frm = (msg.get("From") or "").lower()
    for acct in ACCOUNTS:
        if acct in frm:
            sender = acct
            break
    if sender:
        results.append(_store_message(sender, "Sent", raw))
    for rcpt in rcpts:
        r = rcpt.lower().strip()
        if r in ACCOUNTS:
            results.append(_store_message(r, "INBOX", raw))
    rec = {
        "ts": time.time(),
        "mailfrom": mailfrom,
        "rcpts": rcpts,
        "message_id": msg.get("Message-ID"),
        "subject": msg.get("Subject"),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "stores": results,
    }
    SMTP_ACCEPTS.append(rec)
    (ROOT / "smtp_accepts.json").write_text(json.dumps(SMTP_ACCEPTS, indent=2))
    _log("smtp_accept", **rec)
    return rec


class SMTPSession:
    def __init__(self, conn: socket.socket, addr: Tuple[str, int]):
        self.conn = conn
        self.addr = addr
        self.mailfrom = ""
        self.rcpts: List[str] = []
        self.data_mode = False
        self.buf = b""
        self.authed = False
        self.user = ""

    def send(self, line: str) -> None:
        self.conn.sendall((line + "\r\n").encode())

    def handle(self) -> None:
        self.send("220 cx2h3.test ESMTP CX2H3")
        self.conn.settimeout(120)
        while True:
            try:
                chunk = self.conn.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            self.buf += chunk
            while b"\n" in self.buf and not self.data_mode:
                line, self.buf = self.buf.split(b"\n", 1)
                text = line.decode(errors="replace").rstrip("\r")
                upper = text.upper()
                if upper.startswith("EHLO") or upper.startswith("HELO"):
                    self.send("250-cx2h3.test")
                    self.send("250-AUTH LOGIN PLAIN")
                    self.send("250-SIZE 52428800")
                    self.send("250 8BITMIME")
                elif upper.startswith("AUTH PLAIN"):
                    parts = text.split(" ", 2)
                    if len(parts) == 3:
                        import base64

                        try:
                            decoded = base64.b64decode(parts[2]).decode()
                            # \0user\0pass
                            bits = decoded.split("\0")
                            user = bits[-2] if len(bits) >= 2 else ""
                            pw = bits[-1] if bits else ""
                            if user in ACCOUNTS and ACCOUNTS[user]["password"] == pw:
                                self.authed = True
                                self.user = user
                                self.send("235 Authentication successful")
                            else:
                                self.send("535 Authentication failed")
                        except Exception:
                            self.send("535 Authentication failed")
                    else:
                        self.send("334 ")
                elif upper.startswith("AUTH LOGIN"):
                    self.send("334 VXNlcm5hbWU6")  # Username:
                    raw_u = self.conn.recv(4096).decode().strip()
                    import base64

                    try:
                        user = base64.b64decode(raw_u).decode()
                    except Exception:
                        user = raw_u
                    self.send("334 UGFzc3dvcmQ6")
                    raw_p = self.conn.recv(4096).decode().strip()
                    try:
                        pw = base64.b64decode(raw_p).decode()
                    except Exception:
                        pw = raw_p
                    if user in ACCOUNTS and ACCOUNTS[user]["password"] == pw:
                        self.authed = True
                        self.user = user
                        self.send("235 Authentication successful")
                    else:
                        self.send("535 Authentication failed")
                elif upper.startswith("MAIL FROM:"):
                    if not self.authed:
                        self.send("530 Authentication required")
                    else:
                        self.mailfrom = text[10:].strip().strip("<>")
                        self.rcpts = []
                        self.send("250 OK")
                elif upper.startswith("RCPT TO:"):
                    self.rcpts.append(text[8:].strip().strip("<>"))
                    self.send("250 OK")
                elif upper == "DATA":
                    self.send("354 End data with <CR><LF>.<CR><LF>")
                    self.data_mode = True
                    self.buf = b""
                elif upper == "RSET":
                    self.mailfrom = ""
                    self.rcpts = []
                    self.send("250 OK")
                elif upper == "QUIT":
                    self.send("221 Bye")
                    return
                elif upper == "NOOP":
                    self.send("250 OK")
                else:
                    self.send("502 Command not implemented")
            if self.data_mode:
                if b"\r\n.\r\n" in self.buf or b"\n.\r\n" in self.buf:
                    if b"\r\n.\r\n" in self.buf:
                        data, self.buf = self.buf.split(b"\r\n.\r\n", 1)
                    else:
                        data, self.buf = self.buf.split(b"\n.\r\n", 1)
                    # unescape dot-stuffing
                    data = data.replace(b"\r\n.", b"\r\n")
                    _deliver_smtp(data, self.mailfrom, self.rcpts)
                    self.data_mode = False
                    self.send("250 OK: queued")
                    self.mailfrom = ""
                    self.rcpts = []


def smtp_server() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, SMTP_PORT))
    srv.listen(20)
    _log("smtp_listen", port=SMTP_PORT)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=lambda c=conn, a=addr: SMTPSession(c, a).handle(), daemon=True).start()


class IMAPSession:
    def __init__(self, conn: socket.socket, addr: Tuple[str, int]):
        self.conn = conn
        self.addr = addr
        self.user = ""
        self.selected = ""
        self.tag_buf = b""

    def send(self, line: str) -> None:
        self.conn.sendall((line + "\r\n").encode())

    def handle(self) -> None:
        self.send("* OK CX2H3 IMAP ready")
        self.conn.settimeout(300)
        buf = b""
        while True:
            try:
                chunk = self.conn.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                text = line.decode(errors="replace").rstrip("\r")
                if not text:
                    continue
                parts = text.split(" ", 2)
                tag = parts[0]
                cmd = parts[1].upper() if len(parts) > 1 else ""
                arg = parts[2] if len(parts) > 2 else ""
                if cmd == "CAPABILITY":
                    self.send("* CAPABILITY IMAP4rev1 AUTH=PLAIN")
                    self.send(f"{tag} OK CAPABILITY")
                elif cmd == "LOGIN":
                    bits = arg.split(" ", 1)
                    user = bits[0].strip('"')
                    pw = bits[1].strip('"') if len(bits) > 1 else ""
                    if user in ACCOUNTS and ACCOUNTS[user]["password"] == pw:
                        self.user = user
                        self.send(f"{tag} OK LOGIN")
                        _log("imap_login", user=user)
                    else:
                        self.send(f"{tag} NO LOGIN failed")
                elif cmd == "LIST":
                    self.send('* LIST (\\HasNoChildren) "/" INBOX')
                    self.send('* LIST (\\HasNoChildren) "/" Sent')
                    self.send(f"{tag} OK LIST")
                elif cmd == "SELECT" or cmd == "EXAMINE":
                    folder = arg.strip().strip('"')
                    self.selected = folder
                    msgs = _list_msgs(self.user, folder) if self.user else []
                    self.send(f"* {len(msgs)} EXISTS")
                    self.send("* 0 RECENT")
                    self.send(f"* OK [UIDVALIDITY 1]")
                    self.send(f"{tag} OK [READ-WRITE] SELECT")
                elif cmd == "FETCH" or cmd == "UID":
                    # Minimal FETCH support: UID FETCH n BODY[] / RFC822 / BODY.PEEK[]
                    msgs = _list_msgs(self.user, self.selected) if self.user and self.selected else []
                    if cmd == "UID":
                        # UID FETCH <set> <items>
                        rest = arg
                        sub = rest.split(" ", 1)
                        if sub and sub[0].upper() == "FETCH":
                            rest = sub[1] if len(sub) > 1 else ""
                        set_part, _, items = rest.partition(" ")
                        want_uids = set_part
                        try:
                            if ":" in want_uids:
                                a, b = want_uids.split(":", 1)
                                uids = range(int(a), int(b) + 1) if b != "*" else range(int(a), 10**9)
                            else:
                                uids = [int(want_uids)]
                        except Exception:
                            uids = []
                        for i, p in enumerate(msgs, 1):
                            uid = int(p.name.split(".", 1)[0])
                            if uid not in uids and not (isinstance(uids, range) and uid in uids):
                                # also allow '*' range via membership
                                if not any(uid == u for u in uids):
                                    continue
                            raw = p.read_bytes()
                            if "BODY.PEEK[]" in items.upper() or "RFC822" in items.upper() or "BODY[]" in items.upper():
                                self.send(f"* {i} FETCH (UID {uid} RFC822 {{{len(raw)}}}")
                                self.conn.sendall(raw + b")\r\n")
                            else:
                                self.send(f"* {i} FETCH (UID {uid} FLAGS (\\Seen) RFC822.SIZE {len(raw)})")
                        self.send(f"{tag} OK UID FETCH")
                    else:
                        # FETCH seq
                        set_part, _, items = arg.partition(" ")
                        try:
                            seqs = [int(set_part)]
                        except Exception:
                            seqs = list(range(1, len(msgs) + 1))
                        for seq in seqs:
                            if seq < 1 or seq > len(msgs):
                                continue
                            p = msgs[seq - 1]
                            uid = int(p.name.split(".", 1)[0])
                            raw = p.read_bytes()
                            self.send(f"* {seq} FETCH (UID {uid} RFC822 {{{len(raw)}}}")
                            self.conn.sendall(raw + b")\r\n")
                        self.send(f"{tag} OK FETCH")
                elif cmd == "SEARCH":
                    msgs = _list_msgs(self.user, self.selected) if self.user else []
                    ids = " ".join(str(i) for i in range(1, len(msgs) + 1))
                    self.send(f"* SEARCH {ids}".rstrip())
                    self.send(f"{tag} OK SEARCH")
                elif cmd == "LOGOUT":
                    self.send("* BYE")
                    self.send(f"{tag} OK LOGOUT")
                    return
                elif cmd == "NOOP":
                    self.send(f"{tag} OK NOOP")
                elif cmd == "CLOSE":
                    self.selected = ""
                    self.send(f"{tag} OK CLOSE")
                else:
                    self.send(f"{tag} BAD unknown command {cmd}")


def imap_server() -> None:
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((HOST, IMAP_PORT))
    srv.listen(20)
    _log("imap_listen", port=IMAP_PORT)
    while True:
        conn, addr = srv.accept()
        threading.Thread(target=lambda c=conn, a=addr: IMAPSession(c, a).handle(), daemon=True).start()


def write_status() -> None:
    status = {
        "smtp_port": SMTP_PORT,
        "imap_port": IMAP_PORT,
        "accounts": list(ACCOUNTS.keys()),
        "pid": os.getpid(),
        "smtp_accepts": len(SMTP_ACCEPTS),
    }
    (ROOT / "server.json").write_text(json.dumps(status, indent=2))
    (ROOT / "server.pid").write_text(str(os.getpid()))


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    for u in ACCOUNTS:
        _mbox(u)
    write_status()
    threading.Thread(target=smtp_server, daemon=True).start()
    threading.Thread(target=imap_server, daemon=True).start()
    print(f"CX2H3 mail SMTP:{SMTP_PORT} IMAP:{IMAP_PORT}", flush=True)
    while True:
        write_status()
        time.sleep(2)


if __name__ == "__main__":
    main()
