"""Write CX2G evidence exclusively under artifacts/complete_experience/cx2g/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2g import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2g.journeys import upgrade_journeys
from gunnchos_device_os.cx2g.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx2g.tokens import Cx2gTokens


def next_gate(tokens: Cx2gTokens, journeys: Dict[str, Any]) -> str:
    if (
        tokens.gate_shell_stack()
        and journeys.get("desired_before_cx3_pass")
    ):
        return "CX3_EDUCATION_CREDENTIALS_PORTFOLIO"
    if tokens.lab_blocker:
        frag = tokens.lab_blocker.split(":")[0].strip().replace(" ", "_")[:80]
        if frag.startswith("CX2G_"):
            frag = frag[5:]
        elif frag.startswith("CX2H_"):
            frag = frag[5:]
        elif frag.startswith("CX2"):
            # strip CX2X_ prefix if present
            parts = frag.split("_", 1)
            frag = parts[1] if len(parts) > 1 else frag
        return "CX2H_" + frag
    if not tokens.CX2G_NON_CLOUD_KERNEL_BOOT_PASS:
        return "CX2H_NON_CLOUD_KERNEL_BOOT"
    if not tokens.CX2G_DRM_CARD_PASS:
        return "CX2H_DRM_CARD"
    if not tokens.CX2G_WESTON_DRM_PASS:
        return "CX2H_WESTON_DRM"
    if not tokens.CX2G_GUNNCH_SHELL_RENDER_PASS:
        return "CX2H_SHELL_RENDER_OR_CAPTURE_NOT_PROVEN"
    if not tokens.CX2G_QEMU_FRAMEBUFFER_CAPTURE_PASS:
        return "CX2H_FRAMEBUFFER_CAPTURE"
    if not tokens.CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS:
        return "CX2H_INPUT_TO_SHELL_MUTATION"
    return "CX2H_JOURNEY_DIGITAL_PASS_INCOMPLETE"


def write_evidence(repo: Optional[Path], tokens: Cx2gTokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    root = evidence_root(repo)
    root.mkdir(parents=True, exist_ok=True)
    journeys = upgrade_journeys(facts)
    for jid, j in journeys["journeys"].items():
        setattr(tokens, f"{jid}_CLASS", j["cx2g_class"])
    gate = next_gate(tokens, journeys)
    generated = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def dump(name: str, obj: Any) -> None:
        (root / name).write_text(json.dumps(obj, indent=2) + "\n")

    # Individual artifacts
    for key in (
        "CX2G_KERNEL_SELECTION",
        "CX2G_DRM_PROBE",
        "CX2G_QEMU_GRAPHICS",
        "CX2G_WESTON_DRM_SESSION",
        "CX2G_SHELL_RUNTIME_TARGET",
        "CX2G_SHELL_RENDER_PROOF",
        "CX2G_FRAMEBUFFER_CAPTURE_MANIFEST",
        "FRAMEBUFFER_DIFF_REPORT",
        "CX2G_INPUT_TO_SHELL_PROOF",
        "ATSPI_SHELL_TREE",
        "CX2G_XDG_PORTAL_MATRIX",
        "CX2G_PROVIDER_GUI_PROBES",
    ):
        if key in facts:
            dump(f"{key}.json" if not key.endswith(".json") else key, facts[key])

    dump("CX2G_JOURNEYS.json", journeys)
    dump("CX2G_TOKENS.json", tokens.to_dict())

    report = {
        "schema": "gunnchos.cx2g.evidence_report.v1",
        "generated_at_utc": generated,
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "production_shell": "apps/gunnch_shell",
        "journeys": journeys,
        "tokens": tokens.to_dict(),
        "firewall": {
            "device_lab_134_unaltered": tokens.CX2G_DEVICE_LAB_134_UNALTERED,
            "portal_14_15_unaltered": tokens.CX2G_PORTAL_14_UNALTERED and tokens.CX2G_PORTAL_15_UNALTERED,
            "device_lab_manifest_unaltered": tokens.CX2G_DEVICE_LAB_MANIFEST_UNALTERED,
            "evidence_path": "artifacts/complete_experience/cx2g",
            "no_merges": tokens.CX2G_NO_MERGES,
            "cx2e_overlay_immutable": True,
        },
        "NEXT_CX_GATE": gate,
        "lab_blocker": tokens.lab_blocker,
        "facts_keys": sorted(facts.keys()),
    }
    dump("CX2G_EVIDENCE_REPORT.json", report)
    (root / "README.md").write_text(
        "# CX2G evidence\n\nNon-cloud kernel + DRM Weston + gunnch_shell render/capture.\n"
        "`FULL_COMPLETE_EXPERIENCE_COMPLETE=false`\n"
    )
    return report
