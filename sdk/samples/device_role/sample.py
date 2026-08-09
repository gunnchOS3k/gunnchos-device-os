#!/usr/bin/env python3
"""Device role sample."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from gunnchos_adopter_sdk import AdopterClient


def main() -> None:
    client = AdopterClient()
    for role in ("student", "office", "handheld", "ds_xl"):
        print(client.sample_device_role(role))


if __name__ == "__main__":
    main()
