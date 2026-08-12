#!/usr/bin/env python3
"""gunnchSDK example app: WAIKE learning-mode stub.

Records a real learning-session log entry (question asked, canned local
answer, timestamp) into the sandboxed data directory. No network egress —
respects the manifest's `network_policy: deny_all` by construction.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def main() -> int:
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    policy = os.environ.get("GUNNCHOS_SANDBOX_NETWORK_POLICY", "deny_all")
    session_log = data_dir / "session_log.jsonl"
    entry = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prompt": "What is an A/B update slot?",
        "answer_source": "local_offline_stub",
        "network_policy_in_effect": policy,
    }
    with session_log.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    print(json.dumps({"ok": True, "session_log": str(session_log), "entry": entry}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
