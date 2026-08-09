#!/usr/bin/env python3
"""Phase XII prove script: ledger + claim scope + RJ campaign + firewall inputs."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "artifacts" / "phase_xii"
sys.path.insert(0, str(ROOT))


def run(cmd: list[str]) -> dict:
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    return {"cmd": cmd, "rc": r.returncode, "out": (r.stdout or "")[-2000:], "err": (r.stderr or "")[-2000:]}


def main() -> int:
    ART.mkdir(parents=True, exist_ok=True)
    steps = []
    steps.append(run([sys.executable, "scripts/build_reality_depth_ledger.py"]))
    # claim scope
    from gunnchos_device_os.phase_xii.claim_scope import write_claim_scope  # noqa: E402
    scope = write_claim_scope(ROOT)
    steps.append({"cmd": "write_claim_scope", "rc": 0, "scope_tokens": list((scope.get("tokens") or {}).keys())})
    steps.append(run([sys.executable, "scripts/run_phase_xii_rj.py"]))
    report = {
        "schema": "gunnchos.phase_xii.prove.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "steps": steps,
        "physical_execution_freeze": True,
        "auto_merge_request": None,
    }
    (ART / "PROVE_REPORT.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"ok": all(s.get("rc", 1) == 0 for s in steps if "rc" in s), "art": str(ART)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
