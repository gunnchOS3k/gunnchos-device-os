"""Boot evidence assembly and status tokens."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

STATUS_SOFTWARE_PASS = "GUNNCHOS_BOOT_SOFTWARE_PATH_PASS"
STATUS_SOFTWARE_FAIL = "GUNNCHOS_BOOT_SOFTWARE_PATH_FAIL"
STATUS_PHYSICAL_PENDING = "GUNNCHOS_PHYSICAL_BOOT_PENDING"


def build_boot_evidence(probe_evidence: dict[str, Any]) -> dict[str, Any]:
    """Normalize probe output into the published evidence document."""
    doc = dict(probe_evidence)
    doc.setdefault("schema", "gunnchos.boot_evidence.v1")
    tokens = list(doc.get("status_tokens") or [])
    if STATUS_PHYSICAL_PENDING not in tokens:
        tokens.append(STATUS_PHYSICAL_PENDING)
    doc["status_tokens"] = tokens
    doc["physical_boot"] = False
    return doc


def write_evidence(path: Path | str, evidence: dict[str, Any]) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
