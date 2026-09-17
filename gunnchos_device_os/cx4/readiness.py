"""Materialize CX4 human/physical/external readiness packets (preparation ≠ PASS)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx4.paths import ensure_lab_tree, evidence_root, readiness_docs_root, repo_root_from_here

HW_SIBLING = Path(
    "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/gunnchos-hardware-industrial-design"
)

SURFACES = [
    "Home",
    "Vault",
    "App Center",
    "Browser",
    "Mail",
    "Writer",
    "Wallet",
    "Portfolio",
    "Career Profile",
    "Verifier",
    "Care",
    "Assist",
]

SKUS = [
    "Student 14.5",
    "Handheld Hybrid",
    "DS-XL Coder",
    "Edge I/O Rings",
    "first-party Dock",
]


def _w(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not text.endswith("\n"):
        text += "\n"
    path.write_text(text)
    return str(path)


def write_human_a11y_packet(docs: Path, lab: Path) -> Dict[str, Any]:
    md = docs / "HUMAN_A11Y_VALIDATION_PACKET.md"
    schema = docs / "HUMAN_A11Y_RESULT_SCHEMA.json"
    issue = lab / "work" / "a11y" / "ISSUE_TEMPLATE.md"
    form = lab / "work" / "a11y" / "OBSERVATION_FORM.md"
    surfaces = "\n".join(f"- {s}" for s in SURFACES)
    body = f"""# Human Accessibility Validation Packet (CX4.0)

**Status:** preparation only.
**Class:** `J6_CLASS=HUMAN_VALIDATION_PENDING`
**Never set:** `human_a11y_pass=true` from automation or this packet alone.

Automation already earned `CX3_AUTOMATED_A11Y_PASS=true`. This packet is for **human** validation.

## Plan (not completed evidence)

- Minimum participant recommendation (plan): **6** participants covering screen-reader, keyboard-only, low-vision, captions/hearing, motor/switch, cognitive/reading needs.
- This count is a **plan**, not executed evidence.

## Surfaces under test

{surfaces}

## Participant instructions

1. Read consent/privacy notes below; confirm voluntary participation.
2. Use the assigned modality only for the assigned block (keyboard-only / SR / zoom / etc.).
3. Follow the task script; do not skip error/recovery tasks.
4. Record observations in the observation form; file issues with the template.
5. Store evidence using the naming convention.

## Consent / privacy notes

- Collect only accessibility observations needed for product improvement.
- Do not capture passwords, credentials, personal portfolio content, or minors' data.
- Redact screenshots that show personal names/emails before upload.
- Participant may stop at any time.

## Task script (per surface)

For each surface above:

1. Navigate using the assigned modality.
2. Confirm focus visibility on interactive controls.
3. Complete one primary task (open/view/edit/export as applicable).
4. Trigger one recoverable error and recover.
5. Note focus traps, missing names/roles, contrast failures, or SR silence.

### Keyboard-only tasks
- Tab/Shift-Tab through primary nav; verify order and visibility.
- Activate each primary surface without pointer.
- Escape/back returns predictably; no keyboard trap.

### Screen-reader tasks (where supported)
- Launch Orca or platform SR.
- Confirm surface title/landmark announcement.
- Confirm actionable controls expose accessible names/roles.
- Confirm status messages are announced.

### Zoom / text-scaling
- 150% and 200% scaling: layout remains usable; no clipped critical controls.

### Color / contrast observation prompts
- Primary text/icons against backgrounds meet expected contrast in default + contrast mode.
- Focus ring remains visible in contrast mode.

### Error / recovery
- Deny a permission or cancel a dialog; user can continue.
- Offline banner/state is perceivable via keyboard/SR.

## Completion criteria (human PASS rule — not auto-claimable)

Human a11y PASS requires uploaded observation forms for the planned participant set, zero unresolved severity-1 issues, and signed facilitator attestation. **This campaign does not claim that PASS.**

## Severity rubric

| Sev | Definition |
|-----|------------|
| 1 | Blocks task completion for the modality |
| 2 | Major barrier with workaround |
| 3 | Minor annoyance / polish |
| 4 | Suggestion |

## Evidence naming convention

`cx4_a11y_<participantId>_<surface>_<modality>_<YYYYMMDD>_<seq>.{{png,log,md}}`

Upload to: `artifacts/complete_experience/cx4_0/human_a11y/` (created at execution time).

## Facilitator checklist

- [ ] Consent recorded
- [ ] Environment recorded (device profile, SR version, zoom level)
- [ ] Tasks completed per surface
- [ ] Issues filed
- [ ] Evidence uploaded
"""
    schema_obj = {
        "schema": "gunnchos.cx4.human_a11y_result.v1",
        "human_a11y_pass": False,
        "J6_CLASS": "HUMAN_VALIDATION_PENDING",
        "note": "Result schema for future human sessions — preparation must not set pass true.",
        "required_fields": [
            "participant_id",
            "modality",
            "surface",
            "tasks",
            "severity",
            "issues",
            "evidence_paths",
            "facilitator_attestation",
        ],
        "pass_rule": "planned_participants_complete AND severity1_open==0 AND attestation==true",
    }
    paths = [
        _w(md, body),
        _w(schema, json.dumps(schema_obj, indent=2)),
        _w(
            issue,
            "# A11y issue template\n\n- Surface:\n- Modality:\n- Severity (1-4):\n- Steps:\n- Expected:\n- Actual:\n- Evidence:\n- Participant ID:\n",
        ),
        _w(
            form,
            "# Observation form\n\nParticipant ID:\nModality:\nDevice profile:\nSR/zoom/switch:\nNotes:\nBlockers:\n",
        ),
        str(lab / "harnesses" / "collect_a11y_evidence.sh"),
    ]
    return {"ready": True, "paths": paths, "J6_CLASS": "HUMAN_VALIDATION_PENDING", "human_a11y_pass": False}


def write_printer_packet(docs: Path, lab: Path) -> Dict[str, Any]:
    md = docs / "PHYSICAL_PRINTER_VALIDATION_PACKET.md"
    paths = [
        _w(
            md,
            """# Physical Printer Validation Packet (CX4.0)

Digital CUPS/IPP already proven. This packet is for **real printers**.

`PHYSICAL_PRINTER_PENDING=true` — do not set physical printer PASS from collectors alone.

## Paths
- USB printer path
- LAN / IPP Everywhere path (when hardware supports it)

## Field script
1. Discovery (USB + network)
2. Add/configure printer in user UI
3. Print Writer document
4. Print PDF
5. Queue inspect / cancel
6. Paper-out simulation + recovery
7. Printer-offline + reconnect
8. Duplex/color where applicable
9. Restart session — persistence
10. Accessibility of print dialogs
11. User-visible recovery messaging

## Automated collectors
`os_build/cx4_linux_lab/harnesses/collect_cups_physical_evidence.sh`

## Pass rule (future)
Physical printer PASS requires successful USB or LAN path on real hardware with captured job IDs + physical output photos/hashes and no severity-1 recovery failures.
""",
        ),
        str(lab / "harnesses" / "collect_cups_physical_evidence.sh"),
    ]
    return {"ready": True, "PHYSICAL_PRINTER_PENDING": True, "physical_printer_pass": False, "paths": paths}


def write_av_packet(docs: Path, lab: Path) -> Dict[str, Any]:
    paths = [
        _w(
            docs / "CAMERA_MIC_AV_VALIDATION_PACKET.md",
            """# Camera / Microphone / AV Physical Validation Packet (CX4.0)

`PHYSICAL_CAMERA_MIC_AV_PENDING=true`
Do not claim audiovisual quality without human/physical evidence.
Device enumeration fixtures ≠ physical PASS.

## Field tests
- camera discovery / preview / photo-frame capture
- microphone discovery / record / playback
- browser permission allow/deny
- meeting-app permission flow
- hot-plug/unplug
- audio output / headphones / Bluetooth if supported
- failure/recovery
- privacy indicator/state
- restart persistence

## Automated collectors
`collect_av_diagnostics.sh` — V4L2, PipeWire/WirePlumber, audio graph snapshots.
""",
        ),
        str(lab / "harnesses" / "collect_av_diagnostics.sh"),
    ]
    return {"ready": True, "PHYSICAL_CAMERA_MIC_AV_PENDING": True, "paths": paths}


def write_peripheral_packet(docs: Path, lab: Path) -> Dict[str, Any]:
    matrix = {
        "schema": "gunnchos.cx4.peripheral_matrix.v1",
        "physical_pass": False,
        "devices": [
            {
                "id": d,
                "checks": [
                    "discovery",
                    "connect",
                    "input_or_state_mutation",
                    "disconnect",
                    "reconnect",
                    "suspend_resume_if_applicable",
                    "restart",
                    "permissions",
                    "failure_recovery",
                ],
            }
            for d in [
                "keyboard",
                "mouse",
                "touch",
                "gamepad",
                "usb_storage",
                "bluetooth",
                "display_hdmi_dp",
                "dock",
                "ring_devices",
            ]
        ],
    }
    paths = [
        _w(
            docs / "PHYSICAL_PERIPHERAL_VALIDATION_PACKET.md",
            """# Physical Peripheral Validation Packet (CX4.0)

Physical PASS remains false until real hardware sessions complete.

## Matrix
Keyboard, mouse, touch, gamepad/controller, USB storage, Bluetooth, display/HDMI/DP, dock, Ring devices.

For each: discovery → connect → input/state mutation → disconnect → reconnect → suspend/resume → restart → permissions → failure/recovery.
""",
        ),
        _w(docs / "PHYSICAL_PERIPHERAL_MATRIX.json", json.dumps(matrix, indent=2)),
        str(lab / "harnesses" / "collect_peripheral_matrix.sh"),
    ]
    return {"ready": True, "physical_pass": False, "paths": paths}


def write_device_quartet_packets(docs: Path) -> Dict[str, Any]:
    paths = []
    grounding = {
        "hardware_sibling": str(HW_SIBLING),
        "device_dirs_present": {
            "student_14_5": (HW_SIBLING / "devices" / "student_14_5").is_dir(),
            "handheld_hybrid": (HW_SIBLING / "devices" / "handheld_hybrid").is_dir(),
            "ds_xl_coder": (HW_SIBLING / "devices" / "ds_xl_coder").is_dir(),
            "edge_io_rings": (HW_SIBLING / "device_designs" / "edge_io_rings").is_dir(),
            "dock": (HW_SIBLING / "device_designs" / "dock").is_dir(),
        },
        "evt_dvt_pvt_plan": str(HW_SIBLING / "docs" / "13_EVT_DVT_PVT_AND_CERTIFICATION_PLAN.md"),
        "hardware_fabricated": False,
        "EVT_PENDING": True,
        "DVT_PENDING": True,
        "PVT_PENDING": True,
        "evt_pass": False,
        "dvt_pass": False,
        "pvt_pass": False,
    }
    paths.append(_w(docs / "DEVICE_QUARTET_GROUNDING.json", json.dumps(grounding, indent=2)))
    for sku in SKUS:
        slug = (
            sku.lower()
            .replace(" ", "_")
            .replace("/", "_")
            .replace("-", "_")
        )
        paths.append(
            _w(
                docs / f"EVT_{slug}.md",
                f"""# EVT Packet — {sku}

`EVT_PENDING=true` · `evt_pass=false` · Do not fabricate hardware.

## Gates
- board bring-up, power rails, boot, display/input, thermal baseline, I/O, radios present, firmware recovery

## Also
- RF validation readiness, battery transport readiness, ergonomics, drop/mechanical, charging, repairability

Grounded (read-only) on hardware-industrial-design sibling where present.
""",
            )
        )
        paths.append(
            _w(
                docs / f"DVT_{slug}.md",
                f"""# DVT Packet — {sku}

`DVT_PENDING=true` · `dvt_pass=false`

## Gates
- sustained workloads, sleep/resume, thermal/power, mechanical, display/input consistency, dock/accessory, wireless coexistence
""",
            )
        )
        paths.append(
            _w(
                docs / f"PVT_{slug}.md",
                f"""# PVT Packet — {sku}

`PVT_PENDING=true` · `pvt_pass=false` · No mass-manufacturing claim.

## Gates
- manufacturing repeatability, provisioning, test fixtures, serialization, factory diagnostics, packaging
""",
            )
        )
    paths.append(_w(docs / "EVT_PACKET.md", "# EVT readiness index\n\nSee per-SKU `EVT_*.md`. `EVT_PENDING=true`.\n"))
    paths.append(_w(docs / "DVT_PACKET.md", "# DVT readiness index\n\nSee per-SKU `DVT_*.md`. `DVT_PENDING=true`.\n"))
    paths.append(_w(docs / "PVT_PACKET.md", "# PVT readiness index\n\nSee per-SKU `PVT_*.md`. `PVT_PENDING=true`.\n"))
    return {"ready": True, "EVT_PENDING": True, "DVT_PENDING": True, "PVT_PENDING": True, "paths": paths}


def write_firmware_packet(docs: Path, lab: Path) -> Dict[str, Any]:
    paths = [
        _w(
            docs / "FIRMWARE_LIFECYCLE_PACKET.md",
            """# Firmware / Driver Lifecycle Packet (CX4.0)

Digital tooling for inventory, version reporting, upgrade, rollback, failed-update recovery,
signed-image verification (where architecture supports), driver inventory, health diagnostics,
support bundle capture.

Simulation fixtures may validate harnesses only — **simulation ≠ physical PASS**.
""",
        ),
        str(lab / "harnesses" / "firmware_lifecycle_sim.py"),
    ]
    return {"ready": True, "physical_pass": False, "paths": paths}


def write_support_repair_packets(docs: Path, lab: Path) -> Dict[str, Any]:
    paths = [
        _w(
            docs / "SUPPORT_BUNDLE_GENERATOR.md",
            """# Support Bundle Generator (CX4.0)

Automatable: inventory, recent logs, app/provider health, network/storage diagnostics,
redaction rules, user consent before export, integrity hash.

Operational warranty/RMA business function is **not** claimed as established.
""",
        ),
        _w(
            docs / "REPAIR_RMA_PACKET.md",
            """# Repair / RMA / Warranty Evidence Packet (CX4.0)

Includes troubleshooting tree, repair intake template, device reset/recovery guide,
backup-before-service path, RMA evidence schema, warranty claim evidence schema.

`operational_business_gates_pending=true` — packet readiness ≠ business ops PASS.
""",
        ),
        _w(
            docs / "RMA_EVIDENCE_SCHEMA.json",
            json.dumps(
                {
                    "schema": "gunnchos.cx4.rma_evidence.v1",
                    "operational_pass": False,
                    "fields": [
                        "device_serial",
                        "failure_symptom",
                        "support_bundle_hash",
                        "customer_consent",
                        "backup_attestation",
                        "intake_id",
                    ],
                },
                indent=2,
            ),
        ),
        _w(
            docs / "WARRANTY_CLAIM_SCHEMA.json",
            json.dumps(
                {
                    "schema": "gunnchos.cx4.warranty_claim.v1",
                    "operational_pass": False,
                    "fields": ["device_serial", "purchase_proof", "defect_class", "support_bundle_hash"],
                },
                indent=2,
            ),
        ),
        _w(
            docs / "TROUBLESHOOTING_TREE.md",
            """# Troubleshooting tree (prep)

1. Power/boot → 2. Display/input → 3. Network → 4. App/provider health → 5. Storage → 6. Capture support bundle (with consent) → 7. Repair intake / RMA if hardware fault.
""",
        ),
        _w(
            docs / "REPAIR_INTAKE_TEMPLATE.md",
            """# Repair intake template

- Device serial:
- Symptom:
- Repro steps:
- Support bundle hash:
- Backup-before-service completed (Y/N):
- Customer consent (Y/N):
""",
        ),
        _w(
            docs / "DEVICE_RESET_RECOVERY_GUIDE.md",
            """# Device reset / recovery guide (prep)

1. Backup via Vault/Care UI
2. Confirm backup integrity
3. Initiate reset from Care
4. Re-provision
5. Restore selected data
6. Verify provider reopen
""",
        ),
        str(lab / "harnesses" / "generate_support_bundle.py"),
    ]
    return {"ready": True, "operational_pass": False, "paths": paths}


def write_chat_meeting_packet(docs: Path) -> Dict[str, Any]:
    contracts = {
        "schema": "gunnchos.cx4.chat_meeting_provider_contracts.v1",
        "J4_CLASS_retained": "REAL_PROVIDER_GUI_PARTIAL",
        "adapters": [
            {"id": "chat_messaging", "class": "CONTRACT_PASS"},
            {"id": "meeting_join", "class": "CONTRACT_PASS"},
            {"id": "calendar_invite_to_meeting", "class": "CONTRACT_PASS"},
            {"id": "contact_to_message", "class": "CONTRACT_PASS"},
            {"id": "file_share_handoff", "class": "CONTRACT_PASS"},
            {"id": "external_commercial_provider", "class": "EXTERNAL_PROVIDER_PENDING"},
        ],
        "external_provider_integration_pass": False,
        "lab_provider_digital_ok": True,
        "note": "Contracts/readiness only; do not rewrite J4 without genuine evidence.",
    }
    paths = [
        _w(docs / "CHAT_MEETING_PROVIDER_READINESS.json", json.dumps(contracts, indent=2)),
        _w(
            docs / "CHAT_MEETING_PROVIDER_READINESS.md",
            """# Chat / Meeting Provider Readiness (CX4.0)

Provider-neutral adapters/contracts for chat, meeting join, calendar→meeting, contact→message, file share.

Lab provider may be digitally qualified; external commercial providers remain `EXTERNAL_PROVIDER_PENDING`.

`external_provider_integration_pass=false` — readiness ≠ integration PASS.
""",
        ),
    ]
    return {
        "ready": True,
        "CX4_CHAT_MEETING_PROVIDER_READINESS_PASS": True,
        "external_provider_integration_pass": False,
        "paths": paths,
    }


def write_issuer_packet(docs: Path) -> Dict[str, Any]:
    paths = [
        _w(
            docs / "CX4_INSTITUTIONAL_ISSUER_ONBOARDING.md",
            """# Institutional Issuer Onboarding (CX4.0)

`certification_claimed=false` — no Open Badges / CLR conformance claim.

## Packet contents
- Open Badges-inspired adapter mapping (inspired only)
- CLR-inspired aggregation mapping (inspired only)
- Issuer onboarding checklist
- Public-key / trust exchange expectations
- Revocation / status endpoint expectations
- Privacy / security review prompts
- Credential evidence contract
- Conformance test **placeholder** (not a certification)

## Checklist
1. Legal entity + data controller identified
2. Key ceremony / public key publication plan
3. Evidence binding policy
4. Revocation endpoint SLA
5. Privacy DPIA prompt
6. Sandbox interoperability dry-run
""",
        )
    ]
    return {"ready": True, "certification_claimed": False, "paths": paths}


def write_privacy_rights(docs: Path) -> Dict[str, Any]:
    privacy = {
        "schema": "gunnchos.cx4.privacy_review_register.v1",
        "legal_approval": False,
        "categories": [
            "personal_data",
            "credential_education_data",
            "minors_k12_boundary",
            "telemetry",
            "support_bundles",
            "camera_mic",
            "external_provider_data",
            "public_portfolio_share",
            "retention_deletion",
            "consent",
        ],
        "note": "Register only — no legal conclusions.",
    }
    rights = {
        "schema": "gunnchos.cx4.rights_register.v1",
        "legal_approval": False,
        "items": ["music", "game_assets", "fonts", "third_party_datasets", "external_apis", "trademarks_logos"],
        "note": "Register only — no legal conclusions.",
    }
    paths = [
        _w(docs / "PRIVACY_REVIEW_REGISTER.json", json.dumps(privacy, indent=2)),
        _w(docs / "RIGHTS_REGISTER.json", json.dumps(rights, indent=2)),
    ]
    return {"ready": True, "legal_approval": False, "paths": paths}


def write_cert_mfg(docs: Path) -> Dict[str, Any]:
    cert = {
        "schema": "gunnchos.cx4.certification_matrix.v1",
        "certified": False,
        "certification_claimed": False,
        "rows": [
            {
                "requirement": r,
                "status": "PENDING",
                "owner": "TBD",
                "lab": "TBD",
                "prerequisite_hardware_maturity": "EVT+",
                "evidence_artifact": "TBD",
                "product_sku": "Device Quartet",
            }
            for r in [
                "FCC",
                "CE/RED",
                "Bluetooth SIG",
                "Wi-Fi Alliance",
                "USB-IF",
                "carrier/operator",
                "battery UN 38.3",
                "safety/environmental",
                "SAR/RF exposure",
                "packaging/labeling",
            ]
        ],
    }
    mfg = {
        "schema": "gunnchos.cx4.manufacturing_readiness.v1",
        "manufacturing_pass": False,
        "pvt_pass": False,
        "sections": [
            "BOM ownership schema",
            "approved vendor list schema",
            "manufacturing test requirements",
            "provisioning",
            "serialization",
            "secure key injection architecture",
            "calibration needs",
            "factory acceptance test",
            "yield metrics",
            "nonconformance/RMA feedback",
            "packaging test requirements",
            "software-image release handoff",
        ],
        "note": "No mass-manufacturing readiness claim.",
    }
    paths = [
        _w(docs / "CERTIFICATION_MATRIX.json", json.dumps(cert, indent=2)),
        _w(docs / "MANUFACTURING_PACKET.json", json.dumps(mfg, indent=2)),
        _w(docs / "CERTIFICATION_MATRIX.md", "# Certification matrix\n\nRequirements only. `certified=false`.\n"),
        _w(docs / "MANUFACTURING_PACKET.md", "# Manufacturing readiness\n\n`manufacturing_pass=false` · `pvt_pass=false`.\n"),
    ]
    return {"ready": True, "certified": False, "manufacturing_pass": False, "paths": paths}


def materialize_all_packets(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    docs = readiness_docs_root(repo)
    lab = ensure_lab_tree(repo)
    docs.mkdir(parents=True, exist_ok=True)
    out: Dict[str, Any] = {
        "schema": "gunnchos.cx4.readiness_materialization.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
    }
    out["human_a11y"] = write_human_a11y_packet(docs, lab)
    out["printer"] = write_printer_packet(docs, lab)
    out["av"] = write_av_packet(docs, lab)
    out["peripherals"] = write_peripheral_packet(docs, lab)
    out["device_quartet"] = write_device_quartet_packets(docs)
    out["firmware"] = write_firmware_packet(docs, lab)
    out["support_repair"] = write_support_repair_packets(docs, lab)
    out["chat_meeting"] = write_chat_meeting_packet(docs)
    out["issuer"] = write_issuer_packet(docs)
    out["privacy_rights"] = write_privacy_rights(docs)
    out["cert_mfg"] = write_cert_mfg(docs)
    index = {
        "docs_root": str(docs),
        "packets": {k: v.get("ready") for k, v in out.items() if isinstance(v, dict) and "ready" in v},
        "pending_gates": {
            "J6_CLASS": "HUMAN_VALIDATION_PENDING",
            "PHYSICAL_PRINTER_PENDING": True,
            "PHYSICAL_CAMERA_MIC_AV_PENDING": True,
            "EVT_PENDING": True,
            "DVT_PENDING": True,
            "PVT_PENDING": True,
            "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        },
    }
    _w(docs / "README.md", "# CX4 readiness packets\n\nPreparation only. Readiness ≠ PASS for human/physical/external gates.\n")
    _w(docs / "INDEX.json", json.dumps(index, indent=2))
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "CX4_READINESS_MATERIALIZATION.json").write_text(json.dumps(out, indent=2) + "\n")
    return out
