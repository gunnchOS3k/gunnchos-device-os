#!/usr/bin/env python3
"""Support bundle generator with redaction + consent gate (prep)."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

REDACT_KEYS = {"password", "token", "secret", "private_key", "ssn"}


def redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if k.lower() in REDACT_KEYS else redact(v)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def generate(out: Path, *, consent: bool, inventory: dict | None = None) -> dict:
    if not consent:
        return {"ok": False, "blocker": "USER_CONSENT_REQUIRED", "operational_pass": False}
    out.mkdir(parents=True, exist_ok=True)
    body = {
        "schema": "gunnchos.cx4.support_bundle.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "inventory": redact(inventory or {"hw": "unknown", "sw": "cx4-tip"}),
        "consent": True,
        "operational_pass": False,
    }
    raw = json.dumps(body, indent=2) + "\n"
    digest = hashlib.sha256(raw.encode()).hexdigest()
    body["integrity_sha256"] = digest
    path = out / f"support_bundle_{digest[:12]}.json"
    path.write_text(json.dumps(body, indent=2) + "\n")
    return {"ok": True, "path": str(path), "integrity_sha256": digest, "operational_pass": False}


if __name__ == "__main__":
    import sys

    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("artifacts/complete_experience/cx4_0/support")
    print(json.dumps(generate(target, consent=True), indent=2))
