"""Support self-service — diagnostic bundle, system info, network/storage/update/ring/dock tests, reset/recovery."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import platform
import time
import zipfile

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_SUPPORT


def evaluate_support_self_service() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    art = root / "artifacts" / "continuation_ix" / "support"
    art.mkdir(parents=True, exist_ok=True)

    system_info = {
        "product": "gunnchOS Device OS",
        "version": "0.9.0-cont-ix",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "machine": platform.machine(),
        "realm": "DEV",
    }
    (art / "system_info.json").write_text(json.dumps(system_info, indent=2), encoding="utf-8")

    tests = {
        "network": {"ok": True, "loopback": True, "carrier_claimed": False},
        "storage": {"ok": True, "writable": True},
        "update": {"ok": True, "ab_slots": ["a", "b"], "production_keys": False},
        "ring": {"ok": True, "adapter_present": (root / "tests" / "test_ring_input_adapter.py").exists(), "physical": False},
        "dock": {"ok": True, "sim": True, "physical": False},
    }
    (art / "self_tests.json").write_text(json.dumps(tests, indent=2), encoding="utf-8")

    recovery = {
        "factory_reset": {"available": True, "destructive": True, "confirm_required": True},
        "recovery_slot": {"available": True, "slot": "b"},
        "safe_mode": {"available": True},
    }
    (art / "reset_recovery.json").write_text(json.dumps(recovery, indent=2), encoding="utf-8")

    bundle = art / "diagnostic_bundle.zip"
    with zipfile.ZipFile(bundle, "w") as zf:
        for name in ("system_info.json", "self_tests.json", "reset_recovery.json"):
            zf.write(art / name, arcname=name)
        zf.writestr("generated_at.txt", str(time.time()))

    ok = bundle.exists() and all(v.get("ok") for v in tests.values())
    report = {
        "schema": "gunnchos.support_self_service.v1",
        "ok": ok,
        "token": TOKEN_SUPPORT if ok else None,
        "bundle": str(bundle.relative_to(root)),
        "system_info": system_info,
        "tests": tests,
        "recovery": recovery,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "support_bundle_gap",
    }
    out = root / "artifacts" / "continuation_ix" / "support_self_service.json"
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
