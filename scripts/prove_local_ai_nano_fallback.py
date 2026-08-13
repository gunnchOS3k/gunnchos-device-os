#!/usr/bin/env python3
"""Record honest Nano vs Fast vs Pro inventory for device-os local_ai.

SmolLM2-135M Q4_K_M 512-ctx is Nano fallback only. Fast/Pro weights stay OPEN
until GGUFs are on disk. GUNNCHAI_APP_PRODUCT_COMPLETE and HUMAN_E6 stay false.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "local_ai"
sys.path.insert(0, str(ROOT))


def _rejects(fn) -> bool:
    try:
        fn()
    except ValueError as exc:
        return "Nano/fallback" in str(exc)
    return False


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    from gunnchos_device_os.phase_xiv.local_ai import (
        ROLE_FAST,
        ROLE_PRO,
        SMOLLM2_MODEL_ID,
        LocalAiRuntime,
        ModelRegistry,
        assert_honest_smollm2_label,
        find_smollm2_gguf,
        invoke_gunnchai_tutor_local,
        list_local_ggufs,
        local_fast_weights_present,
        local_pro_weights_present,
    )

    pytest = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "tests/phase_xiv/test_local_ai_nano_labels.py",
            "tests/phase_xiv/test_phase_xiv.py::test_local_ai_registry_hash_fallback",
            "tests/wp013/test_sdk_pipeline.py::test_first_party_real_app_full_pipeline[gunnchai_tutor]",
        ],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env={**dict(**{k: v for k, v in __import__("os").environ.items()}), "PYTHONPATH": f"{ROOT}:src"},
    )
    tests_ok = pytest.returncode == 0

    reg = ModelRegistry(ART / "prove_registry")
    rt = LocalAiRuntime(reg, timeout_s=8)
    registered = rt.ensure_default_models(ROOT, include_llama=False)
    inventory = rt.intelligence_inventory()
    tutor = invoke_gunnchai_tutor_local(
        ROOT,
        registry_root=ART / "tutor_registry",
        include_llama=False,
    )

    mislabel_attempts = {
        "claim_fast_rejected": _rejects(
            lambda: assert_honest_smollm2_label(SMOLLM2_MODEL_ID, tier="fast", role=ROLE_FAST)
        ),
        "claim_pro_rejected": _rejects(
            lambda: assert_honest_smollm2_label(SMOLLM2_MODEL_ID, tier="pro", role=ROLE_PRO)
        ),
        "claim_small_rejected": _rejects(
            lambda: assert_honest_smollm2_label(SMOLLM2_MODEL_ID, tier="small")
        ),
        "claim_local_fast_display_rejected": _rejects(
            lambda: assert_honest_smollm2_label(
                SMOLLM2_MODEL_ID, tier="nano", role="NANO_LOCAL", display_label="Local Fast"
            )
        ),
    }
    mislabel_pass = all(mislabel_attempts.values())

    ggufs = [p.name for p in list_local_ggufs(ROOT)]
    nano_path = find_smollm2_gguf(ROOT)

    payload = {
        "schema": "gunnchos.local_ai.nano_fallback.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_main": "3858e760295ad35828ff141919681f2bb8685cf0",
        "doctrine": (
            "SmolLM2-135M-Instruct Q4_K_M 512-ctx is Nano/fallback only. "
            "Not Local Fast, not Local Pro, not GUNNCHAI_APP_PRODUCT_COMPLETE intelligence."
        ),
        "tests": {
            "ok": tests_ok,
            "rc": pytest.returncode,
            "out": (pytest.stdout or "")[-4000:],
            "err": (pytest.stderr or "")[-2000:],
        },
        "registered": registered,
        "disk": {
            "ggufs": ggufs,
            "nano_gguf_present": bool(nano_path),
            "nano_gguf_name": nano_path.name if nano_path else None,
            "local_fast_weights_present": local_fast_weights_present(ROOT),
            "local_pro_weights_present": local_pro_weights_present(ROOT),
        },
        "intelligence": inventory,
        "tutor": {
            "ok": bool(tutor.get("ok")),
            "entrypoint": "invoke_gunnchai_tutor_local",
            "tier": (tutor.get("reply") or {}).get("tier"),
            "runtime": (tutor.get("reply") or {}).get("runtime"),
            "is_nano_fallback_only": (tutor.get("reply") or {}).get("is_nano_fallback_only"),
            "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
        },
        "mislabel_attempts": mislabel_attempts,
        "mislabel_rejected": mislabel_pass,
        "GUNNCHAI_APP_PRODUCT_COMPLETE": False,
        "HUMAN_E6": False,
        "GUNNCHOS_FRONTIER_OS_PARITY": False,
        "INDEPENDENT_VERIFICATION": "PENDING",
        "READY_FOR_EDMUND_MERGE": False,
        "do_not_merge": True,
        "open": [
            reason
            for reason in (
                inventory["fast"].get("reason"),
                inventory["pro"].get("reason"),
                "gunnchai_tutor first_party run_gunnchai_tutor / companion_bridge live on DRAFT #106 — this PR does not regress that contract",
                "HUMAN_E6 not started",
                "GUNNCHAI_APP_PRODUCT_COMPLETE remains false until Fast/Pro weights and OS-companion UX are earned",
            )
            if reason
        ],
        "claim_boundary": inventory["claim_boundary"],
        "verdict": (
            "PASS"
            if tests_ok and mislabel_pass and inventory["GUNNCHAI_APP_PRODUCT_COMPLETE"] is False
            else "FAIL"
        ),
    }
    out = ART / "VP_LOCAL_AI_NANO_FALLBACK.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": payload["verdict"] == "PASS", "wrote": str(out), "verdict": payload["verdict"]}))
    return 0 if payload["verdict"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
