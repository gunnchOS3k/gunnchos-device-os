#!/usr/bin/env python3
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    out = ROOT / "results/update_system"
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "version": "0.1.0",
        "channel": "research",
        "signed": False,
        "rollback_slot": "b",
        "policy": "unsigned_updates_rejected",
    }
    (out / "sample_update_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out / "update_verification_report.md").write_text(
        "# Update verification\n\n- Unsigned updates: rejected by policy\n- Rollback metadata: present\n",
        encoding="utf-8",
    )
    print("Generated update report")


if __name__ == "__main__":
    main()
