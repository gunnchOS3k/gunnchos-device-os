"""Authentic journeys J1–J7 — REAL_USER_JOURNEY_DIGITAL_PASS only with real UI+provider."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

from gunnchos_device_os.cx2.shell.product_shell import ProductShell


@dataclass
class AuthenticJourneyRunner:
    shell: ProductShell

    def run_all(self) -> Dict[str, dict]:
        return {
            "J1": self.j1_school_office_paper(),
            "J2": self.j2_research_web_mail(),
            "J3": self.j3_app_lifecycle(),
            "J4": self.j4_calendar_collaboration(),
            "J5": self.j5_offline_reconnect(),
            "J6": self.j6_accessibility(),
            "J7": self.j7_recovery(),
        }

    def j1_school_office_paper(self) -> dict:
        """Docs → PDF → print attempt → Vault."""
        self.shell.ensure_first_run("J1 User", "School")
        self.shell.nav.go("home")
        prod = self.shell.provider_registry().productivity
        doc = prod.create_document("j1_essay", "writer", body="J1 school essay CX2")
        edited = prod.edit_via_libreoffice("j1_essay", "writer", append=" revised")
        pdf = prod.export_pdf("j1_essay", "writer")
        printed = self.shell.provider_registry().printing.submit(Path(pdf["path"])) if pdf.get("ok") else {"ok": False}
        # GUI surface touch
        ui = self.shell.surface("vault")
        real_provider = bool(doc.get("ok") and pdf.get("ok"))
        # ProductShell.surface is API contract, not compositor/React rendered proof
        rendered_gui_proven = False
        if real_provider and printed.get("ok") and rendered_gui_proven:
            status = "REAL_USER_JOURNEY_DIGITAL_PASS"
        elif real_provider and printed.get("ok"):
            status = "REAL_PROVIDER_CLI_PASS"
        elif real_provider:
            status = "REAL_PROVIDER_PARTIAL"
        else:
            status = "BLOCKED"
        return {
            "name": "J1_school_office_paper",
            "ok": real_provider,
            "steps": {"doc": doc, "edited": edited, "pdf": pdf, "printed": printed, "ui": ui.get("title")},
            "PHYSICAL_PRINTER_VALIDATION_PENDING": True,
            "evidence_class": status,
        }

    def j2_research_web_mail(self) -> dict:
        self.shell.ensure_first_run("J2 User", "School")
        browser = self.shell.provider_registry().browser.qualify(allow_gui=False)
        self.shell.cx1.vault.write("research/note.txt", b"research note")
        connect = self.shell.provider_registry().connect
        # providers re-attached in ensure_first_run; keep vault pointer fresh
        connect.vault = self.shell.cx1.vault
        mail = connect.compose_send_receive(
            subject="J2 research",
            body="see note",
            attachment_vault_path="research/note.txt",
        )
        ui = self.shell.surface("connect")
        real = mail.get("ok") and browser.get("evidence_class") in (
            "REAL_PROVIDER_CLI_PASS",
            "REAL_PROVIDER_GUI_PASS",
            "REAL_PROVIDER_PARTIAL",
        )
        # Browser often CLI-only without GUI automation
        klass = "REAL_PROVIDER_PARTIAL" if real else "HARNESS_ONLY"
        # Require explicit rendered GUI proof for journey DIGITAL_PASS (not API surface alone)
        return {
            "name": "J2_research_web_mail",
            "ok": bool(mail.get("ok")),
            "steps": {"browser": browser.get("evidence_class"), "mail": mail, "ui": ui.get("title")},
            "evidence_class": klass,
        }

    def j3_app_lifecycle(self) -> dict:
        self.shell.ensure_first_run("J3 User")
        apps = self.shell.provider_registry().app_center
        inst = apps.install("org.gunnchos.cx2.testapp", "1.0.0")
        launch = apps.launch("org.gunnchos.cx2.testapp")
        upd = apps.update("org.gunnchos.cx2.testapp", "2.0.0")
        rb = apps.rollback("org.gunnchos.cx2.testapp")
        launch2 = apps.launch("org.gunnchos.cx2.testapp")
        un = apps.uninstall("org.gunnchos.cx2.testapp")
        ui = self.shell.surface("app_center")
        ok = all([inst.get("installed"), launch.get("launched"), upd.get("updated"), rb.get("rolled_back"), launch2.get("launched"), un.get("uninstalled")])
        if ok and launch.get("pid") and launch.get("gui_window"):
            klass = "REAL_USER_JOURNEY_DIGITAL_PASS"
        elif ok and launch.get("pid"):
            klass = "REAL_PROVIDER_CLI_PASS"
        else:
            klass = "BLOCKED"
        return {
            "name": "J3_app_lifecycle",
            "ok": ok,
            "steps": {"install": inst, "launch": launch, "update": upd, "rollback": rb, "uninstall": un},
            "evidence_class": klass,
        }

    def j4_calendar_collaboration(self) -> dict:
        self.shell.ensure_first_run("J4 User")
        connect = self.shell.provider_registry().connect
        cal = connect.calendar_crud()
        contacts = connect.contacts_crud()
        chat = connect.status_chat_video()
        ui = self.shell.surface("connect")
        ok = cal.get("ok") and contacts.get("ok")
        return {
            "name": "J4_calendar_collaboration",
            "ok": ok,
            "steps": {"calendar": cal, "contacts": contacts, "chat_video": chat, "ui": ui.get("title")},
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
            "HUMAN_AV_QUALITY_PENDING": True,
            "PHYSICAL_CAMERA_MIC_PENDING": True,
        }

    def j5_offline_reconnect(self) -> dict:
        self.shell.ensure_first_run("J5 User")
        self.shell.set_offline(True)
        self.shell.cx1.vault.write("offline/draft.txt", b"draft-offline")
        connect = self.shell.provider_registry().connect
        queued = connect.offline_queue_reconnect()
        self.shell.set_offline(False)
        ok = queued.get("ok") and self.shell.cx1.vault.read("offline/draft.txt") == b"draft-offline"
        return {
            "name": "J5_offline_reconnect",
            "ok": ok,
            "steps": {"queue": queued},
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
        }

    def j6_accessibility(self) -> dict:
        self.shell.ensure_first_run("J6 User")
        traverse = self.shell.keyboard_traverse_all()
        ui = self.shell.surface("assist")
        # Rendered React UI a11y is tested separately in vitest; Python side is harness
        return {
            "name": "J6_accessibility",
            "ok": traverse.get("ok") and ui.get("surface") == "assist",
            "steps": {"traverse": traverse, "assist": ui.get("title")},
            "HUMAN_A11Y_PENDING": True,
            "HUMAN_VALIDATION_PENDING": True,
            "evidence_class": "HARNESS_PASS",
            "human_validation_packet": str(
                Path("artifacts/complete_experience/cx2/HUMAN_A11Y_VALIDATION_PACKET.md")
            ),
        }

    def j7_recovery(self) -> dict:
        self.shell.ensure_first_run("J7 User")
        vault = self.shell.cx1.vault
        vault.write("critical/data.bin", b"important-bytes")
        backup = vault.create_backup("j7_backup")
        # corrupt
        vault.write("critical/data.bin", b"CORRUPTED")
        restored = vault.restore_backup("j7_backup", overwrite="replace")
        data = vault.read("critical/data.bin")
        care = self.shell.surface("care")
        ok = data == b"important-bytes" and restored.get("restore_verified") and backup.get("integrity_manifest")
        return {
            "name": "J7_recovery",
            "ok": ok,
            "steps": {"backup": backup.get("backup_id"), "restored": restored, "care_ui": care.get("title")},
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
        }
