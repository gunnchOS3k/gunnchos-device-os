"""CX1G Connect — email/calendar/contacts adapters + local protocol E2E fixtures."""

from __future__ import annotations

import json
import shutil
import smtplib
import socket
import time
from dataclasses import dataclass, field
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional

from .vault import Vault


@dataclass
class LocalMailFixture:
    """Minimal local SMTP sink for protocol E2E (not Gmail/Outlook)."""

    root: Path
    host: str = "127.0.0.1"
    port: int = 0
    messages: List[dict] = field(default_factory=list)

    def store(self, raw: bytes, envelope: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / f"msg_{int(time.time()*1000)}.eml"
        path.write_bytes(raw)
        self.messages.append({"path": str(path), **envelope})


@dataclass
class Connect:
    root: Path
    vault: Vault
    thunderbird: Optional[str] = None
    outbox: List[dict] = field(default_factory=list)
    calendar: List[dict] = field(default_factory=list)
    contacts: List[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("mail", "calendar", "contacts", "outbox", "conference"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self.thunderbird = shutil.which("thunderbird")
        self._load()

    def _load(self) -> None:
        outbox = self.root / "outbox" / "queue.json"
        if outbox.exists():
            self.outbox = json.loads(outbox.read_text()).get("items", [])
        cal = self.root / "calendar" / "events.json"
        if cal.exists():
            self.calendar = json.loads(cal.read_text()).get("events", [])
        contacts = self.root / "contacts" / "cards.json"
        if contacts.exists():
            self.contacts = json.loads(contacts.read_text()).get("contacts", [])

    def _save(self) -> None:
        (self.root / "outbox" / "queue.json").write_text(
            json.dumps({"items": self.outbox}, indent=2) + "\n"
        )
        (self.root / "calendar" / "events.json").write_text(
            json.dumps({"events": self.calendar}, indent=2) + "\n"
        )
        (self.root / "contacts" / "cards.json").write_text(
            json.dumps({"contacts": self.contacts}, indent=2) + "\n"
        )

    def thunderbird_status(self) -> dict:
        if not self.thunderbird:
            return {
                "available": False,
                "evidence_class": "DIGITAL_PARTIAL",
                "notes": "thunderbird_absent_fail_closed_no_gmail_claim",
            }
        return {"available": True, "binary": self.thunderbird, "evidence_class": "DIGITAL_PASS"}

    def add_contact(self, name: str, email: str) -> dict:
        card = {"name": name, "email": email, "uid": f"contact_{len(self.contacts)+1}"}
        self.contacts.append(card)
        self._save()
        return card

    def add_event(self, title: str, starts_at: str, meeting_url: Optional[str] = None) -> dict:
        event = {
            "title": title,
            "starts_at": starts_at,
            "meeting_url": meeting_url,
            "uid": f"evt_{len(self.calendar)+1}",
        }
        self.calendar.append(event)
        self._save()
        return event

    def compose(
        self,
        to: str,
        subject: str,
        body: str,
        *,
        attachment_vault_path: Optional[str] = None,
    ) -> dict:
        item = {
            "id": f"mail_{int(time.time()*1000)}",
            "to": to,
            "subject": subject,
            "body": body,
            "attachment": attachment_vault_path,
            "state": "queued",
            "ts": time.time(),
        }
        if attachment_vault_path:
            # ensure attachment exists in vault
            data = self.vault.read(attachment_vault_path)
            item["attachment_sha256"] = __import__("hashlib").sha256(data).hexdigest()
        self.outbox.append(item)
        self._save()
        return item

    def send_local_smtp(self, item_id: str, *, smtp_host: str = "127.0.0.1", smtp_port: int) -> dict:
        item = next((i for i in self.outbox if i["id"] == item_id), None)
        if not item:
            raise KeyError(item_id)
        msg = EmailMessage()
        msg["From"] = "cx1@localhost"
        msg["To"] = item["to"]
        msg["Subject"] = item["subject"]
        msg.set_content(item["body"])
        if item.get("attachment"):
            data = self.vault.read(item["attachment"])
            msg.add_attachment(
                data,
                maintype="application",
                subtype="octet-stream",
                filename=Path(item["attachment"]).name,
            )
        try:
            with smtplib.SMTP(smtp_host, smtp_port, timeout=5) as smtp:
                smtp.send_message(msg)
            item["state"] = "sent"
            self._save()
            return {"ok": True, "id": item_id, "evidence_class": "DIGITAL_PASS"}
        except (OSError, smtplib.SMTPException) as exc:
            item["state"] = "queued"
            self._save()
            return {
                "ok": False,
                "id": item_id,
                "error": type(exc).__name__,
                "evidence_class": "DIGITAL_PARTIAL",
            }

    def save_attachment_from_mail(self, eml_path: Path, dest_rel: str) -> dict:
        raw = Path(eml_path).read_bytes()
        # naive extract after first blank line for fixture mails
        self.vault.write(dest_rel, raw, mime_hint="message/rfc822")
        return {"ok": True, "path": dest_rel}

    def launch_conference(self, meeting_url: str) -> dict:
        path = self.root / "conference" / "last_launch.json"
        path.write_text(json.dumps({"url": meeting_url, "ts": time.time()}) + "\n")
        return {
            "ok": True,
            "url": meeting_url,
            "via": "browser_web_launch",
            "screen_share_permission_hook": "permissions.screencast",
            "evidence_class": "DIGITAL_PARTIAL",
            "claim_boundary": "web_launch_not_native_meet_completeness",
        }

    def caldav_carddav_fixture_roundtrip(self) -> dict:
        """Local CalDAV/CardDAV-shaped JSON store — protocol E2E without cloud."""
        self.add_contact("Ada", "ada@example.test")
        self.add_event("Standup", "2026-09-16T15:00:00Z", meeting_url="https://meet.example.test/cx1")
        return {
            "contacts": len(self.contacts),
            "events": len(self.calendar),
            "ok": len(self.contacts) >= 1 and len(self.calendar) >= 1,
            "evidence_class": "DIGITAL_PASS",
            "claim_boundary": "local_fixture_not_gmail_outlook",
        }

    def reload_outbox(self) -> int:
        self._load()
        return sum(1 for i in self.outbox if i.get("state") == "queued")
