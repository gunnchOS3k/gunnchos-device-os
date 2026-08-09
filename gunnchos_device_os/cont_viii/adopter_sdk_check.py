"""Adopter SDK presence + package/test surface (Lane G)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_ADOPTER_SDK_PASS

REQUIRED = (
    "sdk/README.md",
    "sdk/.env.example",
    "sdk/gunnchos_adopter_sdk/__init__.py",
    "sdk/gunnchos_adopter_sdk/client.py",
    "sdk/samples/app_template/README.md",
    "sdk/samples/ring_input/sample.py",
    "sdk/samples/device_role/sample.py",
    "sdk/samples/ai/sample.py",
    "sdk/samples/connectivity/sample.py",
    "sdk/samples/telemetry/sample.py",
    "sdk/tests/test_sdk_client.py",
    "sdk/pyproject.toml",
)


def evaluate_adopter_sdk(root: Path | None = None) -> dict[str, Any]:
    root = root or Path(__file__).resolve().parents[2]
    present = {rel: (root / rel).exists() for rel in REQUIRED}
    # Import client digitally
    import sys
    sys.path.insert(0, str(root / "sdk"))
    client_ok = False
    detail = {}
    try:
        from gunnchos_adopter_sdk.client import AdopterClient
        c = AdopterClient(base_url="http://127.0.0.1:9", api_version="1.0.0")
        nego = c.negotiate("device_role", "1.0.0")
        client_ok = bool(nego.get("ok"))
        detail = {"negotiate": nego}
    except Exception as exc:  # noqa: BLE001
        detail = {"error": str(exc)}
    ok = all(present.values()) and client_ok
    return {
        "schema": "gunnchos.adopter_sdk.v1",
        "ok": ok,
        "token": TOKEN_ADOPTER_SDK_PASS if ok else None,
        "present": present,
        "missing": [k for k, v in present.items() if not v],
        "client": detail,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
