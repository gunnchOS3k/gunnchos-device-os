#!/usr/bin/env python3
"""Real gunnchAI tutor first-party package entry (not sdk/examples stub)."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("GUNNCHOS_REPO_ROOT", Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gunnchos_device_os.gunnchai_integration import (  # noqa: E402
    tutor_prompt_guard,
    tutor_safety_check,
    tutor_session_start,
)


def main() -> int:
    session = tutor_session_start("student", "wireless_basics")
    guard = tutor_prompt_guard("Explain OFDM at a high level")
    safety = tutor_safety_check("OFDM splits a wide channel into many narrow subcarriers.")
    result = {
        "ok": bool(session.get("started")) and bool(guard.get("ok")) and bool(safety.get("safe_to_show")),
        "session": session,
        "guard": guard,
        "safety": safety,
        "stub_content": False,
        "claim_boundary": "Digital tutor safety gates only — not production LLM deployment.",
    }
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    out = data_dir / "gunnchai_tutor_run.json"
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": result["ok"], "app_id": "gunnchos.gunnchai_tutor", "stub_content": False, "wrote": str(out)}))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
