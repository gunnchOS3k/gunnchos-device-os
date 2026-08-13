#!/usr/bin/env python3
"""gunnchAI tutor first-party package entry.

REQUIRED PLATFORM-001 ``run_gunnchai_tutor`` (companion_bridge contract).
Fails closed if the first-party tutor is missing — do not catch ImportError
and silently fall back to ``invoke_gunnchai_tutor_local``.

After a successful tutor run, stamp honest Nano/Fast/Pro inventory.
SmolLM2-135M Q4_K_M 512-ctx is Nano fallback only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GUNNCHOS_REPO_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.first_party_apps.gunnchai_tutor import run_gunnchai_tutor  # noqa: E402
from gunnchos_device_os.phase_xiv.local_ai import (  # noqa: E402
    LocalAiRuntime,
    ModelRegistry,
)

# Pinned to accepted gunnchAI3k main after #32 (do not copy gunnchAI wholesale).
GUNNCHAI_OWNER_MAIN_SHA = "c483a45197cbe3bd4a3d68d06c91fd86494c2992"
GUNNCHAI_32_IMPL_SHA = "11ead1aa4d4d311564ca659ef4f79ac8b9c04065"


def _llama_enabled() -> bool:
    return os.environ.get("GUNNCHOS_ENABLE_LLAMA_TIER", "").lower() in {"1", "true", "yes"}


def _stamp_intelligence(result: dict) -> dict:
    """Annotate tutor output with honest local-AI inventory. Does not replace execution."""
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    rt = LocalAiRuntime(ModelRegistry(data_dir / "local_ai_registry"), timeout_s=8)
    # Packaging smoke must stay fast: only hash/run GGUF when llama tier is opted in.
    rt.ensure_default_models(ROOT, include_llama=_llama_enabled())
    inventory = dict(rt.intelligence_inventory())
    inventory["owner_gunnchai_sha"] = os.environ.get(
        "GUNNCHOS_GUNNCHAI_OWNER_SHA", GUNNCHAI_OWNER_MAIN_SHA
    )
    inventory["gunnchai_32_impl_sha"] = os.environ.get(
        "GUNNCHOS_GUNNCHAI_32_IMPL_SHA", GUNNCHAI_32_IMPL_SHA
    )
    inventory["weights_present"] = {
        "nano": bool((inventory.get("nano") or {}).get("present")),
        "fast": bool((inventory.get("fast") or {}).get("present")),
        "pro": bool((inventory.get("pro") or {}).get("present")),
    }
    inventory["nano_fallback_only"] = bool(
        (inventory.get("nano") or {}).get("is_nano_fallback_only")
    )
    result = dict(result)
    result.setdefault("intelligence", inventory)
    result["GUNNCHAI_APP_PRODUCT_COMPLETE"] = False
    result["HUMAN_E6"] = False
    result["smollm2_is_full_intelligence_layer"] = False
    result["stub_content"] = False
    result["tutor_entrypoint"] = "first_party_run_gunnchai_tutor"
    return result


def main() -> int:
    os.environ.setdefault(
        "GUNNCHOS_APP_PERMISSIONS",
        "storage_read,storage_write,ai_interface",
    )
    crash = "--crash-probe" in sys.argv
    result = run_gunnchai_tutor(crash_probe=crash)
    if result.get("ok"):
        result = _stamp_intelligence(result)
    else:
        result = dict(result)
        result["tutor_entrypoint"] = "first_party_run_gunnchai_tutor"
        result["GUNNCHAI_APP_PRODUCT_COMPLETE"] = False
        result["HUMAN_E6"] = False
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    out = data_dir / "gunnchai_tutor_run.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": bool(result.get("ok")),
                "app_id": "gunnchos.gunnchai_tutor",
                "stub_content": False,
                "persisted_session_count": result.get("persisted_session_count"),
                "tutor_entrypoint": result.get("tutor_entrypoint"),
                "preferred_daily_tier": (result.get("intelligence") or {}).get(
                    "preferred_daily_tier"
                ),
                "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
                "HUMAN_E6": False,
                "wrote": str(out),
            }
        )
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
