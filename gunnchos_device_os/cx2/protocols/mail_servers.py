"""Deterministic local SMTP + IMAP servers (imaplib-compatible)."""

from __future__ import annotations

import json
import socket
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


class _SMTPHandler(threading.Thread):
    def __init__(self, sock: socket.socket, store: "MailStore"):
        super().__init__(daemon=True)
        self.sock = sock
        self.store = store

    def run(self) -> None:
        with self.sock:
            f = self.sock.makefile("rwb")

            def send(line: str) -> None:
                f.write((line + "\r\n").encode())
                f.flush()

            send("220 cx2.local SMTP ready")
            buf: List[str] = []
            data_mode = False
            mail_from = ""
            rcpt: List[str] = []
            while True:
                line = f.readline()
                if not line:
                    break
                text = line.decode(errors="ignore").rstrip("\r\n")
                upper = text.upper()
                if data_mode:
                    if text == ".":
                        raw = "\r\n".join(buf).encode()
                        self.store.add(raw, mail_from, rcpt)
                        send("250 OK queued")
                        buf = []
                        data_mode = False
                        mail_from = ""
                        rcpt = []
                    else:
                        buf.append(text[1:] if text.startswith(".") else text)
                    continue
                if upper.startswith("EHLO") or upper.startswith("HELO"):
                    send("250-cx2.local")
                    send("250 OK")
                elif upper.startswith("MAIL FROM:"):
                    mail_from = text.split(":", 1)[1].strip()
                    send("250 OK")
                elif upper.startswith("RCPT TO:"):
                    rcpt.append(text.split(":", 1)[1].strip())
                    send("250 OK")
                elif upper == "DATA":
                    send("354 End data with <CR><LF>.<CR><LF>")
                    data_mode = True
                elif upper == "QUIT":
                    send("221 Bye")
                    break
                elif upper == "RSET":
                    mail_from, rcpt, buf = "", [], []
                    send("250 OK")
                else:
                    send("250 OK")


class _IMAPHandler(threading.Thread):
    def __init__(self, sock: socket.socket, store: "MailStore"):
        super().__init__(daemon=True)
        self.sock = sock
        self.store = store

    def run(self) -> None:
        with self.sock:
            f = self.sock.makefile("rwb")

            def send(line: str) -> None:
                f.write((line + "\r\n").encode())
                f.flush()

            send("* OK CX2 IMAP ready")
            selected = False
            while True:
                line = f.readline()
                if not line:
                    break
                text = line.decode(errors="ignore").rstrip("\r\n")
                if not text:
                    continue
                parts = text.split(" ")
                tag = parts[0]
                cmd = parts[1].upper() if len(parts) > 1 else ""
                arg = " ".join(parts[2:]) if len(parts) > 2 else ""

                if cmd == "CAPABILITY":
                    send("* CAPABILITY IMAP4rev1 AUTH=PLAIN")
                    send(f"{tag} OK CAPABILITY completed")
                elif cmd == "LOGIN":
                    send(f"{tag} OK LOGIN completed")
                elif cmd in ("SELECT", "EXAMINE"):
                    selected = True
                    n = len(self.store.messages)
                    send(r"* FLAGS (\Seen)")
                    send(f"* {n} EXISTS")
                    send(f"* 0 RECENT")
                    send("* OK [UIDVALIDITY 1] UIDs valid")
                    send(f"* OK [UIDNEXT {n + 1}] Predicted next UID")
                    send(f"{tag} OK [READ-WRITE] {cmd} completed")
                elif cmd == "FETCH" and selected:
                    self._fetch(f, send, tag, arg)
                elif cmd == "UID" and arg.upper().startswith("FETCH") and selected:
                    self._fetch(f, send, tag, arg.split(" ", 1)[1] if " " in arg else "1:*", uid=True)
                elif cmd == "SEARCH":
                    ids = " ".join(str(i) for i in range(1, len(self.store.messages) + 1))
                    send(f"* SEARCH {ids}".rstrip())
                    send(f"{tag} OK SEARCH completed")
                elif cmd == "LOGOUT":
                    send("* BYE CX2 logging out")
                    send(f"{tag} OK LOGOUT completed")
                    break
                elif cmd == "NOOP":
                    send(f"{tag} OK NOOP completed")
                else:
                    send(f"{tag} BAD unknown command {cmd}")

    def _fetch(self, f, send, tag: str, arg: str, uid: bool = False) -> None:
        for idx, msg in enumerate(self.store.messages, start=1):
            raw = msg["raw"]
            # literal must be immediately followed by data then closing paren on continuation
            if uid:
                header = f"* {idx} FETCH (UID {idx} RFC822 {{{len(raw)}}}\r\n"
            else:
                header = f"* {idx} FETCH (RFC822 {{{len(raw)}}}\r\n"
            f.write(header.encode())
            f.write(raw)
            f.write(b")\r\n")
            f.flush()
        send(f"{tag} OK FETCH completed")


@dataclass
class MailStore:
    root: Path
    messages: List[dict] = field(default_factory=list)

    def add(self, raw: bytes, mail_from: str, rcpt: List[str]) -> Path:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"msg_{int(time.time() * 1000)}_{len(self.messages)}.eml"
        path.write_bytes(raw)
        self.messages.append({"path": str(path), "raw": raw, "from": mail_from, "to": rcpt})
        (self.root / "index.json").write_text(
            json.dumps(
                [{"path": m["path"], "from": m["from"], "to": m["to"]} for m in self.messages],
                indent=2,
            )
            + "\n"
        )
        return path


@dataclass
class LocalMailStack:
    root: Path
    store: MailStore = field(init=False)
    smtp_host: str = "127.0.0.1"
    imap_host: str = "127.0.0.1"
    smtp_port: int = 0
    imap_port: int = 0
    _smtp_sock: Optional[socket.socket] = None
    _imap_sock: Optional[socket.socket] = None
    _stop: bool = False

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.store = MailStore(self.root / "maildir")

    def start(self) -> dict:
        self._smtp_sock = socket.socket()
        self._smtp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._smtp_sock.bind((self.smtp_host, 0))
        self._smtp_sock.listen(5)
        self.smtp_port = self._smtp_sock.getsockname()[1]

        self._imap_sock = socket.socket()
        self._imap_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._imap_sock.bind((self.imap_host, 0))
        self._imap_sock.listen(5)
        self.imap_port = self._imap_sock.getsockname()[1]

        self._stop = False
        threading.Thread(target=self._accept_smtp, daemon=True).start()
        threading.Thread(target=self._accept_imap, daemon=True).start()
        return {
            "smtp": f"{self.smtp_host}:{self.smtp_port}",
            "imap": f"{self.imap_host}:{self.imap_port}",
            "tls": False,
            "notes": "plain_local_deterministic_stack",
        }

    def _accept_smtp(self) -> None:
        assert self._smtp_sock
        self._smtp_sock.settimeout(0.5)
        while not self._stop:
            try:
                conn, _ = self._smtp_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            _SMTPHandler(conn, self.store).start()

    def _accept_imap(self) -> None:
        assert self._imap_sock
        self._imap_sock.settimeout(0.5)
        while not self._stop:
            try:
                conn, _ = self._imap_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            _IMAPHandler(conn, self.store).start()

    def stop(self) -> None:
        self._stop = True
        for s in (self._smtp_sock, self._imap_sock):
            if s:
                try:
                    s.close()
                except OSError:
                    pass
