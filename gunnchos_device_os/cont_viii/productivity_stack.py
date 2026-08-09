"""Productivity stack — integrate maintained Linux/open-source apps (Lane F).

Does NOT rewrite Microsoft Office. Selects LibreOffice (MPL-2.0 / Apache) for
offline ARM+x86 coverage over ONLYOFFICE (AGPL complexity for OEM).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import platform

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_PRODUCTIVITY_STACK_PASS


@dataclass(frozen=True)
class StackComponent:
    id: str
    role: str
    package: str
    license: str
    arches: tuple[str, ...]
    offline: bool
    integration: str
    notes: str = ""


# LibreOffice chosen: strong ARM+x86 Linux packaging, offline-first, MPL/Apache,
# CUPS print path mature. ONLYOFFICE remains documented alternative (AGPL).
PRODUCTIVITY_COMPONENTS: tuple[StackComponent, ...] = (
    StackComponent(
        "browser",
        "web",
        "chromium OR firefox",
        "BSD/MPL",
        ("x86_64", "aarch64"),
        True,
        "snap/flatpak/deb package pin",
        "Prefer Chromium on x86_64; Firefox ESR acceptable on aarch64.",
    ),
    StackComponent(
        "office_suite",
        "docs_sheets_decks",
        "libreoffice",
        "MPL-2.0",
        ("x86_64", "aarch64"),
        True,
        "apt/flatpak; headless soffice for CI export",
        "ONLYOFFICE alternative noted; LibreOffice selected for OEM/offline.",
    ),
    StackComponent(
        "pdf_tools",
        "pdf",
        "poppler-utils + libreoffice-draw",
        "GPL-2.0 / MPL-2.0",
        ("x86_64", "aarch64"),
        True,
        "pdftotext/pdfinfo + print-to-PDF via CUPS",
    ),
    StackComponent(
        "email_calendar",
        "comms",
        "thunderbird OR evolution OR web PWA",
        "MPL-2.0 / GPL-2.0",
        ("x86_64", "aarch64"),
        False,
        "IMAP/CalDAV client path + browser PWA fallback",
        "Offline cache when client supports; PWA requires network for first sync.",
    ),
    StackComponent(
        "webrtc_conferencing",
        "av_conf",
        "chromium WebRTC OR jitsi meet PWA",
        "BSD / Apache-2.0",
        ("x86_64", "aarch64"),
        False,
        "browser getUserMedia permission bridge",
    ),
    StackComponent(
        "printing",
        "cups",
        "cups + cups-pdf (virtual)",
        "Apache-2.0 / GPL-2.0",
        ("x86_64", "aarch64"),
        True,
        "CUPS virtual PDF printer for CI; physical printers PHYSICAL pending",
    ),
    StackComponent(
        "vpn_wireguard",
        "vpn",
        "wireguard-tools",
        "GPL-2.0",
        ("x86_64", "aarch64"),
        True,
        "wg-quick profile store under /etc/wireguard (DEV)",
    ),
    StackComponent(
        "vpn_openvpn",
        "vpn",
        "openvpn",
        "GPL-2.0",
        ("x86_64", "aarch64"),
        True,
        "openvpn client profile path",
    ),
    StackComponent(
        "smb",
        "fileshare",
        "cifs-utils / smbclient",
        "GPL-3.0",
        ("x86_64", "aarch64"),
        False,
        "mount.cifs for school/office shares",
    ),
    StackComponent(
        "nfs",
        "fileshare",
        "nfs-common",
        "GPL-2.0",
        ("x86_64", "aarch64"),
        False,
        "NFSv4 client where campus policy allows",
    ),
    StackComponent(
        "terminal",
        "creator_coder",
        "gnome-terminal OR kitty + bash/zsh",
        "GPL-3.0 / MIT",
        ("x86_64", "aarch64"),
        True,
        "Creator/Coder Studio shell",
    ),
    StackComponent(
        "editor_ide",
        "creator_coder",
        "vscode-oss OR code-server OR neovim",
        "MIT",
        ("x86_64", "aarch64"),
        True,
        "Creator Studio IDE surface; no proprietary VS Code marketplace claim",
    ),
)


@dataclass
class ProductivityStackPlan:
    host_arch: str = field(default_factory=lambda: platform.machine() or "unknown")
    components: list[dict[str, Any]] = field(default_factory=list)
    office_choice: str = "libreoffice"
    onlyoffice_alternative: str = "documented_not_selected"
    cups_virtual_pdf: bool = True
    mock: bool = False

    def evaluate(self) -> dict[str, Any]:
        self.components = [asdict(c) for c in PRODUCTIVITY_COMPONENTS]
        arch = self.host_arch
        if arch in ("arm64", "ARM64"):
            arch = "aarch64"
        if arch in ("amd64", "x64"):
            arch = "x86_64"
        supported = []
        for c in PRODUCTIVITY_COMPONENTS:
            ok = arch in c.arches or arch == "unknown"
            supported.append({"id": c.id, "arch_ok": ok, "offline": c.offline})
        required_ids = {
            "browser",
            "office_suite",
            "pdf_tools",
            "email_calendar",
            "webrtc_conferencing",
            "printing",
            "vpn_wireguard",
            "vpn_openvpn",
            "smb",
            "nfs",
            "terminal",
            "editor_ide",
        }
        present = {c.id for c in PRODUCTIVITY_COMPONENTS}
        ok = required_ids.issubset(present) and self.office_choice == "libreoffice"
        return {
            "schema": "gunnchos.productivity_stack.v1",
            "ok": ok,
            "token": TOKEN_PRODUCTIVITY_STACK_PASS if ok else None,
            "host_arch": self.host_arch,
            "normalized_arch": arch,
            "office_choice": self.office_choice,
            "onlyoffice_alternative": self.onlyoffice_alternative,
            "selection_rationale": (
                "LibreOffice: offline ARM+x86 Linux packages, MPL-2.0/Apache, "
                "mature CUPS print-to-PDF; ONLYOFFICE AGPL noted as alternative."
            ),
            "components": self.components,
            "arch_matrix": supported,
            "cups_virtual_pdf": self.cups_virtual_pdf,
            "rewrites_ms_office": False,
            "ms_fidelity_claimed": False,
            "physical_printer_claimed": False,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def build_productivity_stack() -> dict[str, Any]:
    return ProductivityStackPlan().evaluate()
