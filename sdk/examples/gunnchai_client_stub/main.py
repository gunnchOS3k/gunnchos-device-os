#!/usr/bin/env python3
"""gunnchSDK example app: gunnchAI client stub.

Even though the manifest declares `network` + `ai_interface.query`, this
stub honestly refuses to make any real network call and instead
demonstrates sandbox-policy enforcement: it reads the runner-provided
`GUNNCHOS_SANDBOX_NETWORK_POLICY` env var and, when it is `deny_all`
(the default in this manifest), returns a local-only synthetic response
rather than claiming a network round-trip that never happened.
"""
from __future__ import annotations

import json
import os
import time
from pathlib import Path


def main() -> int:
    data_dir = Path(os.environ.get("GUNNCHOS_SANDBOX_DATA_DIR", "."))
    policy = os.environ.get("GUNNCHOS_SANDBOX_NETWORK_POLICY", "deny_all")

    if policy == "deny_all":
        response = {
            "mode": "local_synthetic_no_network_egress",
            "answer": "gunnchAI client stub: network denied by sandbox policy, no call attempted.",
        }
    else:  # pragma: no cover - not exercised by default manifest
        response = {"mode": "network_allowed_but_not_implemented_in_stub", "answer": None}

    out = data_dir / "gunnchai_response.json"
    payload = {"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "network_policy": policy, **response}
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "wrote": str(out), **response}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
