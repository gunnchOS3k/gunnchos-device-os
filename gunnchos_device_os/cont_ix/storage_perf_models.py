"""Storage/memory/performance models finalized — fail if storage does not fit."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_STORAGE_PERF
from gunnchos_device_os.cont_viii.performance_models import MODELS, estimate_storage_headroom, estimate_memory_pressure


# Cont IX finalized budgets (GB)
IMAGE_BUDGET = {
    "os_base": 8.0,
    "productivity": 4.5,
    "games": 3.0,
    "ai_models_local": 2.5,
    "user_data_reserve": 16.0,
    "update_ab_reserve_ratio": 0.35,
}


def evaluate_storage_perf_models() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    rows = []
    failures = []
    for m in MODELS:
        fixed = (
            IMAGE_BUDGET["os_base"]
            + IMAGE_BUDGET["productivity"]
            + IMAGE_BUDGET["games"]
            + IMAGE_BUDGET["ai_models_local"]
            + IMAGE_BUDGET["user_data_reserve"]
        )
        ab = m.storage_gb * IMAGE_BUDGET["update_ab_reserve_ratio"]
        needed = fixed + ab
        fits = needed <= m.storage_gb
        storage = estimate_storage_headroom(m, used_gb=needed)
        mem = estimate_memory_pressure(m)
        row = {
            "sku": m.sku,
            "capacity_gb": m.storage_gb,
            "needed_gb": round(needed, 2),
            "fits": fits,
            "storage": storage,
            "memory": mem,
        }
        rows.append(row)
        if not fits:
            failures.append(m.sku)

    ok = len(failures) == 0 and len(rows) == len(MODELS)
    report = {
        "schema": "gunnchos.storage_perf_models.v1",
        "ok": ok,
        "token": TOKEN_STORAGE_PERF if ok else None,
        "budget": IMAGE_BUDGET,
        "models": rows,
        "failures": failures,
        "measured_physical": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else f"storage_does_not_fit:{','.join(failures)}",
    }
    out = root / "artifacts" / "continuation_ix" / "storage_perf_models.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
