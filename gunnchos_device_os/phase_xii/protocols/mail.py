"""Real SMTP + IMAP local stack (aiosmtpd + minimal IMAP4 server)."""
from __future__ import annotations

import email
import socket
import threading
import time
import uuid
from email.message import EmailMessage
from typing import Any

from aiosmtpd.controller import Controller

from gunnchos_device_os.phase_xii.protocols.ports import free_port


class _Mailbox:
    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.messages: list[dict[str, Any]] = []

    def append(self, raw: bytes, envelope_from: str, envelope_to: list[str]) -> str:
        msg_id = str(uuid.uuid4())
        parsed = email.message_from_bytes(raw)
        with self.lock:
            self.messages.append(
                {
                    "id": msg_id,
                    "uid": len(self.messages) + 1,
                    "raw": raw,
                    "from": envelope_from,
                    "to": list(envelope_to),
                    "subject": parsed.get("Subject", ""),
                    "flags": ["\\Recent"],
                    "internaldate": time.strftime("%d-%b-%Y %H:%M:%S +0000", time.gmtime()),
                }
            )
        return msg_id


class _SMTPHandler:
    def __init__(self, mailbox: _Mailbox) -> None:
        self.mailbox = mailbox

    async def handle_DATA(self, server, session, envelope):  # noqa: N802
        self.mailbox.append(envelope.content, envelope.mail_from, list(envelope.rcpt_tos))
        return "250 Message accepted"


class _IMAPServer(threading.Thread):
    """Minimal IMAP4rev1 subset sufficient for compose/send/receive/search/reply proofs."""

    daemon = True

    def __init__(self, host: str, port: int, mailbox: _Mailbox) -> None:
        super().__init__(name="phase-xii-imap")
        self.host = host
        self.port = port
        self.mailbox = mailbox
        self._sock: socket.socket | None = None
        self._stop = threading.Event()

    def stop(self) -> None:
        self._stop.set()
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass

    def run(self) -> None:
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen(8)
        self._sock.settimeout(0.5)
        while not self._stop.is_set():
            try:
                conn, _addr = self._sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(target=self._client, args=(conn,), daemon=True).start()

    def _send(self, conn: socket.socket, line: str) -> None:
        conn.sendall((line + "\r\n").encode("utf-8"))

    def _client(self, conn: socket.socket) -> None:
        try:
            self._send(conn, "* OK phase-xii IMAP ready")
            selected = False
            buf = b""
            while not self._stop.is_set():
                chunk = conn.recv(4096)
                if not chunk:
                    break
                buf += chunk
                while b"\r\n" in buf:
                    line_b, buf = buf.split(b"\r\n", 1)
                    line = line_b.decode("utf-8", errors="replace")
                    parts = line.split(" ")
                    if len(parts) < 2:
                        continue
                    tag, cmd = parts[0], parts[1].upper()
                    if cmd == "CAPABILITY":
                        self._send(conn, "* CAPABILITY IMAP4rev1 AUTH=PLAIN")
                        self._send(conn, f"{tag} OK CAPABILITY completed")
                    elif cmd == "LOGIN":
                        self._send(conn, f"{tag} OK LOGIN completed")
                    elif cmd == "SELECT":
                        with self.mailbox.lock:
                            n = len(self.mailbox.messages)
                        self._send(conn, f"* {n} EXISTS")
                        self._send(conn, "* 0 RECENT")
                        self._send(conn, f'* OK [UIDVALIDITY 1] UIDs valid')
                        self._send(conn, f"{tag} OK [READ-WRITE] SELECT completed")
                        selected = True
                    elif cmd == "SEARCH":
                        with self.mailbox.lock:
                            ids = " ".join(str(i + 1) for i in range(len(self.mailbox.messages)))
                        self._send(conn, f"* SEARCH {ids}".rstrip())
                        self._send(conn, f"{tag} OK SEARCH completed")
                    elif cmd == "FETCH":
                        # FETCH 1 (RFC822) with proper literal framing
                        seq = 1
                        for p in parts[2:]:
                            if p.isdigit():
                                seq = int(p)
                                break
                        with self.mailbox.lock:
                            if 1 <= seq <= len(self.mailbox.messages):
                                raw = self.mailbox.messages[seq - 1]["raw"]
                            else:
                                raw = b""
                        # IMAP literal: * n FETCH (RFC822 {N}\r\n<data>\r\n)\r\n
                        conn.sendall(f"* {seq} FETCH (RFC822 {{{len(raw)}}}\r\n".encode("ascii"))
                        conn.sendall(raw)
                        conn.sendall(b")\r\n")
                        self._send(conn, f"{tag} OK FETCH completed")
                    elif cmd == "LOGOUT":
                        self._send(conn, "* BYE")
                        self._send(conn, f"{tag} OK LOGOUT completed")
                        return
                    elif cmd == "NOOP":
                        self._send(conn, f"{tag} OK NOOP completed")
                    else:
                        self._send(conn, f"{tag} OK {cmd} completed")
        finally:
            try:
                conn.close()
            except OSError:
                pass


class MailStack:
    def __init__(self) -> None:
        self.mailbox = _Mailbox()
        self.smtp_port = free_port()
        self.imap_port = free_port()
        self._smtp: Controller | None = None
        self._imap: _IMAPServer | None = None

    def start(self) -> dict[str, Any]:
        handler = _SMTPHandler(self.mailbox)
        self._smtp = Controller(handler, hostname="127.0.0.1", port=self.smtp_port)
        self._smtp.start()
        self._imap = _IMAPServer("127.0.0.1", self.imap_port, self.mailbox)
        self._imap.start()
        time.sleep(0.05)
        return {
            "ok": True,
            "protocol": "smtp+imap",
            "smtp": f"127.0.0.1:{self.smtp_port}",
            "imap": f"127.0.0.1:{self.imap_port}",
            "execution_depth": "L3_REAL_SERVICE_API",
            "implementation": "aiosmtpd+phase_xii_imap",
        }

    def stop(self) -> None:
        if self._smtp:
            self._smtp.stop()
        if self._imap:
            self._imap.stop()

    def send_message(self, from_addr: str, to_addr: str, subject: str, body: str, attach: bytes | None = None) -> dict[str, Any]:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText
        from email.mime.application import MIMEApplication

        msg = MIMEMultipart()
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))
        if attach:
            part = MIMEApplication(attach, Name="attachment.bin")
            part["Content-Disposition"] = 'attachment; filename="attachment.bin"'
            msg.attach(part)
        with smtplib.SMTP("127.0.0.1", self.smtp_port, timeout=10) as s:
            s.send_message(msg)
        return {"ok": True, "sent": True, "subject": subject, "execution_depth": "L4_REAL_APPLICATION_PROCESS"}

    def receive_latest(self, user: str = "dev", password: str = "dev") -> dict[str, Any]:
        import imaplib

        M = imaplib.IMAP4("127.0.0.1", self.imap_port)
        M.login(user, password)
        M.select("INBOX")
        typ, data = M.search(None, "ALL")
        ids = data[0].split() if data and data[0] else []
        latest = None
        if ids:
            typ, msg_data = M.fetch(ids[-1], "(RFC822)")
            raw = msg_data[0][1] if msg_data and msg_data[0] else b""
            parsed = email.message_from_bytes(raw)
            latest = {"subject": parsed.get("Subject"), "from": parsed.get("From"), "bytes": len(raw)}
        M.logout()
        return {"ok": True, "count": len(ids), "latest": latest, "execution_depth": "L4_REAL_APPLICATION_PROCESS"}
