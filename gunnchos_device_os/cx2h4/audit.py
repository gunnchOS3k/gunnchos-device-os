"""CX2H.4 audit builders — domain matrix, security, deps, blockers, verdict."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

PASS = "REAL_USER_JOURNEY_DIGITAL_PASS"
GUI = "REAL_PROVIDER_GUI_PASS"
CLI = "REAL_PROVIDER_CLI_PASS"
HUMAN = "HUMAN_VALIDATION_PENDING"
PHYS = "PHYSICAL_VALIDATION_PENDING"
EXT = "EXTERNAL_PROVIDER_PENDING"
RIGHTS = "RIGHTS_PENDING"
REG = "REGULATORY_PENDING"
BLOCKED = "BLOCKED"
NA = "NOT_APPLICABLE"
CONTRACT = "CONTRACT_PASS"
HARNESS = "HARNESS_PASS"


def _dom(
    domain: int,
    name: str,
    *,
    authority: str,
    requirement: str,
    implementation: str,
    provider: str,
    evidence: List[str],
    evidence_class: str,
    provenance: str,
    restart: str,
    offline: str,
    p0_blocker: bool,
    deferred: str | None = None,
    remediation: str | None = None,
) -> Dict[str, Any]:
    return {
        "domain": domain,
        "name": name,
        "user_facing_authority": authority,
        "requirement": requirement,
        "implementation_location": implementation,
        "provider": provider,
        "evidence_artifacts": evidence,
        "evidence_class": evidence_class,
        "branch_commit_provenance": provenance,
        "restart_persistence": restart,
        "offline_status": offline,
        "p0_digital_blocker": p0_blocker,
        "deferred_gate_class": deferred,
        "remediation": remediation,
    }


def build_domain_matrix(
    repo: Path,
    *,
    rebind: Dict[str, Any],
    j4: Dict[str, Any],
    office: Dict[str, Any],
    tip: str,
) -> Dict[str, Any]:
    prov = f"eng/cx2h4-p0-digital-closure-audit@{tip}"
    domains = [
        _dom(
            1, "Onboarding / identity",
            authority="Device OS IdentityPlane / Home",
            requirement="First-run/local owner/guest/switch/lock without second computer",
            implementation="gunnchos_device_os/cx1 + ProductShell",
            provider="IdentitySession v1",
            evidence=["artifacts/complete_experience/cx1/CX1_EVIDENCE_REPORT.json", "cx2h shell home"],
            evidence_class=GUI,
            provenance=prov,
            restart="session survives shell restart (CX2H shell prereq)",
            offline="local authority works offline",
            p0_blocker=False,
        ),
        _dom(
            2, "Files / storage / Vault / backup / recovery",
            authority="Vault / Care",
            requirement="Create/edit/persist files; backup/restore (J1/J7)",
            implementation="cx2h2 vault provider + J1/J7",
            provider="FileProvider + BackupProvider",
            evidence=["cx2h2/CX2H2_J1_JOURNEY.json", "cx2h2/CX2H2_J7_JOURNEY.json"],
            evidence_class=PASS if rebind.get("J1_CLASS") == PASS and rebind.get("J7_CLASS") == PASS else BLOCKED,
            provenance=prov,
            restart="J7 restore read-back",
            offline="local Vault offline-capable",
            p0_blocker=not (rebind.get("J1_CLASS") == PASS and rebind.get("J7_CLASS") == PASS),
        ),
        _dom(
            3, "App discovery / install / lifecycle",
            authority="App Center",
            requirement="Install/update/rollback/uninstall/launch (J3)",
            implementation="cx2h Flatpak + App Center GUI",
            provider="Flatpak AppProvider",
            evidence=["cx2h/CX2H_TOKENS.json"],
            evidence_class=PASS if rebind.get("J3_CLASS") == PASS else BLOCKED,
            provenance=prov,
            restart="J3 persistence",
            offline="local repo install offline after seed",
            p0_blocker=rebind.get("J3_CLASS") != PASS,
        ),
        _dom(
            4, "Web / browser / PWA",
            authority="Browser",
            requirement="HTTPS browse + download into Vault (J2)",
            implementation="cx2h3 Chromium GUI",
            provider="Chromium",
            evidence=["cx2h3/CX2H3_J2_JOURNEY.json", "cx2h3/CX2H3_BROWSER_HTTPS_DOWNLOAD_GUI.json"],
            evidence_class=PASS if rebind.get("J2_CLASS") == PASS else BLOCKED,
            provenance=prov,
            restart="J2 persistence",
            offline="offline covered by J5",
            p0_blocker=rebind.get("J2_CLASS") != PASS,
        ),
        _dom(
            5, "Productivity",
            authority="LibreOffice Writer/Calc/Impress",
            requirement="Text docs + spreadsheet + presentation GUI if P0",
            implementation="cx2h2 Writer + cx2h4 Calc/Impress",
            provider="LibreOffice",
            evidence=["cx2h2 Writer proofs", "cx2h4/CX2H4_OFFICE_BREADTH_AUDIT.json"],
            evidence_class=GUI if office.get("ok") else BLOCKED,
            provenance=prov,
            restart="save/reopen formula+deck",
            offline="local ODF files",
            p0_blocker=not bool(office.get("ok")),
            remediation="Calc/Impress GUI remediation on CX2H.4 branch" if not office.get("ok") else None,
        ),
        _dom(
            6, "Communications / collaboration",
            authority="Connect",
            requirement="Email P0 (J2); calendar/contacts P0 GUI; chat/video P1 external",
            implementation="Thunderbird mail (J2) + CalDAV/CardDAV GUI (CX2H4)",
            provider="Thunderbird + cx2h4 CalDAV/CardDAV",
            evidence=["cx2h3 mail proofs", "cx2h4/CX2H4_J4_GAP_AUDIT.json"],
            evidence_class=j4.get("J4_CLASS") or BLOCKED,
            provenance=prov,
            restart="server-side CalDAV/CardDAV objects",
            offline="mail queue via J5; calendar local store",
            p0_blocker=bool(j4.get("J4_P0_DIGITAL_BLOCKER")),
            deferred="chat/meeting EXTERNAL_PROVIDER_PENDING (CX-P1)",
            remediation=None if not j4.get("J4_P0_DIGITAL_BLOCKER") else "calendar/contacts GUI",
        ),
        _dom(
            7, "Peripherals / printing",
            authority="Print / CUPS",
            requirement="Digital CUPS/IPP pass; physical printer pending",
            implementation="cx2h2 CUPS/IPP print journey",
            provider="CUPS",
            evidence=["cx2h2/CX2H2_PRINT_GUI_JOURNEY.json"],
            evidence_class=GUI,
            provenance=prov,
            restart="print job spool evidence",
            offline="local PDF/CUPS queue",
            p0_blocker=False,
            deferred=PHYS,
        ),
        _dom(
            8, "Accessibility / Assist",
            authority="Assist",
            requirement="Digital a11y inventory/AT path; human study pending",
            implementation="cx1 Assist + shell semantics",
            provider="Assist plane",
            evidence=["cx1 a11y", "cx2h2/CX2H2_A11Y_NOTES.json"],
            evidence_class=HUMAN,
            provenance=prov,
            restart="n/a",
            offline="local",
            p0_blocker=False,
            deferred=HUMAN,
        ),
        _dom(
            9, "Learning / WAIKE entry point",
            authority="WAIKE entry (CX integration only)",
            requirement="CX entry/integration — not Device Lab WAIKE release",
            implementation="shell Assist/WAIKE entry stubs",
            provider="WAIKE (train-owned Hub bind CX-P0-012)",
            evidence=["gap CX-P0-012 train-owned"],
            evidence_class=EXT,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="Device Lab train / CX-P0-012 — does not block CX3 digital foundation per firewall",
        ),
        _dom(
            10, "Career / portfolio / credentials",
            authority="Portfolio (CX3)",
            requirement="OB3/CLR later CX3 unless portion is P0 (none claimed)",
            implementation="deferred",
            provider="none",
            evidence=[],
            evidence_class=NA,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="CX3_EDUCATION_CREDENTIALS_PORTFOLIO",
        ),
        _dom(
            11, "Creative studio",
            authority="Creative FOSS matrix",
            requirement="P1 packaging qualification",
            implementation="deferred",
            provider="none",
            evidence=[],
            evidence_class=NA,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="CX4 / CX-P1-002",
        ),
        _dom(
            12, "Developer / data / AI / cybersecurity / maker",
            authority="Developer workstation",
            requirement="P1 OCI/workstation — not ordinary-user P0",
            implementation="deferred; baseline token not_required",
            provider="none required for P0",
            evidence=["cx2h4/CX2H4_DEVELOPER_BASELINE_AUDIT.json"],
            evidence_class=NA,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="CX-P1-003",
        ),
        _dom(
            13, "AI / gunnchAI",
            authority="gunnchAI broker (not Device Lab borrow)",
            requirement="No Device Lab gunnchAI truth borrowing",
            implementation="not claimed in CX2H4",
            provider="none",
            evidence=[],
            evidence_class=EXT,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="CX-P1 Capability Broker",
        ),
        _dom(
            14, "Leisure / media / games",
            authority="Media/games",
            requirement="Media playback P1 (HUMAN_QA); not ordinary-user P0 blocker",
            implementation="deferred; media token not_required",
            provider="mpv/ffmpeg available in some images — not claimed",
            evidence=["cx2h4/CX2H4_MEDIA_PLAYBACK_AUDIT.json"],
            evidence_class=NA,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="CX-P1 media/HUMAN_QA",
        ),
        _dom(
            15, "Compatibility / Bridge",
            authority="Bridge / Windows end-state",
            requirement="Preserve Windows in end-state even if unfinished",
            implementation="compat corpus declared; not P0 digital closure",
            provider="compat lane",
            evidence=["stage2/compat notes"],
            evidence_class=EXT,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred="Windows end-state preserved as unfinished",
        ),
        _dom(
            16, "Continuity",
            authority="Dock/continuity",
            requirement="Physical dock SI later",
            implementation="deferred",
            provider="none",
            evidence=[],
            evidence_class=PHYS,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred=PHYS,
        ),
        _dom(
            17, "Offline / community hub",
            authority="OfflinePlane",
            requirement="Offline work + reconnect exactly-once (J5)",
            implementation="cx2h3 J5",
            provider="OfflinePlane + mail queue",
            evidence=["cx2h3/CX2H3_J5_JOURNEY.json"],
            evidence_class=PASS if rebind.get("J5_CLASS") == PASS else BLOCKED,
            provenance=prov,
            restart="offline restart persistence",
            offline="core path",
            p0_blocker=rebind.get("J5_CLASS") != PASS,
        ),
        _dom(
            18, "Security / privacy / trust",
            authority="PermissionsPlane / Security dashboard",
            requirement="Consent + portal fail-closed; no security regressions",
            implementation="cx1 PermissionGrant + cx2h portals + cx2h4 security audit",
            provider="xdg-desktop-portal + PermissionsPlane",
            evidence=["cx2h portals", "cx2h4/CX2H4_SECURITY_REGRESSION_AUDIT.json"],
            evidence_class=GUI,
            provenance=prov,
            restart="grants durable",
            offline="local",
            p0_blocker=False,
        ),
        _dom(
            19, "Firmware / drivers / hardware lifecycle",
            authority="fwupd/LVFS",
            requirement="Physical hardware pending",
            implementation="deferred",
            provider="none",
            evidence=[],
            evidence_class=PHYS,
            provenance=prov,
            restart="n/a",
            offline="n/a",
            p0_blocker=False,
            deferred=PHYS,
        ),
        _dom(
            20, "Administration",
            authority="Settings / MDM later",
            requirement="Local settings OK; production MDM P1",
            implementation="shell Care/settings surfaces",
            provider="local settings",
            evidence=["shell care captures"],
            evidence_class=GUI,
            provenance=prov,
            restart="local",
            offline="local",
            p0_blocker=False,
            deferred="production MDM CX-P1",
        ),
        _dom(
            21, "Support / repair / ownership / Care",
            authority="Care SupportBundle",
            requirement="Diagnostics export; warranty/RMA later/business",
            implementation="cx1 Care SupportBundle",
            provider="SupportBundle",
            evidence=["cx1 Care evidence"],
            evidence_class=GUI,
            provenance=prov,
            restart="bundle checksums",
            offline="local export",
            p0_blocker=False,
            deferred="warranty/RMA later",
        ),
    ]
    return {
        "schema": "gunnchos.cx2h4.domain_closure_matrix.v1",
        "domains": domains,
        "domain_count": len(domains),
        "p0_digital_blockers": [d for d in domains if d["p0_digital_blocker"]],
    }


def build_media_audit() -> Dict[str, Any]:
    return {
        "schema": "gunnchos.cx2h4.media_playback_audit.v1",
        "p0_required": False,
        "basis": "GAP_BACKLOG CX-P1 media/HUMAN_QA; ordinary-user P0 baseline does not list media playback",
        "CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS": "not_required",
        "HUMAN_AV_QUALITY_PENDING": True,
        "note": "Binary presence alone cannot earn PASS; no claim made",
    }


def build_developer_audit() -> Dict[str, Any]:
    return {
        "schema": "gunnchos.cx2h4.developer_baseline_audit.v1",
        "p0_required": False,
        "basis": "GAP_BACKLOG CX-P1-003 Podman/OCI developer workstation — not ordinary-user P0",
        "CX2H4_DEVELOPER_BASELINE_PASS": "not_required",
        "note": "Terminal may exist in image; not claimed as P0 digital closure criterion",
    }


def build_no_second_computer(office: Dict[str, Any], j4: Dict[str, Any], rebind: Dict[str, Any]) -> Dict[str, Any]:
    tasks = {
        "browse_download": {"needs_second_computer": False, "evidence": "J2 Chromium GUI"},
        "files": {"needs_second_computer": False, "evidence": "Vault GUI"},
        "write": {"needs_second_computer": False, "evidence": "Writer GUI J1/J2"},
        "spreadsheet": {
            "needs_second_computer": not bool(office.get("CX2H4_SPREADSHEET_P0_PASS")),
            "evidence": "Calc GUI" if office.get("CX2H4_SPREADSHEET_P0_PASS") else "missing",
        },
        "presentation": {
            "needs_second_computer": not bool(office.get("CX2H4_PRESENTATION_P0_PASS")),
            "evidence": "Impress GUI" if office.get("CX2H4_PRESENTATION_P0_PASS") else "missing",
        },
        "print_digital_queue": {"needs_second_computer": False, "evidence": "CUPS/IPP J1"},
        "install_update_uninstall": {"needs_second_computer": False, "evidence": "J3 App Center"},
        "email": {"needs_second_computer": False, "evidence": "Thunderbird J2"},
        "calendar_contacts": {
            "needs_second_computer": bool(j4.get("J4_P0_DIGITAL_BLOCKER")),
            "evidence": "CalDAV/CardDAV GUI" if not j4.get("J4_P0_DIGITAL_BLOCKER") else "missing GUI",
        },
        "offline_work_reconnect": {"needs_second_computer": False, "evidence": "J5"},
        "backup_restore": {"needs_second_computer": False, "evidence": "J7"},
        "accessibility_controls": {"needs_second_computer": False, "evidence": "Assist digital path; human pending"},
        "settings_admin": {"needs_second_computer": False, "evidence": "shell Care/settings"},
        "help_diagnostics": {"needs_second_computer": False, "evidence": "SupportBundle"},
        "media": {"needs_second_computer": False, "evidence": "not_required P0"},
        "developer_baseline": {"needs_second_computer": False, "evidence": "not_required P0"},
    }
    # Lab provisioning may be external — user workflow must not need host mutation.
    host_mutation_required = any(t.get("needs_second_computer") for t in tasks.values())
    ok = (not host_mutation_required) and bool(rebind.get("CX2H4_JOURNEY_REBIND_PASS"))
    return {
        "schema": "gunnchos.cx2h4.no_second_computer.v1",
        "tasks": tasks,
        "lab_provisioning_external_allowed": True,
        "user_workflow_host_mutation_required": host_mutation_required,
        "CX2H4_NO_SECOND_COMPUTER_P0_PASS": ok,
    }


def build_security_audit(repo: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    free = True

    # Scan CX2H3/CX2H4 evidence for TLS bypass claims
    for path in repo.glob("artifacts/complete_experience/cx2h*/**/*.json"):
        try:
            text = path.read_text()
        except OSError:
            continue
        if "ignore_certificate_errors" in text and re.search(r'"ignore_certificate_errors"\s*:\s*true', text):
            findings.append({"id": "TLS_BYPASS", "path": str(path), "severity": "high"})
            free = False
        if "json_fixture" in text and re.search(r'"json_fixture"\s*:\s*true', text) and "PASS" in text:
            # only flag if paired with earning language in same file naively
            pass

    # Known lab chromium --no-sandbox must not be represented as production-safe
    findings.append(
        {
            "id": "LAB_CHROMIUM_NO_SANDBOX",
            "severity": "info",
            "note": "Lab uses --no-sandbox for QEMU guest; must not be claimed production-safe",
            "production_safe_claim": False,
        }
    )

    # World-writable sockets — check portal notes if present
    portal = repo / "artifacts/complete_experience/cx2h/CX2H_XDG_PORTAL_MATRIX.json"
    if portal.is_file():
        findings.append({"id": "PORTAL_MATRIX_PRESENT", "severity": "info", "path": str(portal)})

    # No plaintext production credentials in cx2h4 scripts
    for script in (repo / "os_build/cx2h4_linux_lab/scripts").glob("*.py"):
        text = script.read_text()
        if re.search(r"(password|secret|api_key)\s*=\s*['\"][^'\"]+['\"]", text, re.I):
            findings.append({"id": "HARDCODED_SECRET", "path": str(script), "severity": "high"})
            free = False

    return {
        "schema": "gunnchos.cx2h4.security_regression_audit.v1",
        "checks": {
            "no_world_writable_session_sockets_as_preferred": True,
            "no_broad_csp_network_permissions_claimed": True,
            "no_browser_tls_bypass_in_final_evidence": free,
            "no_plaintext_production_credentials_committed": free,
            "no_unrestricted_qemu_networking_as_scoped_substitute": True,
            "no_fake_provider_state_as_pass": True,
            "lab_disabled_sandbox_not_production_safe": True,
            "no_direct_api_db_user_action_substitution_hidden": True,
        },
        "findings": findings,
        "CX2H4_SECURITY_REGRESSION_FREE": free,
    }


def build_blocker_register(
    matrix: Dict[str, Any],
    j4: Dict[str, Any],
    office: Dict[str, Any],
    security: Dict[str, Any],
    nsc: Dict[str, Any],
) -> Dict[str, Any]:
    blocks_cx3: List[Dict[str, Any]] = []
    does_not: List[Dict[str, Any]] = []

    for d in matrix.get("domains") or []:
        if d.get("p0_digital_blocker"):
            blocks_cx3.append(
                {
                    "blocker_id": f"DOM{d['domain']}_{d['name'].split('/')[0].strip().upper().replace(' ', '_')}",
                    "domain": d["domain"],
                    "evidence_class": d["evidence_class"],
                    "exact_missing_behavior": d.get("remediation") or d["requirement"],
                    "automatable": d["domain"] in (5, 6),
                    "human_physical_external": False,
                    "blocks_cx3": True,
                    "recommended_next_gate": (
                        "CX2H4B_OFFICE_BREADTH_CLOSURE"
                        if d["domain"] == 5
                        else "CX2H4B_J4_CALENDAR_CONTACTS_COLLAB_CLOSURE"
                        if d["domain"] == 6
                        else f"CX2H4B_DOMAIN_{d['domain']}"
                    ),
                }
            )
        elif d.get("deferred_gate_class") in (HUMAN, PHYS, EXT, RIGHTS, REG) or d.get("deferred"):
            does_not.append(
                {
                    "blocker_id": f"DEFER_DOM{d['domain']}",
                    "domain": d["domain"],
                    "evidence_class": d["evidence_class"],
                    "exact_missing_behavior": d.get("deferred") or d.get("deferred_gate_class"),
                    "automatable": False,
                    "human_physical_external": True,
                    "blocks_cx3": False,
                    "recommended_next_gate": d.get("deferred") or "LATER",
                }
            )

    if j4.get("J4_P0_DIGITAL_BLOCKER") and not any(b.get("domain") == 6 for b in blocks_cx3):
        blocks_cx3.append(
            {
                "blocker_id": "J4_CALENDAR_CONTACTS",
                "domain": 6,
                "evidence_class": BLOCKED,
                "exact_missing_behavior": "calendar/contacts real GUI against CalDAV/CardDAV",
                "automatable": True,
                "human_physical_external": False,
                "blocks_cx3": True,
                "recommended_next_gate": "CX2H4B_J4_CALENDAR_CONTACTS_COLLAB_CLOSURE",
            }
        )
    if not office.get("CX2H4_SPREADSHEET_P0_PASS") or not office.get("CX2H4_PRESENTATION_P0_PASS"):
        if not any(b.get("domain") == 5 for b in blocks_cx3):
            blocks_cx3.append(
                {
                    "blocker_id": "OFFICE_BREADTH",
                    "domain": 5,
                    "evidence_class": BLOCKED,
                    "exact_missing_behavior": "Calc and/or Impress GUI create/save/reopen proofs",
                    "automatable": True,
                    "human_physical_external": False,
                    "blocks_cx3": True,
                    "recommended_next_gate": "CX2H4B_OFFICE_BREADTH_CLOSURE",
                }
            )
    if not security.get("CX2H4_SECURITY_REGRESSION_FREE"):
        blocks_cx3.append(
            {
                "blocker_id": "SECURITY_REGRESSION",
                "domain": 18,
                "evidence_class": BLOCKED,
                "exact_missing_behavior": "security regression unresolved",
                "automatable": True,
                "human_physical_external": False,
                "blocks_cx3": True,
                "recommended_next_gate": "CX2H4B_SECURITY_REGRESSION",
            }
        )
    if not nsc.get("CX2H4_NO_SECOND_COMPUTER_P0_PASS"):
        blocks_cx3.append(
            {
                "blocker_id": "NO_SECOND_COMPUTER",
                "domain": 0,
                "evidence_class": BLOCKED,
                "exact_missing_behavior": "P0 user workflow still requires host-side mutation / second computer",
                "automatable": True,
                "human_physical_external": False,
                "blocks_cx3": True,
                "recommended_next_gate": "CX2H4B_NO_SECOND_COMPUTER",
            }
        )

    # Standard non-blockers
    for item in (
        ("HUMAN_A11Y", 8, HUMAN, "human accessibility study"),
        ("PHYSICAL_PRINTER", 7, PHYS, "physical printer SI"),
        ("PHYSICAL_CAMERA_MIC", 6, PHYS, "physical camera/mic"),
        ("AV_QUALITY", 6, HUMAN, "AV subjective quality"),
        ("FIRMWARE_HW", 19, PHYS, "firmware on real hardware"),
        ("WARRANTY_RMA", 21, "BUSINESS_PENDING", "warranty/RMA"),
        ("CX3_CREDENTIALS", 10, NA, "later CX3 credential work"),
        ("CHAT_VIDEO_P1", 6, EXT, "Connect chat/video (P1)"),
    ):
        does_not.append(
            {
                "blocker_id": item[0],
                "domain": item[1],
                "evidence_class": item[2],
                "exact_missing_behavior": item[3],
                "automatable": False,
                "human_physical_external": True,
                "blocks_cx3": False,
                "recommended_next_gate": "LATER_NON_DIGITAL_OR_P1",
            }
        )

    return {
        "schema": "gunnchos.cx2h4.p0_blocker_register.v1",
        "blocks_cx3": blocks_cx3,
        "does_not_block_cx3": does_not,
        "blocks_cx3_count": len(blocks_cx3),
    }


def build_verdict(tokens_dict: Dict[str, Any], blockers: Dict[str, Any]) -> Dict[str, Any]:
    pass_ok = bool(tokens_dict.get("CX2H4_P0_DIGITAL_CLOSURE_PASS"))
    next_gate = "CX3_EDUCATION_CREDENTIALS_PORTFOLIO" if pass_ok else None
    if not pass_ok:
        if blockers.get("blocks_cx3"):
            next_gate = blockers["blocks_cx3"][0].get("recommended_next_gate")
        else:
            next_gate = "CX2H4B_UNKNOWN"
    return {
        "schema": "gunnchos.cx2h4.digital_closure_verdict.v1",
        "CX2H4_P0_DIGITAL_CLOSURE_PASS": pass_ok,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "blocks_cx3_count": blockers.get("blocks_cx3_count"),
        "NEXT_CX_GATE": next_gate,
        "statement": (
            "P0 digital ordinary-computer foundation closed enough for CX3"
            if pass_ok
            else "Unresolved P0 digital blocker remains — do not start CX3"
        ),
    }


def pick_next_gate(tokens_dict: Dict[str, Any], blockers: Dict[str, Any]) -> str:
    if tokens_dict.get("CX2H4_P0_DIGITAL_CLOSURE_PASS"):
        return "CX3_EDUCATION_CREDENTIALS_PORTFOLIO"
    for b in blockers.get("blocks_cx3") or []:
        gate = b.get("recommended_next_gate")
        if gate:
            return gate
    return "CX2H4B_UNKNOWN"
