#!/usr/bin/env python3
"""Run STREAM-A-PKT-002: templates + middleware resilience + creator guest E2E."""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

from gunnchos_device_os.creation_enablement.guest_chain import run_guest_creator_e2e
from gunnchos_device_os.creation_enablement.templates import run_template_suite
from gunnchos_device_os.middleware.resilience import write_artifacts as write_middleware_artifacts


def _git_sha(repo: Path) -> str:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    out = root / "artifacts" / "stream_a_pkt_002"
    out.mkdir(parents=True, exist_ok=True)
    started = time.time()

    templates = run_template_suite(root)
    mw_paths = write_middleware_artifacts(root)
    mw = json.loads(mw_paths["faults"].read_text(encoding="utf-8"))
    guest = run_guest_creator_e2e(root)

    tokens = {
        "CREATOR_GUEST_BUILD_PASS": bool((guest.get("tokens") or {}).get("CREATOR_GUEST_BUILD_PASS")),
        "CREATOR_GUEST_INSTALL_PASS": bool((guest.get("tokens") or {}).get("CREATOR_GUEST_INSTALL_PASS")),
        "CREATOR_GUEST_RUN_PASS": bool((guest.get("tokens") or {}).get("CREATOR_GUEST_RUN_PASS")),
        "CREATOR_GUEST_UPDATE_PASS": bool((guest.get("tokens") or {}).get("CREATOR_GUEST_UPDATE_PASS")),
        "CREATOR_GUEST_ROLLBACK_PASS": bool((guest.get("tokens") or {}).get("CREATOR_GUEST_ROLLBACK_PASS")),
        "CREATOR_END_TO_END_DIGITAL_PASS": bool(
            (guest.get("tokens") or {}).get("CREATOR_END_TO_END_DIGITAL_PASS")
        ),
        "TEMPLATE_SUITE_PASS": bool(templates.get("ok")),
        "MIDDLEWARE_RESILIENCE_PASS": bool(mw.get("ok")),
        "SILICON_EXACT_EMULATION": False,
    }

    open_items = []
    if not tokens["CREATOR_END_TO_END_DIGITAL_PASS"]:
        open_items.append(
            {
                "id": "CREATOR_END_TO_END_DIGITAL_PASS",
                "blocker_class": "DIGITAL_OPEN" if guest.get("error") else "DIGITAL_OPEN",
                "detail": guest.get("error") or "one or more CREATOR_GUEST_* tokens false",
            }
        )
    open_items.append(
        {
            "id": "PHYSICAL_RING_E6",
            "blocker_class": "PHYSICAL_PENDING",
            "detail": "Ring physical remains false",
        }
    )
    open_items.append(
        {
            "id": "DA-DEVICE-103",
            "blocker_class": "OWNER_DISPOSITION",
            "detail": "device-os #103 conflicting — do not merge/reopen without Edmund",
        }
    )

    status = {
        "schema": "gunnchos.stream_a_pkt_002.status.v1",
        "packet": "STREAM-A-PKT-002",
        "updated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "base_sha": "e290cdf2bf39453442022e471bbbd4fafd97abf2",
        "tip_sha": _git_sha(root),
        "cursor_never_merges": True,
        "tokens": tokens,
        "OPEN": open_items,
        "evidence": [
            "artifacts/stream_a_pkt_002/CREATOR_GUEST_E2E_RESULT.json",
            "artifacts/stream_a_pkt_002/MIDDLEWARE_RESILIENCE_MATRIX.json",
            "artifacts/stream_a_pkt_002/MIDDLEWARE_FAULT_INJECTION_RESULT.json",
            "artifacts/stream_a_pkt_002/TEMPLATE_SUITE_RESULT.json",
        ],
        "merge_ready": bool(
            tokens["CREATOR_END_TO_END_DIGITAL_PASS"]
            and tokens["TEMPLATE_SUITE_PASS"]
            and tokens["MIDDLEWARE_RESILIENCE_PASS"]
        ),
        "duration_ms": int((time.time() - started) * 1000),
        "guest_error": guest.get("error"),
        "claim_boundary": (
            "CREATOR_END_TO_END_DIGITAL_PASS only if all five CREATOR_GUEST_* tokens "
            "are evidenced from guest RESULT.json. Cursor never merges."
        ),
    }
    (out / "STREAM_A_PKT_002_STATUS.json").write_text(
        json.dumps(status, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "status": str(out / "STREAM_A_PKT_002_STATUS.json"),
                "tokens": tokens,
                "merge_ready": status["merge_ready"],
                "guest_error": guest.get("error"),
            },
            indent=2,
        )
    )
    return 0 if status["merge_ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
