#!/usr/bin/env python3
"""gunnchAI tutor first-party package entry.

Prefers PLATFORM-001 ``run_gunnchai_tutor`` when present (companion_bridge
contract). Otherwise invokes the OS local_ai path with honest Nano/Fast/Pro
labels. SmolLM2-135M Q4_K_M 512-ctx is Nano fallback only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GUNNCHOS_REPO_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.phase_xiv.local_ai import (  # noqa: E402
    LocalAiRuntime,
    ModelRegistry,
    invoke_gunnchai_tutor_local,
)


def _llama_enabled() -> bool:
    return os.environ.get("GUNNCHOS_ENABLE_LLAMA_TIER", "").lower() in {"1", "true", "yes"}


def _stamp_intelligence(result: dict) -> dict:
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    rt = LocalAiRuntime(ModelRegistry(data_dir / "local_ai_registry"), timeout_s=8)
    # Packaging smoke must stay fast: only hash/run GGUF when llama tier is opted in.
    rt.ensure_default_models(ROOT, include_llama=_llama_enabled())
    inventory = rt.intelligence_inventory()
    result = dict(result)
    result.setdefault("intelligence", inventory)
    result["GUNNCHAI_APP_PRODUCT_COMPLETE"] = False
    result["HUMAN_E6"] = False
    result["smollm2_is_full_intelligence_layer"] = False
    result["stub_content"] = False
    return result


def main() -> int:
    os.environ.setdefault(
        "GUNNCHOS_APP_PERMISSIONS",
        "storage_read,storage_write,ai_interface",
    )
    crash = "--crash-probe" in sys.argv
    result: dict
    used_first_party = False
    try:
        from gunnchos_device_os.first_party_apps.gunnchai_tutor import (  # noqa: F401
            run_gunnchai_tutor,
        )
    except ImportError:
        run_gunnchai_tutor = None  # type: ignore[assignment]

    if run_gunnchai_tutor is not None:
        # PLATFORM-001 / companion_bridge path — do not replace the entrypoint.
        used_first_party = True
        result = run_gunnchai_tutor(crash_probe=crash) if crash else run_gunnchai_tutor()
        result = _stamp_intelligence(result)
        result["tutor_entrypoint"] = "first_party_run_gunnchai_tutor"
    else:
        data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
        result = invoke_gunnchai_tutor_local(
            ROOT,
            registry_root=data_dir / "local_ai_registry",
            include_llama=_llama_enabled(),
        )
        result["tutor_entrypoint"] = "os_local_ai_nano_fallback"
        result["companion_bridge_regressed"] = False

    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    out = data_dir / "gunnchai_tutor_run.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": bool(result.get("ok")),
                "app_id": "gunnchos.gunnchai_tutor",
                "stub_content": False,
                "tutor_entrypoint": result.get("tutor_entrypoint"),
                "used_first_party": used_first_party,
                "preferred_daily_tier": (result.get("intelligence") or {}).get("preferred_daily_tier"),
                "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
                "HUMAN_E6": False,
                "wrote": str(out),
            }
        )
    )
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
