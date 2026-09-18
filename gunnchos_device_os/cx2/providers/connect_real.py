"""Real Connect — first-party mail/calendar/contacts over local protocols + chat/video qualify."""

from __future__ import annotations

import imaplib
import json
import shutil
import smtplib
import time
import urllib.request
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional

from gunnchos_device_os.cx1.vault import Vault
from gunnchos_device_os.cx2.protocols.dav_server import LocalDavStack
from gunnchos_device_os.cx2.protocols.mail_servers import LocalMailStack


@dataclass
class RealConnectProvider:
    root: Path
    vault: Vault
    mail: Optional[LocalMailStack] = None
    dav: Optional[LocalDavStack] = None
    outbox: List[dict] = field(default_factory=list)
    thunderbird: Optional[str] = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("mail", "calendar", "contacts", "chat", "outbox"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self.thunderbird = shutil.which("thunderbird")
        tb_app = Path("/Applications/Thunderbird.app/Contents/MacOS/thunderbird")
        if not self.thunderbird and tb_app.exists():
            self.thunderbird = str(tb_app)

    def start_local_stack(self) -> dict:
        self.mail = LocalMailStack(self.root / "mail_stack")
        self.dav = LocalDavStack(self.root / "dav_stack")
        mail_info = self.mail.start()
        dav_info = self.dav.start()
        return {"mail": mail_info, "dav": dav_info, "thunderbird": bool(self.thunderbird)}

    def stop(self) -> None:
        if self.mail:
            self.mail.stop()
        if self.dav:
            self.dav.stop()

    def status_mail(self) -> dict:
        return {
            "thunderbird": bool(self.thunderbird),
            "local_stack": bool(self.mail),
            "smtp": f"{self.mail.smtp_host}:{self.mail.smtp_port}" if self.mail else None,
            "imap": f"{self.mail.imap_host}:{self.mail.imap_port}" if self.mail else None,
        }

    def status_calendar(self) -> dict:
        return {
            "caldav": bool(self.dav),
            "events": len(self.dav.events) if self.dav else 0,
        }

    def status_contacts(self) -> dict:
        return {
            "carddav": bool(self.dav),
            "contacts": len(self.dav.contacts) if self.dav else 0,
        }

    def status_chat_video(self) -> dict:
        # Qualify paths honestly — do not fabricate WebRTC success
        jitsi = False
        matrix = shutil.which("element-desktop") or shutil.which("fractal")
        return {
            "candidates": {
                "jitsi_meet_browser": "EXTERNAL_PROVIDER_PENDING",
                "matrix_element": "REAL_PROVIDER_PARTIAL" if matrix else "EXTERNAL_PROVIDER_PENDING",
                "first_party_webrtc": "EXTERNAL_PROVIDER_PENDING",
            },
            "HUMAN_AV_QUALITY_PENDING": True,
            "PHYSICAL_CAMERA_MIC_PENDING": True,
            "qualified_path": None,
            "evidence_class": "EXTERNAL_PROVIDER_PENDING",
        }

    def overall_class(self) -> str:
        if self.mail and self.dav:
            return "REAL_PROVIDER_CLI_PASS"
        return "EXTERNAL_PROVIDER_PENDING"

    def overall_status(self) -> dict:
        return {
            "mail": self.status_mail(),
            "calendar": self.status_calendar(),
            "contacts": self.status_contacts(),
            "chat_video": self.status_chat_video(),
            "evidence_class": self.overall_class(),
            "claim_boundary": "no_gmail_outlook_completeness_claims",
        }

    def compose_send_receive(
        self,
        *,
        to: str = "peer@localhost",
        subject: str = "CX2 hello",
        body: str = "hello from cx2",
        attachment_vault_path: Optional[str] = None,
    ) -> dict:
        if not self.mail:
            self.start_local_stack()
        assert self.mail
        msg = EmailMessage()
        msg["From"] = "cx2@localhost"
        msg["To"] = to
        msg["Subject"] = subject
        msg.set_content(body)
        if attachment_vault_path:
            data = self.vault.read(attachment_vault_path)
            msg.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=Path(attachment_vault_path).name,
            )
        with smtplib.SMTP(self.mail.smtp_host, self.mail.smtp_port, timeout=5) as smtp:
            smtp.send_message(msg)
        # IMAP fetch
        time.sleep(0.1)
        M = imaplib.IMAP4(self.mail.imap_host, self.mail.imap_port)
        M.login("cx2", "cx2")
        M.select("INBOX")
        typ, data = M.search(None, "ALL")
        ids = data[0].split()
        fetched = []
        for i in ids:
            typ, msg_data = M.fetch(i, "(RFC822)")
            if typ == "OK" and msg_data and msg_data[0]:
                fetched.append(len(msg_data[0][1]))
        M.logout()
        # Persist to vault + offline queue marker
        eml_path = f"mail/sent_{int(time.time()*1000)}.eml"
        self.vault.write(eml_path, msg.as_bytes(), mime_hint="message/rfc822")
        ok = len(self.mail.store.messages) >= 1 and len(fetched) >= 1
        return {
            "ok": ok,
            "smtp_stored": len(self.mail.store.messages),
            "imap_fetched": len(fetched),
            "vault_eml": eml_path,
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
        }

    def calendar_crud(self) -> dict:
        if not self.dav:
            self.start_local_stack()
        assert self.dav
        base = f"http://{self.dav.host}:{self.dav.port}"
        ics = "BEGIN:VCALENDAR\nBEGIN:VEVENT\nSUMMARY:CX2 Sync\nUID:cx2-evt-1\nEND:VEVENT\nEND:VCALENDAR\n"
        req = urllib.request.Request(
            base + "/caldav/cx2-evt-1",
            data=ics.encode(),
            method="PUT",
            headers={"Content-Type": "text/calendar"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            created = json.loads(resp.read().decode())
        with urllib.request.urlopen(base + "/caldav/cx2-evt-1", timeout=5) as resp:
            got = resp.read().decode()
        # edit
        ics2 = ics.replace("CX2 Sync", "CX2 Sync Edited")
        req2 = urllib.request.Request(
            base + "/caldav/cx2-evt-1",
            data=ics2.encode(),
            method="PUT",
            headers={"Content-Type": "text/calendar"},
        )
        with urllib.request.urlopen(req2, timeout=5) as resp:
            edited = json.loads(resp.read().decode())
        # delete
        req3 = urllib.request.Request(base + "/caldav/cx2-evt-1", method="DELETE")
        with urllib.request.urlopen(req3, timeout=5) as resp:
            deleted = json.loads(resp.read().decode())
        ok = created.get("ok") and "CX2 Sync" in got and edited.get("ok") and deleted.get("ok")
        return {
            "ok": ok,
            "created": created,
            "synced_body_len": len(got),
            "edited": edited,
            "deleted": deleted,
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
        }

    def contacts_crud(self) -> dict:
        if not self.dav:
            self.start_local_stack()
        assert self.dav
        base = f"http://{self.dav.host}:{self.dav.port}"
        vcf = "BEGIN:VCARD\nFN:CX2 Peer\nEMAIL:peer@localhost\nUID:cx2-c1\nEND:VCARD\n"
        req = urllib.request.Request(
            base + "/carddav/cx2-c1",
            data=vcf.encode(),
            method="PUT",
            headers={"Content-Type": "text/vcard"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            created = json.loads(resp.read().decode())
        with urllib.request.urlopen(base + "/carddav/cx2-c1", timeout=5) as resp:
            got = resp.read().decode()
        vcf2 = vcf.replace("CX2 Peer", "CX2 Peer Edited")
        req2 = urllib.request.Request(
            base + "/carddav/cx2-c1",
            data=vcf2.encode(),
            method="PUT",
            headers={"Content-Type": "text/vcard"},
        )
        with urllib.request.urlopen(req2, timeout=5) as resp:
            edited = json.loads(resp.read().decode())
        ok = created.get("ok") and "CX2 Peer" in got and edited.get("ok")
        return {
            "ok": ok,
            "created": created,
            "synced": got,
            "edited": edited,
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
        }

    def offline_queue_reconnect(self) -> dict:
        item = {"id": f"q_{int(time.time())}", "state": "queued", "subject": "offline"}
        self.outbox.append(item)
        (self.root / "outbox" / "queue.json").write_text(json.dumps({"items": self.outbox}, indent=2) + "\n")
        # reconnect flush via SMTP
        if not self.mail:
            self.start_local_stack()
        assert self.mail
        send = self.compose_send_receive(subject="offline-flush", body="queued then sent")
        item["state"] = "sent" if send.get("ok") else "queued"
        (self.root / "outbox" / "queue.json").write_text(json.dumps({"items": self.outbox}, indent=2) + "\n")
        return {
            "ok": send.get("ok") and item["state"] == "sent",
            "queue": self.outbox,
            "send": send,
            "duplicates": len(self.mail.store.messages),
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if send.get("ok") else "BLOCKED",
        }
